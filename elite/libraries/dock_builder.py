#!/usr/bin/env python3
import os
import plistlib
import urllib.parse

from ..utils import generate_uuid


def get_dock_plist_path():
    return os.path.expanduser('~/Library/Preferences/com.apple.dock.plist')


ARRANGEMENT_MAPPING = {
    1: 'Name',
    2: 'Date Added',
    3: 'Date Modified',
    4: 'Date Created',
    5: 'Kind'
}

ARRANGEMENT_MAPPING_REV = {
    'Name': 1,
    'Date Added': 2,
    'Date Modified': 3,
    'Date Created': 4,
    'Kind': 5,
}

DISPLAY_AS_MAPPING = {
    0: 'Stack',
    1: 'Folder'
}

DISPLAY_AS_MAPPING_REV = {
    'Stack': 0,
    'Folder': 1
}

SHOW_AS_MAPPING = {
    0: 'Automatic',
    1: 'Fan',
    2: 'Grid',
    3: 'List'
}

SHOW_AS_MAPPING_REV = {
    'Automatic': 0,
    'Fan': 1,
    'Grid': 2,
    'List': 3
}


class DockBuilder:
    def __init__(self, dock_plist_path, app_layout=None, other_layout=None):
        if app_layout is None:
            app_layout = []

        if other_layout is None:
            other_layout = []

        # The Dock plist location
        self.dock_plist_path = dock_plist_path

        # App and other layouts
        self.app_layout = app_layout
        self.normalise_app_layout()
        self.other_layout = other_layout
        self.normalise_other_layout()

        # Store the plist contents
        with open(dock_plist_path, 'rb') as fp:
            self.plist = plistlib.load(fp)

    def build(self):
        # Please note that we must set _CFURLStringType to 0 (instead of the usual 15 value)
        # for items we want the Dock to setup correctly for us.  By setting this value to 0,
        # the Dock will take the data we've provided and rebuild the item in the correct format.

        persistent_apps = []
        for app_path in self.app_layout:
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
        for other in self.other_layout:
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
                        'arrangement': ARRANGEMENT_MAPPING_REV[other['arrangement']],
                        'displayas': DISPLAY_AS_MAPPING_REV[other['display_as']],
                        'showas': SHOW_AS_MAPPING_REV[other['show_as']]
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

        self.plist['persistent-apps'] = persistent_apps
        self.plist['persistent-others'] = persistent_others

        # Update the Dock plist file with the new layout
        with open(self.dock_plist_path, 'wb') as fp:
            plistlib.dump(self.plist, fp)

    def normalise_app_layout(self):
        normalised_app_layout = []
        # Normalise each app path
        for app in self.app_layout:
            app = os.path.expanduser(app)
            if not app.startswith(os.sep) and not app.endswith('.app'):
                normalised_app_layout.append(f'/Applications/{app}.app')
            else:
                normalised_app_layout.append(os.path.normpath(app))

        self.app_layout = normalised_app_layout

    def normalise_other_layout(self):
        normalised_other_layout = []
        for other in self.other_layout:
            # If the current item is a directory path
            if 'path' in other:
                # Normalise the path
                other['path'] = os.path.expanduser(os.path.normpath(other['path']))

                # Set defaults for optional values
                other.setdefault('arrangement', 'Name')
                other.setdefault('display_as', 'Stack')
                other.setdefault('show_as', 'Automatic')

            normalised_other_layout.append(other)

        self.other_layout = normalised_other_layout

    def extract(self):
        app_layout = []
        for app in self.plist['persistent-apps']:
            # Obtain a normalised path to the app
            app_url = app['tile-data']['file-data']['_CFURLString']
            app_url_parse = urllib.parse.urlparse(urllib.parse.unquote(app_url))
            app_path = os.path.normpath(app_url_parse.path)

            # Add the app to our app layout
            app_layout.append(app_path)

        other_layout = []
        for other in self.plist['persistent-others']:
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

        self.app_layout = app_layout
        self.other_layout = other_layout

        return app_layout, other_layout
