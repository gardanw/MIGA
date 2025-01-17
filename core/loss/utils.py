from utils.tensor_operator import tensor2array
from functools import wraps


def merge_loss_dict(loss_dict, weight_dict=None, loss_prefix_list=None):
    re_loss_dict = dict()
    re_total_loss = 0
    for loss_name, sub_loss_dict in loss_dict.items():
        prefix = '_'.join(loss_name.split('_')[:-1])
        total_loss = sub_loss_dict.pop('total_loss')
        if weight_dict is not None:
            weight = weight_dict.get(loss_name, 1)
        else:
            weight = 1
        re_total_loss = re_total_loss + weight * total_loss
        sub_loss_dict[loss_name] = tensor2array(total_loss)
        re_loss_dict.update(sub_loss_dict)
    re_loss_dict['total_loss'] = re_total_loss
    return re_loss_dict


def loss_dict_remake_wrapper(loss_func):
    def remake_loss_dict(*args, **kwargs):
        loss_dict = loss_func(*args, **kwargs)
        total_loss = loss_dict.pop('total_loss')
        new_loss_dict = {'total_loss': total_loss}
        for loss_name, loss_value in loss_dict.items():
            new_loss_dict[loss_name] = tensor2array(loss_value)
        del loss_dict
        return new_loss_dict

    return remake_loss_dict


def atom_loss_remake(atom_loss_out, atom_loss_name):
    return {'total_loss': atom_loss_out, atom_loss_name: tensor2array(atom_loss_out)}


def symmetric_loss_wrapper(func):
    @wraps(func)
    def make_symmetric_func(in_1, in_2, *args, **kwargs):
        a = func(in_1, in_2, *args, **kwargs)
        b = func(in_2, in_1, *args, **kwargs)
        return (a + b) / 2.0
    return make_symmetric_func
