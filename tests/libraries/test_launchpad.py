import os
import re
import shutil

import pytest
from elite.libraries import launchpad


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_get_launchpad_db_path():
    assert re.match(
        '/var/folders/.*/com.apple.dock.launchpad/db/db', launchpad.get_launchpad_db_path()
    )


def test_extract(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    widget_layout, app_layout = launchpad.extract(p.join('db').strpath)
    assert widget_layout == [
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
    assert app_layout == [
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


def test_extract_unspecified_path(tmpdir, monkeypatch):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    monkeypatch.setattr(launchpad, 'get_launchpad_db_path', lambda: p.join('db').strpath)

    widget_layout, app_layout = launchpad.extract()
    assert len(widget_layout) == 1
    assert len(app_layout) == 2


def test_build_missing_folder_title(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    with pytest.raises(launchpad.LaunchpadValidationError):
        launchpad.build(
            widget_layout=[
                [
                    {
                        'folder_layout': [
                            [
                                'Unit Converter',
                                'Weather',
                                'Web Clip'
                            ]
                        ]
                    }
                ]
            ],
            app_layout=[],
            launchpad_db_path=p.join('db').strpath
        )


def test_build_missing_folder_layout(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    with pytest.raises(launchpad.LaunchpadValidationError):
        launchpad.build(
            widget_layout=[],
            app_layout=[
                [
                    {
                        'folder_title': 'Unused Stuff'
                    }
                ]
            ],
            launchpad_db_path=p.join('db').strpath
        )


def test_build_inexistent_widget(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    with pytest.raises(launchpad.LaunchpadValidationError):
        launchpad.build(
            widget_layout=[
                [
                    'Boo'
                ]
            ],
            app_layout=[],
            launchpad_db_path=p.join('db').strpath
        )


def test_build_inexistent_app(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    with pytest.raises(launchpad.LaunchpadValidationError):
        launchpad.build(
            widget_layout=[],
            app_layout=[
                [
                    'Boo'
                ]
            ],
            launchpad_db_path=p.join('db').strpath
        )


def test_build_inexistent_folder_widget(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    with pytest.raises(launchpad.LaunchpadValidationError):
        launchpad.build(
            widget_layout=[
                [
                    {
                        'folder_title': 'Stuff',
                        'folder_layout': [
                            [
                                'Boo'
                            ]
                        ]
                    }
                ]
            ],
            app_layout=[],
            launchpad_db_path=p.join('db').strpath
        )


def test_build_inexistent_folder_app(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    with pytest.raises(launchpad.LaunchpadValidationError):
        launchpad.build(
            widget_layout=[],
            app_layout=[
                [
                    {
                        'folder_title': 'Stuff',
                        'folder_layout': [
                            [
                                'Boo'
                            ]
                        ]
                    }
                ]
            ],
            launchpad_db_path=p.join('db').strpath
        )


def test_build_extract_roundtrip(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

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

    launchpad.build(
        widget_layout=widget_layout,
        app_layout=app_layout,
        launchpad_db_path=p.join('db').strpath
    )

    assert launchpad.extract(p.join('db').strpath) == (widget_layout, app_layout)


def test_build_extract_roundtrip_missing_items(tmpdir):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    widget_layout = [
        # Page 1
        [
            'Dictionary',
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
            'Messages',
            'FaceTime',
            'Photos',
            'iTunes',
            'iBooks',
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
                        'DaisyDisk'
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

    extra_widgets, extra_apps = launchpad.build(
        widget_layout=widget_layout,
        app_layout=app_layout,
        launchpad_db_path=p.join('db').strpath
    )

    assert sorted(extra_widgets) == ['Movies']
    assert sorted(extra_apps) == ['App Store', 'Entropy']

    updated_widget_layout, updated_app_layout = launchpad.extract(p.join('db').strpath)

    assert updated_widget_layout[:-1] == widget_layout
    assert sorted(updated_widget_layout[-1]) == ['Movies']
    assert updated_app_layout[:-1] == app_layout
    assert sorted(updated_app_layout[-1]) == ['App Store', 'Entropy']


def test_build_extract_roundtrip_unspecified_path(tmpdir, monkeypatch):
    p = tmpdir.join('db')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'launchpad'), p.strpath)

    monkeypatch.setattr(launchpad, 'get_launchpad_db_path', lambda: p.join('db').strpath)

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

    launchpad.build(
        widget_layout=widget_layout,
        app_layout=app_layout
    )

    assert launchpad.extract(p.join('db').strpath) == (widget_layout, app_layout)
