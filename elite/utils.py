from collections import namedtuple
import os


def dict_to_namedtuple(typename, dictionary):
    """
    Converts the top level elements of a dict to a named tuple.

    :param typename: The typename to create the tuple as.
    :param dictionary: The dictionary to convert.

    :return: A named tuple containing the dict contents.
    """
    return namedtuple(typename, dictionary.keys())(**dictionary)


def build_absolute_path(path):
    """
    Builds an absolute path based on the root of the current project.

    :param path: The path to process.

    :return: The absolute path of the provided path.
    """
    return os.path.join(os.path.dirname(__file__), os.pardir, path)
