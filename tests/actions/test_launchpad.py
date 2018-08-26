import os
import shutil

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.launchpad import Launchpad


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_same(tmpdir, monkeypatch):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    monkeypatch.setattr(
        'elite.libraries.launchpad.get_launchpad_db_path', lambda: p.join('db').strpath
    )

    widget_layout = [
        # Page 1
        [
            'Calculator',
            'Calendar',
            'Contacts',
            'Dictionary',
            'Movies',
            'Stickies',
            'Stocks',
            'Tile Game',
            'Unit Converter',
            'Weather',
            'Web Clip',
            'World Clock'
        ]
    ]

    app_layout = [
        # Page 1
        [
            'Safari',
            'Mail',
            'Contacts',
            'Calendar',
            'Reminders',
            'Notes',
            'Maps',
            'Messages',
            'FaceTime',
            'Photo Booth',
            'Photos',
            'iTunes',
            'iBooks',
            'App Store',
            'Preview',
            'Dictionary',
            'Calculator',
            {
                'folder_layout': [
                    [
                        'QuickTime Player',
                        'TextEdit',
                        'Grapher',
                        'DVD Player',
                        'Time Machine',
                        'Font Book',
                        'Chess',
                        'Stickies',
                        'Image Capture',
                        'VoiceOver Utility',
                        'AirPort Utility',
                        'Migration Assistant',
                        'Terminal',
                        'Activity Monitor',
                        'Console',
                        'Keychain Access',
                        'System Information',
                        'Automator',
                        'Script Editor',
                        'Disk Utility',
                        'Boot Camp Assistant',
                        'Digital Color Meter',
                        'ColorSync Utility',
                        'Grab',
                        'Bluetooth File Exchange',
                        'Audio MIDI Setup'
                    ]
                ],
                'folder_title': 'Other'
            },
            'Siri',
            'Mission Control',
            'Dashboard',
            'System Preferences'
        ],
        # Page 2
        [
            'DaisyDisk',
            'Entropy',
            'Things',
            'Spotify',
            'Sublime Text'
        ]
    ]

    launchpad = Launchpad(widget_layout, app_layout)
    assert launchpad.process() == ActionResponse(changed=False)


def test_different(tmpdir, monkeypatch):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    monkeypatch.setattr(
        'elite.libraries.launchpad.get_launchpad_db_path', lambda: p.join('db').strpath
    )

    widget_layout = [
        # Page 1
        [
            'Dictionary',
            'Calculator',
            'Contacts',
            'Calendar',
            'Movies',
            'Stickies',
            'Tile Game',
            'Stocks',
            {
                'folder_title': 'Stuff',
                'folder_layout': [
                    [
                        'Unit Converter',
                        'Weather',
                        'Web Clip'
                    ]
                ]
            },
            'World Clock'
        ]
    ]

    app_layout = [
        # Page 1
        [
            'Safari',
            'Mail',
            'Contacts',
            'Calendar',
            'Messages',
            'FaceTime',
            'Photos',
            'iTunes',
            'iBooks',
            'App Store',
            'Preview',
            {
                'folder_title': 'Unused Stuff',
                'folder_layout': [
                    [
                        'Dictionary',
                        'Calculator',
                        'Reminders',
                        'Notes',
                        'Maps',
                        'Photo Booth',
                    ]
                ]
            },
            {
                'folder_layout': [
                    [
                        'QuickTime Player',
                        'TextEdit',
                        'Grapher',
                        'DVD Player',
                        'Time Machine',
                        'Font Book',
                        'Chess',
                        'Stickies',
                        'Image Capture',
                        'VoiceOver Utility',
                        'AirPort Utility',
                        'Migration Assistant',
                        'Terminal',
                        'Activity Monitor',
                        'Console',
                        'Keychain Access',
                        'System Information',
                        'Automator',
                        'Script Editor',
                        'Disk Utility',
                        'Boot Camp Assistant',
                        'Digital Color Meter',
                        'ColorSync Utility',
                        'Grab',
                        'Bluetooth File Exchange',
                        'Audio MIDI Setup'
                    ]
                ],
                'folder_title': 'Other'
            },
            'Siri',
            'System Preferences'
        ],
        # Page 2
        [
            'Mission Control',
            'Dashboard'
        ],
        # Page 3
        [
            {
                'folder_title': 'Productivity',
                'folder_layout': [
                    [
                        'DaisyDisk',
                        'Entropy'
                    ],
                    [
                        'Things'
                    ]
                ]
            },
            'Spotify',
            'Sublime Text'
        ]
    ]

    launchpad = Launchpad(widget_layout, app_layout)
    assert launchpad.process() == ActionResponse(changed=True, data={
        'extra_widgets': [],
        'extra_apps': []
    })


