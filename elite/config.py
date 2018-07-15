import os
import pathlib
from collections import namedtuple

# pylint: disable=no-name-in-module
from AppKit import NSFont
# Strangely NSKeyedArchiver won't import without ScriptingBridge
import ScriptingBridge  # noqa: F401,I100, pylint: disable=unused-import
from Foundation import NSCalibratedRGBColor, NSKeyedArchiver
from ruamel.yaml import YAML, YAMLError


def include(loader, node):
    path = pathlib.Path(loader.loader.reader.stream.name).parent.joinpath(node.value)
    yaml = YAML(typ=loader.loader.typ, pure=loader.loader.pure)
    yaml.composer.anchors = loader.composer.anchors
    return yaml.load(path)


def join_path(loader, node):
    seq = loader.construct_sequence(node)
    return os.path.join(*[i for i in seq])


def first_existing_dir(loader, node):
    seq = loader.construct_sequence(node)

    for path in seq:
        if os.path.isdir(os.path.expanduser(path)):
            return path

    return None


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


def compose_document_without_anchor_reset(self):
    self.parser.get_event()
    node = self.compose_node(None, None)
    self.parser.get_event()
    # self.anchors = {}  # Commented out to avoid resetting of anchors
    return node


class ConfigError(Exception):
    """An error raised when problem is encountered reading a config file or variable"""


def load_config(config_path):
    yaml = YAML(typ='safe', pure=True)
    yaml.Composer.compose_document = compose_document_without_anchor_reset
    yaml.Constructor.add_constructor('!include', include)
    yaml.Constructor.add_constructor('!join_path', join_path)
    yaml.Constructor.add_constructor('!first_existing_dir', first_existing_dir)
    yaml.Constructor.add_constructor('!macos_font', macos_font)
    yaml.Constructor.add_constructor('!macos_color', macos_color)

    try:
        config = yaml.load(pathlib.Path(config_path))
    except OSError:
        raise ConfigError(f"the path specified {config_path} doesn't exist")
    except YAMLError:
        raise ConfigError(f'unable to parse the config file at path {config_path}')

    if not isinstance(config, dict):
        raise ConfigError('the top level of your config must contain key-value pairs')

    Config = namedtuple('Config', config.keys())
    return Config(**config)
