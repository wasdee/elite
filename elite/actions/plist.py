import os
import plistlib

from . import ActionError, FileAction
from ..utils import deep_equal, deep_merge


class Plist(FileAction):
    """
    Provides the ability to manipulate macOS property list configuration files.

    :param values: a dictionary containing the data to be incorporated into the config
    :param path: the full path of the plist file to manipulate
    :param domain: the app domain name of the plist to manipulate
    :param container: the sandbox container name of the plist to manipulate
    :param source: the path of an additional plist file to incorporate with the values provided
    :param fmt: the format of the plist file to write (xml or binary)
    """

    def __init__(
        self, values, path=None, domain=None, container=None, source=None, fmt='xml', **kwargs
    ):
        self._path = path
        self._domain = domain
        self._container = container
        self._fmt = fmt
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
        if self.fmt == 'xml':
            fmt = plistlib.FMT_XML  # pylint: disable=no-member
        else:
            fmt = plistlib.FMT_BINARY  # pylint: disable=no-member

        # Load the plist or create a fresh data structure if it doesn't exist
        try:
            with open(path, 'rb') as fp:
                plist = plistlib.load(fp)
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
                with open(source, 'rb') as fp:
                    source_plist = plistlib.load(fp)
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
            with open(path, 'wb') as fp:
                plistlib.dump(plist, fp, fmt=fmt)

            self.set_file_attributes(path)
            return self.changed(path=path)
        except OSError:
            raise ActionError('unable to update the requested plist')
