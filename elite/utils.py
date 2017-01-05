from collections import namedtuple
import os


def dict_to_namedtuple(typename, dictionary):
    return namedtuple(typename, dictionary.keys())(**dictionary)


def build_relative_path(path):
    return os.path.join(os.path.dirname(__file__), os.pardir, path)
