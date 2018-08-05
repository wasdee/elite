#!/usr/bin/env python3
import os
import plistlib
import urllib.parse

from ..utils import ReversibleDict, generate_uuid


ARRANGEMENT_MAPPING = ReversibleDict({
    1: 'Name',
    2: 'Date Added',
    3: 'Date Modified',
    4: 'Date Created',
    5: 'Kind'
})

DISPLAY_AS_MAPPING = ReversibleDict({
    0: 'Stack',
    1: 'Folder'
})

SHOW_AS_MAPPING = ReversibleDict({
    0: 'Automatic',
    1: 'Fan',
    2: 'Grid',
    3: 'List'
})


def get_dock_plist_path():
    return os.path.expanduser('~/Library/Preferences/com.apple.dock.plist')


def extract(dock_plist_path=None):
    if not dock_plist_path:
        dock_plist_path = get_dock_plist_path()

    with open(dock_plist_path, 'rb') as fp:
        dock_plist = plistlib.load(fp)

    app_layout = []
    for app in dock_plist['persistent-apps']:
        # Obtain a normalised path to the app
        app_url = app['tile-data']['file-data']['_CFURLString']
        app_url_parse = urllib.parse.urlparse(urllib.parse.unquote(app_url))
        app_path = os.path.normpath(app_url_parse.path)

        # Add the app to our app layout
        app_layout.append(app_path)

    other_layout = []
    for other in dock_plist['persistent-others']:
        # A directory location was found
        if 'file-data' in other['tile-data']:
            # Obtain a normalised path to the directory
            other_url = other['tile-data']['file-data']['_CFURLString']
            other_url_parse = urllib.parse.urlparse(urllib.parse.unquote(other_url))
            other_path = os.path.normpath(other_url_parse.path)

            # Obtain details about how the items is displayed
            other_arrangement_id = other['tile-data']['arrangement']
            other_arrangement = ARRANGEMENT_MAPPING[other_arrangement_id]
            other_display_as_id = other['tile-data']['displayas']
            other_display_as = DISPLAY_AS_MAPPING[other_display_as_id]
            other_show_as_id = other['tile-data']['showas']
            other_show_as = SHOW_AS_MAPPING[other_show_as_id]

            # Add the directory to our other layout
            other_layout.append({
                'path': other_path,
                'arrangement': other_arrangement,
                'display_as': other_display_as,
                'show_as': other_show_as
            })
        # A URL location was found
        else:
            # Determine the URL and label of the item
            other_url = other['tile-data']['url']['_CFURLString']
            other_label = other['tile-data']['label']

            # Add the URL to our other layout
            other_layout.append({
                'url': other_url,
                'label': other_label
            })

    return app_layout, other_layout


def normalise(app_layout, other_layout):
    # Normalise each app path
    normalised_app_layout = []
    for app in app_layout:
        app = os.path.expanduser(app)
        if not app.startswith(os.sep) and not app.endswith('.app'):
            normalised_app_layout.append(f'/Applications/{app}.app')
        else:
            normalised_app_layout.append(os.path.normpath(app))

    normalised_other_layout = []
    for other in other_layout:
        # If the current item is a directory path
        if 'path' in other:
            # Normalise the path
            other['path'] = os.path.expanduser(os.path.normpath(other['path']))

            # Set defaults for optional values
            other.setdefault('arrangement', 'Name')
            other.setdefault('display_as', 'Stack')
            other.setdefault('show_as', 'Automatic')

        normalised_other_layout.append(other)

    return normalised_app_layout, normalised_other_layout


def build(app_layout, other_layout, dock_plist_path=None, perform_normalise=True):
    if not dock_plist_path:
        dock_plist_path = get_dock_plist_path()

    if perform_normalise:
        app_layout, other_layout = normalise(app_layout, other_layout)

    # Store the plist contents
    with open(dock_plist_path, 'rb') as fp:
        dock_plist = plistlib.load(fp)

    # Please note that we must set _CFURLStringType to 0 (instead of the usual 15 value)
    # for items we want the Dock to setup correctly for us.  By setting this value to 0,
    # the Dock will take the data we've provided and rebuild the item in the correct format.

    persistent_apps = []
    for app_path in app_layout:
        app_label = os.path.basename(app_path)[:-4]
        persistent_apps.append({
            'GUID': generate_uuid(),
            'tile-data': {
                'file-data': {
                    '_CFURLString': app_path,
                    '_CFURLStringType': 0
                },
                'file-label': app_label
            },
            'tile-type': 'file-tile'
        })

    persistent_others = []
    for other in other_layout:
        # The current item is a directory
        if 'path' in other:
            other_path = other['path']
            other_label = os.path.basename(other['path'])

            persistent_others.append({
                'GUID': generate_uuid(),
                'tile-data': {
                    'file-data': {
                        '_CFURLString': other_path,
                        '_CFURLStringType': 0
                    },
                    'file-label': other_label,
                    'file-type': 2,
                    'arrangement': ARRANGEMENT_MAPPING.lookup(other['arrangement']),
                    'displayas': DISPLAY_AS_MAPPING.lookup(other['display_as']),
                    'showas': SHOW_AS_MAPPING.lookup(other['show_as'])
                },
                'tile-type': 'directory-tile'
            })

        # The current item is a URL
        else:
            persistent_others.append({
                'GUID': generate_uuid(),
                'tile-data': {
                    'label': other['label'],
                    'url': {
                        '_CFURLString': other['url'],
                        '_CFURLStringType': 15
                    }
                },
                'tile-type': 'url-tile'
            })

    dock_plist['persistent-apps'] = persistent_apps
    dock_plist['persistent-others'] = persistent_others

    # Update the Dock plist file with the new layout
    with open(dock_plist_path, 'wb') as fp:
        plistlib.dump(dock_plist, fp)
