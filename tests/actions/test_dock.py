import os
import shutil

from elite.actions import ActionResponse
from elite.actions.dock import Dock


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_same(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    monkeypatch.setattr('elite.libraries.dock.get_dock_plist_path', lambda: p.strpath)

    app_layout = [
        'ForkLift',
        'Siri',
        'Launchpad',
        'Safari',
        'Sublime Text',
        'Utilities/Terminal',
        'Cubase 9.5',
        'MuseScore 2',
        'XLD',
        'Focusrite Control',
        'Spotify',
        'OpenEmu',
        'Messages',
        'Skype',
        'Textual',
        'Things3',
        'VMware Fusion',
        'App Store',
        'System Preferences',
    ]
    other_layout = [
        {
            'path': '/Users/fots/Downloads'
        },
        {
            'label': 'GitHub',
            'url': 'https://github.com/'
        }
    ]

    dock = Dock(app_layout, other_layout)
    assert dock.process() == ActionResponse(changed=False)


def test_different(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.dock.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'dock', 'com.apple.dock.plist'), p.strpath)

    monkeypatch.setattr('elite.libraries.dock.get_dock_plist_path', lambda: p.strpath)

    app_layout = [
        'ForkLift',
        'Siri',
        'Launchpad',
        'Safari',
        'Sublime Text'
    ]
    other_layout = [
        {
            'label': 'GitLub',
            'url': 'https://gitlub.com/'
        },
        {
            'path': '/Users/fots/Documents'
        }
    ]

    dock = Dock(app_layout, other_layout)
    assert dock.process() == ActionResponse(changed=True)
