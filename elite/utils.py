from collections import namedtuple


def dict_to_namedtuple(typename, dictionary):
    return namedtuple(typename, dictionary.keys())(**dictionary)