def test_different_extra_items(tmpdir, monkeypatch):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    monkeypatch.setattr(
        'elite.libraries.launchpad.get_launchpad_db_path', lambda: p.join('db').strpath
    )

    widget_layout = [
        # Page 1
        [
            'Calculator',
            'Contacts',
            'Calendar',
            'Stickies',
            'Tile Game',
            'Stocks',
            {
                'folder_title': 'Stuff',
                'folder_layout': [
                    [
                        'Unit Converter',
                        'Weather',
                        'Web Clip'
                    ]
                ]
            },
            'World Clock'
        ]
    ]

    app_layout = [
        # Page 1
        [
            'Safari',
            'Mail',
            'Contacts',
            'Calendar',
            'Photos',
            'iTunes',
            'iBooks',
            'App Store',
            'Preview',
            {
                'folder_title': 'Unused Stuff',
                'folder_layout': [
                    [
                        'Dictionary',
                        'Calculator',
                        'Reminders',
                        'Notes',
                        'Maps',
                        'Photo Booth',
                    ]
                ]
            },
            {
                'folder_layout': [
                    [
                        'QuickTime Player',
                        'TextEdit',
                        'Grapher',
                        'DVD Player',
                        'Time Machine',
                        'Font Book',
                        'Chess',
                        'Stickies',
                        'Image Capture',
                        'VoiceOver Utility',
                        'AirPort Utility',
                        'Migration Assistant',
                        'Terminal',
                        'Activity Monitor',
                        'Console',
                        'Keychain Access',
                        'System Information',
                        'Automator',
                        'Script Editor',
                        'Disk Utility',
                        'Boot Camp Assistant',
                        'Digital Color Meter',
                        'ColorSync Utility',
                        'Grab',
                        'Bluetooth File Exchange',
                        'Audio MIDI Setup'
                    ]
                ],
                'folder_title': 'Other'
            },
            'Siri',
            'System Preferences'
        ],
        # Page 2
        [
            'Mission Control',
            'Dashboard'
        ],
        # Page 3
        [
            {
                'folder_title': 'Productivity',
                'folder_layout': [
                    [
                        'DaisyDisk',
                        'Entropy'
                    ],
                    [
                        'Things'
                    ]
                ]
            },
            'Spotify',
            'Sublime Text'
        ]
    ]

    launchpad = Launchpad(widget_layout, app_layout)
    response = launchpad.process()
    assert response.changed
    assert sorted(response.data['extra_widgets']) == ['Dictionary', 'Movies']
    assert sorted(response.data['extra_apps']) == ['FaceTime', 'Messages']


def test_layout_invalid(tmpdir, monkeypatch):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    monkeypatch.setattr(
        'elite.libraries.launchpad.get_launchpad_db_path', lambda: p.join('db').strpath
    )

    widget_layout = [
        [
            'Boo'
        ]
    ]
    app_layout = []

    launchpad = Launchpad(widget_layout, app_layout)
    with pytest.raises(ActionError):
        launchpad.process()
