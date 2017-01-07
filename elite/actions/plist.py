import os
import plistlib

from . import Argument, Action


class Plist(Action):
    def process(self, domain, container, path, values):
        # Determine the path of the plist
        if domain in ['NSGlobalDomain', 'Apple Global Domain']:
            path = '~/Library/Preferences/.GlobalPreferences.plist'
        elif domain and container:
            path = f'~/Library/Containers/{container}/Data/Library/Preferences/{domain}.plist'
        elif domain:
            path = f'~/Library/Preferences/{domain}.plist'

        path = os.path.expanduser(path)

        # Update the plist as requested
        working_values = values

        created = False
        try:
            with open(path, 'rb') as f:
                plist = plistlib.load(f)
        except IOError:
            created = True
            plist = {}
        except plistlib.InvalidFileException:
            self.fail('an invalid plist already exists')

        if self.equal(plist, working_values):
            self.ok()

        self.update(plist, working_values)
        plist_dir = os.path.dirname(path)

        try:
            if not os.path.exists(plist_dir):
                os.makedirs(plist_dir)
        except IOError:
            self.fail('unable to create the directory to store the plist')

        try:
            with open(path, 'wb') as f:
                plistlib.dump(plist, f)

            if created:
                self.changed('plist created successfully')
            else:
                self.changed('plist updated successfully')
        except IOError:
            self.fail(f'unable to update the requested plist file')

    def equal(self, slave, master):
        if isinstance(slave, dict) and isinstance(master, dict):
            for key, value in master.items():
                if not self.equal(slave.get(key), value):
                    return False
        else:
            return master == slave

        return True

    def update(self, plist, working_values):
        for key, value in working_values.items():
            if isinstance(value, dict):
                plist[key] = self.update(plist.get(key, {}), value)
            else:
                plist[key] = working_values[key]

        return plist


if __name__ == '__main__':
    plist = Plist(
        Argument('domain', optional=True),
        Argument('container', optional=True),
        Argument('path', optional=True),
        Argument('values')
    )
    plist.invoke()
