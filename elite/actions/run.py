import os

from . import Action, Argument


class Run(Action):
    def process(self, command, working_dir, shell, unless, creates, removes):
        # Ensure that home directories are taken into account
        if working_dir:
            working_dir = os.path.expanduser(working_dir)
        if creates:
            creates = os.path.expanduser(creates)
        if removes:
            removes = os.path.expanduser(removes)

        # Check if the created or removed file is already present
        if creates and os.path.exists(creates):
            self.ok()

        if removes and not os.path.exists(removes):
            self.ok()

        # Build the kwargs to send to subprocess
        kwargs = {'cwd': working_dir}
        if shell:
            kwargs.update(shell=True, executable=shell)

        # Check if the optional check command succeeds
        if unless:
            unless_proc = self.run(unless, ignore_fail=True, **kwargs)
            if not unless_proc.returncode:
                self.ok()

        # Run the given command
        proc = self.run(command, stdout=True, stderr=True, **kwargs)
        self.changed(stdout=proc.stdout, stderr=proc.stderr, return_code=proc.returncode)


if __name__ == '__main__':
    run = Run(
        Argument('command'),
        Argument('working_dir', optional=True),
        Argument('shell', default='/bin/bash'),
        Argument('unless', optional=True),
        Argument('creates', optional=True),
        Argument('removes', optional=True)
    )
    run.invoke()
