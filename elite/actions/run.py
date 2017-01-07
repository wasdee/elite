import os

from . import Argument, Action


class Run(Action):
    def process(self, command, working_dir, shell, unless, creates, removes):
        # Check if the created or removed file is already present
        if creates and os.path.exists(creates):
            self.ok()

        if removes and not os.path.exists(removes):
            self.ok

        # Check if the optional check command succeeds
        if unless:
            unless_proc = self.run(unless, shell=True, executable=shell, ignore_fail=True)
            if not unless_proc.returncode:
                self.ok()

        # Run the given command
        proc = self.run(
            command, cwd=working_dir, stdout=True, stderr=True, shell=True, executable=shell
        )
        self.ok(stdout=proc.stdout, stderr=proc.stderr, return_code=proc.returncode)


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
