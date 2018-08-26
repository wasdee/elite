import os
import plistlib
import tempfile
import urllib.parse
from xml.etree import ElementTree

from . import Action, ActionError


class Package(Action):
    """
    Provides the ability to manage macOS package installation (\\*.pkg).

    :param path: the path of the package to work with
    :param choices: a dictionary containing any choice overrides during installation
    :param target: the target path to install into
    """

    # The locations to search for receipts
    receipts_dirs = ['/System/Library/Receipts', '/private/var/db/receipts']

    def __init__(self, path, choices=None, target='/', **kwargs):
        self.path = path
        self.choices = choices
        self.target = target
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Check that the path exists
        if not os.path.isfile(path):
            raise ActionError('unable to find a file with the path provided')

        # Ensure that the package is being installed with root priveleges
        if os.geteuid() != 0:
            raise ActionError('package installers must be run with root privileges')

        # Create a temporary directory to store our package metadata in
        package_extract_dir = tempfile.mkdtemp()

        # Extract the Distribution or PackageInfo files from the root of the package
        self.run(
            [
                'xar',
                '-xf', path,
                '-C', package_extract_dir,
                '^Distribution$', '^PackageInfo$', '/PackageInfo$'
            ],
            fail_error='unable to extract the provided package for examination'
        )

        # Expected Distribution file that points to multiple other packages was not found
        if not os.path.exists(os.path.join(package_extract_dir, 'Distribution')):
            raise ActionError(
                'unable to find a Distribution or PackageInfo file in the root of the package'
            )

        # Create a list to store all identifiers found
        identifiers = []

        # Determine the full path of the Distribution file being referenced
        distribution = os.path.join(package_extract_dir, 'Distribution')

        # Parse the Distribution XML file and iterate through all pkg-ref tags found
        try:
            tree = ElementTree.parse(distribution)
            root = tree.getroot()
        except ElementTree.ParseError:
            raise ActionError('unable to parse the Distribution XML contained in the package')

        for pkg_ref in root.iter('pkg-ref'):
            # Ensure that we strip whitespace which ocassionally can be present in
            # this variable (e.g. Microsoft Office had this problem)
            if pkg_ref.text:
                pkg_ref.text = pkg_ref.text.strip()

            # We are only interested in pkg-ref items containing a value which points to
            # an included package file.
            #
            # A 'file:' reference implies the package is a separate package outside the given
            # package.  Such items don't appear in the receipts after installation
            # (e.g. Native Instruments sample library installers).
            #
            # If installKBytes has been specified and is 0, the pkg-ref also won't receive
            # a dedicated receipt and therefore should be skipped.
            if (
                not pkg_ref.text or
                pkg_ref.text.startswith('file:') or
                pkg_ref.attrib.get('installKBytes') == '0'
            ):
                # The following continue statement is definitely reached by unit tests
                # but isn't detected by Coverage.py due to the issue
                # https://bitbucket.org/ned/coveragepy/issues/198/continue-marked-as-not-covered
                continue  # pragma: no cover

            # Normalise the package being referenced which normally is urlencoded and
            # starts with a # character.
            ref_package = urllib.parse.unquote(pkg_ref.text)
            if ref_package.startswith('#'):
                ref_package = ref_package[1:]

            # Determine the full path of the PackageInfo file being referenced
            package_info = os.path.join(package_extract_dir, ref_package, 'PackageInfo')

            # Parse the PackageInfo XML file so we can obtain the bundle id identifier
            try:
                tree = ElementTree.parse(package_info)
                root = tree.getroot()
            except ElementTree.ParseError:
                raise ActionError(
                    'unable to parse the PackageInfo XML contained in the package'
                )

            # Append the associated bundle id (identifier) to our list of identifiers
            try:
                identifiers.append(root.attrib['identifier'])
            except KeyError:
                raise ActionError('unable to determine bundle id identifier for package')

        if not identifiers:
            raise ActionError('unable to find any installable components for this package')

        # Determine if all bundle id identifiers are installed on the system
        package_installed = True

        for identifier in identifiers:
            # We start by assuming the identifier is not installed
            identifier_installed = False

            # Search for the identifier plist and bom in the available receipts directories
            # to verify if it is installed or not
            for receipts_dir in self.receipts_dirs:
                if (
                    os.path.exists(os.path.join(receipts_dir, f'{identifier}.plist')) and
                    os.path.exists(os.path.join(receipts_dir, f'{identifier}.bom'))
                ):
                    identifier_installed = True
                    break

            # All identifiers must be installed for the package to be considered installed
            package_installed = package_installed and identifier_installed
            if not package_installed:
                break

        # The package was fully installed on the system so we don't need to run the installer
        if package_installed:
            return self.ok()

        installer_command = ['installer']

        # If choices have been provided, we must create a temporary plist file and pass
        # it to the installer
        if self.choices:
            # Create a temporary plist for use in providing choices to the installer
            _choices_plist_fd, choices_plist_path = tempfile.mkstemp()
            with open(choices_plist_path, 'wb') as fp:
                plistlib.dump(self.choices, fp)

            # Pass the path of the choices plist to the installer command
            installer_command.extend(['-applyChoiceChangesXML', choices_plist_path])

        # Specify the package and target
        installer_command.extend(['-package', path, '-target', self.target])

        # Run the installer
        try:
            self.run(installer_command, fail_error='unable to install the requested package')
        finally:
            # Ensure that the temporary choices plist file is cleaned up
            if self.choices:
                os.remove(choices_plist_path)
        return self.changed()
