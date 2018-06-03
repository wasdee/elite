from . import Argument, Action


class Hostname(Action):
    def process(self, local_host_name, computer_name):
        changed = False

        # Coonfigure the local host name
        if local_host_name:
            current_local_host_name = self.run('scutil --get LocalHostName', stdout=True)
            if local_host_name != current_local_host_name.stdout.rstrip():
                self.run(f'scutil --set LocalHostName "{local_host_name}"')
                changed = True

        # Configure the computer name
        if computer_name:
            current_computer_name = self.run('scutil --get ComputerName', stdout=True)
            if computer_name != current_computer_name.stdout.rstrip():
                self.run(f'scutil --set ComputerName "{computer_name}"')
                changed = True

        self.changed() if changed else self.ok()


if __name__ == '__main__':
    hostname = Hostname(
        Argument('local_host_name', optional=True),
        Argument('computer_name', optional=True)
    )
    hostname.invoke()
