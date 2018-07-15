import os

from . import ActionError, FileAction


def convert_to_spotify_value(value):
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    else:
        return str(value)


class SpotifyPref(FileAction):
    __action_name__ = 'spotify_pref'

    def __init__(self, pref, value, username=None, **kwargs):
        self.username = username
        self.pref = pref
        self.value = value
        super().__init__(**kwargs)

    def process(self):
        # Determine the path of the Spotify prefs file
        if self.username:
            path = f'~/Library/Application Support/Spotify/Users/{self.username}-user/prefs'
        else:
            path = f'~/Library/Application Support/Spotify/prefs'

        path = os.path.expanduser(path)

        # Load the Spotify prefs or create a fresh data structure if it doesn't exist
        prefs = {}
        try:
            with open(path, 'r') as f:
                for config_pref_line in f.readlines():
                    config_pref, config_value = config_pref_line.rstrip().split('=', 1)
                    prefs[config_pref] = config_value
        except ValueError:
            raise ActionError('unable to parse existing Spotify configuration')
        except OSError:
            pass

        # Check if the provided pref and value is the same as what's in the config file
        if self.pref in prefs and prefs[self.pref] == convert_to_spotify_value(self.value):
            changed = self.set_file_attributes(path)
            return self.changed(path=path) if changed else self.ok()

        # Update the config with the pref and value provided
        prefs[self.pref] = convert_to_spotify_value(self.value)

        # Write the updated Spotify config
        try:
            with open(path, 'w') as f:
                for current_pref, current_value in prefs.items():
                    print(f'{current_pref}={current_value}', file=f)

            self.set_file_attributes(path)
            return self.changed(path=path)
        except OSError:
            raise ActionError('unable to update the Spotify config file file')
