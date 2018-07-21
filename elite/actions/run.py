import os

from . import Action


class Run(Action):
    """
    Runs a command, determines whether it has changed anything using various criteria and then
    returns the output to the caller if a change is detected.

    :param command: the command to execute
    :param working_dir: the directory in which to execute the command
    :param shell: the shell to use while executing the command
    :param unless: another command to run which indicates no change if that command has a
                   return code of zero
    :param creates: a path whose existence indicates that nothing has changed
    :param removes: a path whose lack of existence indicates that nothing has changed
    """

    __action_name__ = 'run'

    def __init__(
        self, command, working_dir=None, shell=None, unless=None, creates=None, removes=None,
        **kwargs
    ):
        self.command = command
        self.working_dir = working_dir
        self.shell = shell
        self.unless = unless
        self.creates = creates
        self.removes = removes
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        working_dir = os.path.expanduser(self.working_dir) if self.working_dir else None
        creates = os.path.expanduser(self.creates) if self.creates else None
        removes = os.path.expanduser(self.removes) if self.removes else None

        # Check if the created or removed file is already present
        if creates and os.path.exists(creates):
            return self.ok()

        if removes and not os.path.exists(removes):
            return self.ok()

        # Build the kwargs to send to subprocess
        kwargs = {'cwd': working_dir}
        if self.shell:
            kwargs.update(shell=True, executable=self.shell)

        # Check if the optional check command succeeds
        if self.unless:
            unless_proc = self.run(self.unless, ignore_fail=True, **kwargs)
            if unless_proc.returncode == 0:
                return self.ok()

        # Run the given command
        proc = self.run(self.command, stdout=True, stderr=True, **kwargs)
        return self.changed(stdout=proc.stdout, stderr=proc.stderr, return_code=proc.returncode)
