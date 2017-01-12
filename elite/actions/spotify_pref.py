import os

from . import Argument, Action


def convert_to_spotify_value(value):
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    else:
        return str(value)


class SpotifyPref(Action):
    def process(self, username, pref, value, mode, owner, group):
        # Determine the path of the Spotify prefs file
        if username:
            path = f'~/Library/Application Support/Spotify/Users/{username}-user/prefs'
        else:
            path = f'~/Library/Application Support/Spotify/prefs'

        path = os.path.expanduser(path)

        # Load the Spotify prefs or create a fresh data structure if it doesn't exist
        prefs = {}
        try:
            with open(path, 'r') as f:
                for config_pref_line in f.readlines():
                    config_pref, config_value = config_pref_line.strip().split('=', 1)
                    prefs[config_pref] = config_value
        except ValueError:
            self.fail('unable to parse existing Spotify configuration')
        except IOError:
            pass

        # Check if the provided pref and value is the same as what's in the config file
        if pref in prefs and prefs[pref] == convert_to_spotify_value(value):
            self.ok()

        # Update the config with the pref and value provided
        prefs[pref] = convert_to_spotify_value(value)

        # Create the directory to place the config in if required
        config_dir = os.path.dirname(path)
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
        except IOError:
            self.fail('unable to create the directory to store the Spotify config')

        # Write the updated Spotify config
        try:
            with open(path, 'w') as f:
                for current_pref, current_value in prefs.items():
                    print(f'{current_pref}={current_value}', file=f)

            self.set_file_attributes(path)

            self.changed(path=path)
        except IOError:
            self.fail('unable to update the Spotify config file file')


if __name__ == '__main__':
    spotify_pref = SpotifyPref(
        Argument('username', optional=True),
        Argument('pref'),
        Argument('value'),
        add_file_attribute_args=True
    )
    spotify_pref.invoke()
