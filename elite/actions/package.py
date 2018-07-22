import os
import plistlib
import tempfile
import urllib.parse
from xml.etree import ElementTree

from . import Action, ActionError


class Package(Action):
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

        # Distribution file was found which points to multiple other packages
        # pylint: disable=line-too-long
        # https://developer.apple.com/library/content/documentation/DeveloperTools/Reference/DistributionDefinitionRef/Chapters/Distribution_XML_Ref.html
        if os.path.exists(os.path.join(package_extract_dir, 'Distribution')):
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
                    continue

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

        elif os.path.exists(os.path.join(package_extract_dir, 'PackageInfo')):
            # Determine the full path of the PackageInfo file being referenced
            package_info = os.path.join(package_extract_dir, 'PackageInfo')

            # Parse the PackageInfo XML file so we can obtain the bundle id identifier
            try:
                tree = ElementTree.parse(package_info)
                root = tree.getroot()
            except ElementTree.ParseError:
                raise ActionError('unable to parse the PackageInfo XML contained in the package')

            # Set our identifiers to a list of one item containing the bundle id
            try:
                identifiers = [root.attrib['identifier']]
            except KeyError:
                raise ActionError('unable to determine bundle id identifier for package')
        else:
            raise ActionError(
                'unable to find a Distribution or PackageInfo file in the root of the package'
            )

        # Determine if all bundle id identifiers are installed on the system
        package_installed = True

        for identifier in identifiers:
            # We start by assuming the identifier is not installed
            identifier_installed = False

            # Search for the identifier plist and bom in the available receipts directories
            # to verify if it is installed or not
            for receipts_dir in ['/System/Library/Receipts', '/private/var/db/receipts']:
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

        # Ensure that the package is being installed with root priveleges
        if os.geteuid() != 0:
            raise ActionError('package installers must be run with root privileges')

        installer_command = ['installer']

        # If choices have been provided, we must create a temporary plist file and pass
        # it to the installer
        if self.choices:
            # Create a temporary plist for use in providing choices to the installer
            _choices_plist_fd, choices_plist_name = tempfile.mkstemp()
            with open(choices_plist_name, 'wb') as f:
                plistlib.dump(self.choices, f)

            # Pass the path of the choices plist to the installer command
            installer_command.extend(['-applyChoiceChangesXML', choices_plist_name])

        # Specify the package and target
        installer_command.extend(['-package', path, '-target', self.target])

        # Run the installer
        self.run(installer_command, fail_error='unable to install the requested package')
        return self.changed()
