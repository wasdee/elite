import os
import plistlib

from ..utils import deep_merge
from . import Argument, Action


def equal(source, destination):
    if isinstance(destination, dict) and isinstance(source, dict):
        for key, value in source.items():
            if not equal(destination.get(key), value):
                return False
    else:
        return source == destination

    return True


class Plist(Action):
    def validate_args(self, domain, container, path, values, mode, owner, group):
        if not domain and not path:
            self.fail("you must provide either the 'domain' or 'path' argument")

        if domain and path:
            self.fail("you may only provide one of the 'domain' or 'path' arguments")

        if container and domain in ['NSGlobalDomain', 'Apple Global Domain']:
            self.fail("the 'container' argument is not allowed when updating the global domain")

    def process(self, domain, container, path, values, mode, owner, group):
        # Determine the path of the plist if the domain was provided
        if domain:
            if domain in ['NSGlobalDomain', 'Apple Global Domain']:
                path = '~/Library/Preferences/.GlobalPreferences.plist'
            elif domain and container:
                path = f'~/Library/Containers/{container}/Data/Library/Preferences/{domain}.plist'
            else:
                path = f'~/Library/Preferences/{domain}.plist'

        path = os.path.expanduser(path)

        # Load the plist or create a fresh data structure if it doesn't exist
        try:
            with open(path, 'rb') as f:
                plist = plistlib.load(f)
        except IOError:
            plist = {}
        except plistlib.InvalidFileException:
            self.fail('an invalid plist already exists')

        # Check if the current plist is the same as the values provided
        if equal(values, plist):
            self.ok()

        # Update the plist with the values provided
        deep_merge(values, plist)

        # Create the directory to place the plist in if required
        plist_dir = os.path.dirname(path)
        try:
            if not os.path.exists(plist_dir):
                os.makedirs(plist_dir)
        except IOError:
            self.fail('unable to create the directory to store the plist')

        # Write the updated plist
        try:
            with open(path, 'wb') as f:
                plistlib.dump(plist, f)

            self.set_file_attributes(path)

            self.changed(path=path)
        except IOError:
            self.fail('unable to update the requested plist file')


if __name__ == '__main__':
    plist = Plist(
        Argument('domain', optional=True),
        Argument('container', optional=True),
        Argument('path', optional=True),
        Argument('values'),
        add_file_attribute_args=True
    )
    plist.invoke()
