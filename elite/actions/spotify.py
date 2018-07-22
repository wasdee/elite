import os

from . import ActionError, FileAction
from ..utils import deep_equal, deep_merge


def convert_to_spotify_value(value):
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, int):
        return str(value)
    else:
        raise ActionError(f'an unexpected value ({value}) was encountered')


def convert_from_spotify_value(value):
    if value in ['true', 'false']:
        return True if value == 'true' else False
    elif value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    else:
        try:
            return int(value)
        except ValueError:
            raise ActionError(f'an unexpected value ({value}) was encountered')


class Spotify(FileAction):
    def __init__(self, values, username=None, **kwargs):
        self.values = values
        self.username = username
        super().__init__(**kwargs)

    def determine_pref_path(self):
        """Determine the path of the Spotify prefs file."""
        if self.username:
            return f'~/Library/Application Support/Spotify/Users/{self.username}-user/prefs'
        else:
            return f'~/Library/Application Support/Spotify/prefs'

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.determine_pref_path())

        # Load the Spotify prefs or create a fresh data structure if it doesn't exist
        prefs = {}
        try:
            with open(path, 'r') as f:
                for line in f.readlines():
                    pref, value = line.rstrip().split('=', 1)
                    prefs[pref] = convert_from_spotify_value(value)
        except ValueError:
            raise ActionError('unable to parse existing Spotify configuration')
        except OSError:
            pass

        # Check if the current prefs are the same as the values provided
        if deep_equal(self.values, prefs):
            changed = self.set_file_attributes(path)
            return self.changed(path=path) if changed else self.ok(path=path)

        # Update the JSON with the values provided
        deep_merge(self.values, prefs)

        # Write the updated Spotify config
        try:
            with open(path, 'w') as f:
                for pref, value in prefs.items():
                    print(f'{pref}={convert_to_spotify_value(value)}', file=f)

            self.set_file_attributes(path)
            return self.changed(path=path)
        except OSError:
            raise ActionError('unable to update the Spotify config file file')
