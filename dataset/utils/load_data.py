import os

import albumentations as A
import numpy as np
import pandas as pd
from albumentations.pytorch import ToTensorV2
from rdkit.Chem import AllChem

from dataset.utils.loader import mol_to_graph_data_obj_simple, mol_to_graph_data_obj_asAtomNum


def process_graph(molecule_smiles, model_name='graph_transformer'):
    if not isinstance(molecule_smiles, list):
        molecule_smiles = [molecule_smiles]
    graphs = []
    for smiles in molecule_smiles:
        rdkit_mol = AllChem.MolFromSmiles(smiles)
        if model_name == 'graph_transformer':
            atom_to_what = 'dense_matrix'
            make_one_hot = True
        elif model_name == 'gin':
            atom_to_what = None
            make_one_hot = False

        if rdkit_mol != None:  # ignore invalid mol objects
            if atom_to_what is None:
                molecular_graph = mol_to_graph_data_obj_simple(rdkit_mol)
            else:
                molecular_graph = mol_to_graph_data_obj_asAtomNum(rdkit_mol, make_one_hot)
        graphs.append(molecular_graph)
    return graphs


def read_data_omics(args, mode):
    path = os.path.join(args.data_path, 'new_train.csv')

    print('preprocessing %s data from %s' % (mode, path))

    graphs = []
    with open(path) as f:
        if mode == 'test':
            df = pd.read_csv(path.replace('test', 'train'))[:3000]
        else:
            df = pd.read_csv(path)[3000:]

        print(len(df), '***')

        for i in range(0, len(df)):
            molecule_smiles, img_paths = df.iloc[i]['smiles'], df.iloc[i]['npy_path']
            img_paths = os.path.join(args.data_path, img_paths)

            try:
                rdkit_mol = AllChem.MolFromSmiles(molecule_smiles)
                if rdkit_mol != None:  # ignore invalid mol objects
                    # if args.task_type == 'classification':
                    #     molecular_graph = mol_to_graph_data_obj_clf(rdkit_mol)
                    # elif args.task_type == 'regression':
                    #     molecular_graph = mol_to_graph_data_obj_reg(rdkit_mol)
                    # else:
                    #     raise Exception
                    atom_to_what = args.get('atom_to_what', None)
                    if atom_to_what is None:
                        molecular_graph = mol_to_graph_data_obj_simple(rdkit_mol)
                    else:
                        molecular_graph = mol_to_graph_data_obj_asAtomNum(rdkit_mol, args.get('make_one_hot', False))
            except:
                continue

            if int(i) % 10000 == 0:
                print('%dk' % (int(i) // 1000))

            graphs.append([molecular_graph, img_paths])

    return graphs


def load_data_omics(args):
    if args.cnn_model_name == 'vit_tiny_patch16_224':
        img_size = 224
    else:
        img_size = 128
    train_transform = A.Compose([
        A.Resize(height=img_size, width=img_size, p=1.0),
        A.Transpose(p=0.5),
        A.VerticalFlip(p=0.5),
        A.HorizontalFlip(p=0.5),
        A.RandomBrightness(limit=0.2 / 16, p=0.5),
        A.RandomContrast(limit=0.2 / 16, p=0.5),
        # A.ShiftScaleRotate(shift_limit=0.2, scale_limit=0.2, rotate_limit=45, border_mode=0, p=0.75),
        # A.Cutout(max_h_size=int(img_size*0.7), max_w_size=int(img_size*0.7), num_holes=1, p=0.5),
        ToTensorV2()],
        p=1.0)
    test_transform = A.Compose([
        A.Resize(height=img_size, width=img_size, p=1.0),
        ToTensorV2()],
        p=1.0)
    train_graphs = read_data_omics(args, 'train')
    test_graphs = read_data_omics(args, 'test')

    train_dataset = NewSmilesOmicsDataset(args, 'train', train_graphs, train_transform)
    # valid_dataset = NewSmilesOmicsDataset(args, 'valid', feature_encoder, valid_graphs,transform)
    test_dataset = NewSmilesOmicsDataset(args, 'test', test_graphs, test_transform)
    # train_dataset = NewSmilesOmicsDataset(args, 'train', train_graphs,train_transform)
    # test_dataset = NewSmilesOmicsDataset(args, 'test', test_graphs,test_transform)
    return train_dataset, test_dataset
