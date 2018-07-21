from . import Action


class Hostname(Action):
    """
    Provides the ability to set the local host name and computer name of the system.

    :param local_host_name: the local host name of the system (without spaces)
    :param computer_name: the computer name of the system (may include spaces)
    """

    __action_name__ = 'hostname'

    def __init__(self, local_host_name=None, computer_name=None, **kwargs):
        self.local_host_name = local_host_name
        self.computer_name = computer_name
        super().__init__(**kwargs)

    def process(self):
        changed = False

        # Coonfigure the local host name
        if self.local_host_name:
            current_local_host_name = self.run(['scutil', '--get', 'LocalHostName'], stdout=True)
            if self.local_host_name != current_local_host_name.stdout.rstrip():
                self.run(['scutil', '--set', 'LocalHostName', self.local_host_name])
                changed = True

        # Configure the computer name
        if self.computer_name:
            current_computer_name = self.run(['scutil', '--get', 'ComputerName'], stdout=True)
            if self.computer_name != current_computer_name.stdout.rstrip():
                self.run(['scutil', '--set', 'ComputerName', self.computer_name])
                changed = True

        return self.changed() if changed else self.ok()
