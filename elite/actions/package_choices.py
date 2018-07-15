import os
import plistlib
import tempfile

from . import Action, Argument


class PackageChoices(Action):
    def process(self, path):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)

        # Check that the path exists
        if not os.path.isfile(path):
            self.fail('unable to find a file with the path provided')

        # Create a temporary plist for use in determining the installer choices
        empty_plist_fd, empty_plist_name = tempfile.mkstemp()
        with open(empty_plist_name, 'wb') as f:
            plistlib.dump([], f)

        # Obtain all installer choices as a plist
        choices_proc = self.run(
            [
                'installer',
                '-showChoicesAfterApplyingChangesXML', empty_plist_name,
                '-package', path,
                '-target', '/'
            ],
            stdout=True,
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
            self.fail('unable to parse installer command output')

        self.ok(choices=choices)


if __name__ == '__main__':
    package_choices = PackageChoices(
        Argument('path')
    )
    package_choices.invoke()
