import os
import plistlib

from . import Action, Argument, FILE_ATTRIBUTE_ARGS
from ..utils import deep_equal, deep_merge


class Plist(Action):
    def validate_args(self, domain, container, path, source, values, mode, owner, group, flags):
        if not domain and not path:
            self.fail("you must provide either the 'domain' or 'path' argument")

        if domain and path:
            self.fail("you may only provide one of the 'domain' or 'path' arguments")

        if container and domain in ['NSGlobalDomain', 'Apple Global Domain']:
            self.fail("the 'container' argument is not allowed when updating the global domain")

    def process(self, domain, container, path, source, values, mode, owner, group, flags):
        # Determine the path of the plist if the domain was provided
        if domain:
            if domain in ['NSGlobalDomain', 'Apple Global Domain']:
                path = '~/Library/Preferences/.GlobalPreferences.plist'
            elif domain and container:
                path = f'~/Library/Containers/{container}/Data/Library/Preferences/{domain}.plist'
            else:
                path = f'~/Library/Preferences/{domain}.plist'

        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)

        # Load the plist or create a fresh data structure if it doesn't exist
        try:
            with open(path, 'rb') as f:
                plist = plistlib.load(f)
        except OSError:
            plist = {}
        except plistlib.InvalidFileException:
            self.fail('an invalid plist already exists')

        # When a source has been defined, we merge values with the source
        if source:
            # Ensure that home directories are taken into account
            source = os.path.expanduser(source)

            try:
                with open(source, 'rb') as f:
                    source_plist = plistlib.load(f)
                    source_plist.update(values)
                    values = source_plist
            except OSError:
                self.fail('the source file provided does not exist')
            except plistlib.InvalidFileException:
                self.fail('the source file is an invalid plist')

        # Check if the current plist is the same as the values provided
        if deep_equal(values, plist):
            changed = self.set_file_attributes(path)
            self.changed(path=path) if changed else self.ok()

        # Update the plist with the values provided
        deep_merge(values, plist)

        # Write the updated plist
        try:
            with open(path, 'wb') as f:
                plistlib.dump(plist, f)

            self.set_file_attributes(path)
            self.changed(path=path)
        except OSError:
            self.fail('unable to update the requested plist')


if __name__ == '__main__':
    plist = Plist(
        Argument('domain', optional=True),
        Argument('container', optional=True),
        Argument('path', optional=True),
        Argument('source', optional=True),
        Argument('values'),
        *FILE_ATTRIBUTE_ARGS
    )
    plist.invoke()
