from collections import namedtuple
import os

from AppKit import NSFont
# Strangely NSKeyedArchiver won't import without ScriptingBridge
import ScriptingBridge  # flake8: noqa
from Foundation import NSKeyedArchiver, NSCalibratedRGBColor
import yaml


def join_path(loader, node):
    seq = loader.construct_sequence(node)
    return os.path.join(*[i for i in seq])


def first_existing_path(loader, node):
    map = loader.construct_mapping(node, deep=True)
    try:
        base_dir = map['base_dir']
        paths = map['paths']
    except KeyError:
        raise ValueError('both a base_dir and paths key must be provided')

    for path in paths:
        if os.path.exists(os.path.expanduser(os.path.join(base_dir, path))):
            return path
    else:
        raise ValueError('none of the paths provided exist')


def macos_font(loader, node):
    seq = loader.construct_sequence(node)

    if len(seq) != 2:
        raise ValueError('only two arguments may be provided, the font name and size')

    font_name, font_size = seq
    font = NSFont.fontWithName_size_(font_name, font_size)

    if font is None:
        raise ValueError('unable to find the font requested')

    return bytes(NSKeyedArchiver.archivedDataWithRootObject_(font))


def macos_color(loader, node):
    seq = loader.construct_sequence(node)

    if len(seq) != 4:
        raise ValueError('only four arguments may be provided, red, green, blue and alpha')

    red, green, blue, alpha = seq

    for color in [red, green, blue]:
        if not 0 <= color <= 255:
            raise ValueError('colors provided must be in the range 0 to 255')

    if not 0 <= alpha <= 1:
        raise ValueError('alpha must be in the range 0 to 1')

    color = NSCalibratedRGBColor.alloc().initWithRed_green_blue_alpha_(
        red / 255, green / 255, blue / 255, alpha
    )

    return bytes(NSKeyedArchiver.archivedDataWithRootObject_(color))


yaml.add_constructor('!join_path', join_path)
yaml.add_constructor('!first_existing_path', first_existing_path)
yaml.add_constructor('!macos_font', macos_font)
yaml.add_constructor('!macos_color', macos_color)


class ConfigError(object):
    """An error raised when problem is encountered reading a config file or variable"""


def load_config(search_path, config_order):
    # Find the paths to all YAML config files in the chosen search path and in the appropriate
    # order and then add them to the config_files list.
    config_files = []
    for config_file in config_order:
        abs_config_path = os.path.join(search_path, config_file)
        if os.path.isdir(abs_config_path):
            for root, dirs, files in os.walk(abs_config_path):
                for filename in files:
                    # Skip any files that aren't YAML
                    extension = os.path.splitext(filename)
                    if extension[1] not in ['.yml', '.yaml']:
                        continue

                    # Add the config to our list
                    config_path = os.path.join(root, filename)
                    config_files.append(config_path)
        elif os.path.isfile(abs_config_path):
            config_files.append(abs_config_path)
        else:
            raise ConfigError(f"the path specified {abs_config_path} doesn't exist")

    # Load all the configs requested into one big combined data structure.
    configs = []
    for config_file in config_files:
        with open(config_file) as f:
            config_str = f.read()
            configs.append(config_str if config_str.endswith('\n') else config_str + '\n')

    config_dict = yaml.load(''.join(configs))

    if not isinstance(config_dict, dict):
        raise ConfigError('the top level of your config must contain key-value pairs')

    for key in list(config_dict):
        if key.startswith('_'):
            del config_dict[key]

    Config = namedtuple('Config', config_dict.keys())
    return Config(**config_dict)
