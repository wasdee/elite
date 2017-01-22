import ast
import os
import shlex
import shutil

from . import Argument, Action


class Rsync(Action):
    def process(self, path, source, executable, archive, options):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)
        source = os.path.expanduser(source)

        # Determine the rsync executable
        if not executable:
            executable = shutil.which('rsync')
            if not executable:
                self.fail('unable to find rsync executable to use')

        # Create a list to store our rsync options
        options_list = []

        if archive:
            options_list.append('--archive')

        # Add any additional user provided options
        options_list.extend(shlex.split(options) if options else [])

        # The output we want from rsync is a tuple containing the operation and filename of
        # each affected file
        options_list.append("--out-format=('%o', '%n')")

        # Run rsync to sync the files requested
        rsync_proc = self.run(
            [executable] + options_list + [source, path], stdout=True,
            fail_error='rsync failed to sync the requested source to path'
        )

        # Obtain rsync output and check to see if any changes were made
        rsync_output = rsync_proc.stdout.strip()
        if not rsync_output:
            self.ok()

        # Changes were found and must be reported to the user
        changes = [ast.literal_eval(c) for c in rsync_output.split('\n')]
        self.changed(changes=changes)


if __name__ == '__main__':
    rsync = Rsync(
        Argument('path'),
        Argument('source'),
        Argument('executable', optional=True),
        Argument('archive', default=True),
        Argument('options', optional=True)
    )
    rsync.invoke()
