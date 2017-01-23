from collections import namedtuple
import os
import subprocess


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
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, path))


def deep_merge(source, destination):
    """
    Deep merges the source dict into the destination.

    :param source: The source dict to merge into the destination.
    :param destination: The destination dict to merge the source into.

    :return: the destination dict is returned (required for recursion) but the destination
             dict will be updated too
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            destination[key] = deep_merge(value, node)
        else:
            destination[key] = value

    return destination


def batch(items, batch_size):
    """
    Batches up a list into multiple lists which each are of the requested batch size;

    :param items: the list of items to be batched
    :param batch_size: the size of each batch
    """
    length = len(items)
    for index in range(0, length, batch_size):
        yield items[index:min(index + batch_size, length)]


def generate_uuid():
    """Generate a UUID using uuidgen."""
    return subprocess.check_output('uuidgen', encoding='utf-8').rstrip()
