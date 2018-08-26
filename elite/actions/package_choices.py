import os
import plistlib

from . import Action, ActionError


class PackageChoices(Action):
    """
    Returns available choices for a macOS package (\\*.pkg)

    :param path: the path of the package to work with
    """

    def __init__(self, path, **kwargs):
        self.path = path
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Check that the path exists
        if not os.path.isfile(path):
            raise ActionError('unable to find a file with the path provided')

        # Obtain all installer choices as a plist
        choices_proc = self.run(
            ['installer', '-showChoicesXML', '-package', path, '-target', '/'], stdout=True,
            fail_error='unable to obtain installer information for the path provided'
        )

        # Split the lines and crop output to only include the plist
        # (sometimes the installer command includes extra lines before the plist)
        choices_stdout_lines = choices_proc.stdout.rstrip().split('\n')

        try:
            # Determine the location of the plist header and footer
            choices_plist_start_index = choices_stdout_lines.index(
                '<?xml version="1.0" encoding="UTF-8"?>'
            )
            choices_plist_end_index = choices_stdout_lines.index('</plist>') + 1

            # Only obtain lines of the output which are part of the plist
            choices_plist = '\n'.join(
                choices_stdout_lines[choices_plist_start_index:choices_plist_end_index]
            )

            # Parse the plist provided
            choices = plistlib.loads(choices_plist.encode('utf-8'))
        except (ValueError, IndexError, plistlib.InvalidFileException):
            raise ActionError('unable to parse installer command output')

        return self.ok(choices=choices)
