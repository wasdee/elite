import os
import plistlib

from . import ActionError, FileAction
from ..utils import deep_equal, deep_merge


class Plist(FileAction):
    __action_name__ = 'plist'

    def __init__(
        self, values, path=None, domain=None, container=None, source=None, fmt='xml', **kwargs
    ):
        self._domain = None
        self._container = None
        self._path = None
        self._fmt = None
        self.values = values
        self.path = path
        self.domain = domain
        self.container = container
        self.source = source
        self.fmt = fmt
        super().__init__(**kwargs)

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, domain):
        if not domain and not self.path:
            raise ValueError("you must provide either the 'domain' or 'path' argument")
        if domain and self.path:
            raise ValueError("you may only provide one of the 'domain' or 'path' arguments")
        if self.container and domain in ['NSGlobalDomain', 'Apple Global Domain']:
            raise ValueError(
                "the 'container' argument is not allowed when updating the global domain"
            )
        self._domain = domain

    @property
    def container(self):
        return self._container

    @container.setter
    def container(self, container):
        if container and not self.domain:
            raise ValueError(
                "the 'domain' argument is required when specifying the container argument"
            )
        if container and self.domain in ['NSGlobalDomain', 'Apple Global Domain']:
            raise ValueError(
                "the 'container' argument is not allowed when updating the global domain"
            )
        self._container = container

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        if not self.domain and not path:
            raise ValueError("you must provide either the 'domain' or 'path' argument")
        if self.domain and path:
            raise ValueError("you may only provide one of the 'domain' or 'path' arguments")
        self._path = path

    @property
    def fmt(self):
        return self._fmt

    @fmt.setter
    def fmt(self, fmt):
        if fmt not in ['xml', 'binary']:
            raise ValueError('fmt must be xml or binary')
        self._fmt = fmt

    def determine_plist_path(self):
        """Determine the path of the plist using the domain or container provided."""
        if self.domain:
            if self.domain in ['NSGlobalDomain', 'Apple Global Domain']:
                return '~/Library/Preferences/.GlobalPreferences.plist'
            elif self.domain and self.container:
                return (
                    f'~/Library/Containers/{self.container}/Data/Library/Preferences/'
                    f'{self.domain}.plist'
                )
            else:
                return f'~/Library/Preferences/{self.domain}.plist'
        else:
            return self.path

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.determine_plist_path())

        # Set the fmt of the output file
        # pylint: disable=no-member
        fmt = plistlib.FMT_XML if self.fmt == 'xml' else plistlib.FMT_BINARY

        # Load the plist or create a fresh data structure if it doesn't exist
        try:
            with open(path, 'rb') as f:
                plist = plistlib.load(f)
        except OSError:
            plist = {}
        except plistlib.InvalidFileException:
            raise ActionError('an invalid plist already exists')

        values = self.values

        # When a source has been defined, we merge values with the source
        if self.source:
            # Ensure that home directories are taken into account
            source = os.path.expanduser(self.source)

            try:
                with open(source, 'rb') as f:
                    source_plist = plistlib.load(f)
                    source_plist.update(self.values)
                    values = source_plist
            except OSError:
                raise ActionError('the source file provided does not exist')
            except plistlib.InvalidFileException:
                raise ActionError('the source file is an invalid plist')

        # Check if the current plist is the same as the values provided
        if deep_equal(values, plist):
            changed = self.set_file_attributes(path)
            return self.changed(path=path) if changed else self.ok(path=path)

        # Update the plist with the values provided
        deep_merge(values, plist)

        # Write the updated plist
        try:
            with open(path, 'wb') as f:
                plistlib.dump(plist, f, fmt=fmt)

            self.set_file_attributes(path)
            return self.changed(path=path)
        except OSError:
            raise ActionError('unable to update the requested plist')
