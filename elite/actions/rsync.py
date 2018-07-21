import ast
import os

from . import Action


class Rsync(Action):
    __action_name__ = 'rsync'

    def __init__(self, path, source, executable=None, archive=True, options=None, **kwargs):
        self.path = path
        self.source = source
        self.executable = executable
        self.archive = archive
        self.options = options
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)
        source = os.path.expanduser(self.source)

        # Determine the rsync executable
        executable = self.executable if self.executable else 'rsync'

        # Create a list to store our rsync options
        options_list = []

        if self.archive:
            options_list.append('--archive')

        # Add any additional user provided options
        options_list.extend(self.options if self.options else [])

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
            return self.ok()

        # Changes were found and must be reported to the user
        changes = [ast.literal_eval(c) for c in rsync_output.split('\n')]
        return self.changed(changes=changes)
