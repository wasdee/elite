import os
import re
import shutil

from elite.libraries import dock


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_get_dock_plist_path():
    assert re.match(
        '/Users/.*/Library/Preferences/com.apple.dock.plist', dock.get_dock_plist_path()
    )


def test_extract(tmpdir):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    app_layout, other_layout = dock.extract(p.strpath)
    assert app_layout == [
        '/Applications/ForkLift.app',
        '/Applications/Siri.app',
        '/Applications/Launchpad.app',
        '/Applications/Safari.app',
        '/Applications/Sublime Text.app',
        '/Applications/Utilities/Terminal.app',
        '/Applications/Cubase 9.5.app',
        '/Applications/MuseScore 2.app',
        '/Applications/XLD.app',
        '/Applications/Focusrite Control.app',
        '/Applications/Spotify.app',
        '/Applications/OpenEmu.app',
        '/Applications/Messages.app',
        '/Applications/Skype.app',
        '/Applications/Textual.app',
        '/Applications/Things3.app',
        '/Applications/VMware Fusion.app',
        '/Applications/App Store.app',
        '/Applications/System Preferences.app',
    ]
    assert other_layout == [
        {
            'path': '/Users/fots/Downloads',
            'arrangement': 'Name',
            'display_as': 'Stack',
            'show_as': 'Automatic'
        },
        {
            'label': 'GitHub',
            'url': 'https://github.com/'
        }
    ]


def test_extract_path_unspecified(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    monkeypatch.setattr(dock, 'get_dock_plist_path', lambda: p.strpath)

    app_layout, other_layout = dock.extract()
    assert len(app_layout) == 19
    assert len(other_layout) == 2


def test_normalise():
    app_layout, other_layout = dock.normalise(
        app_layout=[
            'ForkLift',
            '/Applications/Siri.app',
            '/Applications/Launchpad.app',
            'Safari',
            '/Applications/Sublime Text.app'
        ],
        other_layout=[
            {
                'path': '/Users/fots/Downloads'
            }
        ]
    )
    assert app_layout == [
        '/Applications/ForkLift.app',
        '/Applications/Siri.app',
        '/Applications/Launchpad.app',
        '/Applications/Safari.app',
        '/Applications/Sublime Text.app'
    ]
    assert other_layout == [
        {
            'path': '/Users/fots/Downloads',
            'arrangement': 'Name',
            'display_as': 'Stack',
            'show_as': 'Automatic'
        }
    ]


def test_build_extract_roundtrip(tmpdir):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    app_layout = [
        '/Applications/ForkLift.app',
        '/Applications/Siri.app',
        '/Applications/Launchpad.app',
        '/Applications/Safari.app',
        '/Applications/Sublime Text.app'
    ]

    other_layout = [
        {
            'path': '/Users/fots/Documents',
            'arrangement': 'Name',
            'display_as': 'Stack',
            'show_as': 'Automatic'
        },
        {
            'label': 'GitLab',
            'url': 'https://gitlab.com/'
        }
    ]

    dock.build(
        app_layout=app_layout,
        other_layout=other_layout,
        dock_plist_path=p.strpath,
        perform_normalise=False
    )

    assert dock.extract(p.strpath) == (app_layout, other_layout)


def test_build_extract_roundtrip_path_unspecified(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    monkeypatch.setattr(dock, 'get_dock_plist_path', lambda: p.strpath)

    app_layout = [
        '/Applications/ForkLift.app',
        '/Applications/Siri.app',
        '/Applications/Launchpad.app',
        '/Applications/Safari.app',
        '/Applications/Sublime Text.app'
    ]

    other_layout = [
        {
            'path': '/Users/fots/Documents',
            'arrangement': 'Name',
            'display_as': 'Stack',
            'show_as': 'Automatic'
        },
        {
            'label': 'GitLab',
            'url': 'https://gitlab.com/'
        }
    ]

    dock.build(
        app_layout=app_layout,
        other_layout=other_layout,
        perform_normalise=False
    )

    assert dock.extract(p.strpath) == (app_layout, other_layout)


def test_build_extract_roundtrip_with_normalisation(tmpdir):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    dock.build(
        app_layout=[
            'ForkLift',
            '/Applications/Siri.app',
            '/Applications/Launchpad.app',
            'Safari',
            '/Applications/Sublime Text.app'
        ],
        other_layout=[
            {
                'path': '/Users/fots/Documents'
            },
            {
                'label': 'GitLab',
                'url': 'https://gitlab.com/'
            }
        ],
        dock_plist_path=p.strpath
    )

    app_layout, other_layout = dock.extract(p.strpath)
    assert app_layout == [
        '/Applications/ForkLift.app',
        '/Applications/Siri.app',
        '/Applications/Launchpad.app',
        '/Applications/Safari.app',
        '/Applications/Sublime Text.app'
    ]
    assert other_layout == [
        {
            'path': '/Users/fots/Documents',
            'arrangement': 'Name',
            'display_as': 'Stack',
            'show_as': 'Automatic'
        },
        {
            'label': 'GitLab',
            'url': 'https://gitlab.com/'
        }
    ]
