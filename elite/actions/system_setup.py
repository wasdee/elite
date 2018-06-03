from . import Argument, Action


class SystemSetup(Action):
    def process(self, timezone, computer_sleep_time, display_sleep_time):
        changed = False

        # Coonfigure the timezone
        if timezone:
            current_timezone = self.run('systemsetup -gettimezone', stdout=True)
            if f'Time Zone: {timezone}' != current_timezone.stdout.rstrip():
                self.run(f'systemsetup -settimezone {timezone}')
                changed = True

        # Configure the computer sleep time
        if computer_sleep_time:
            computer_sleep = self.run('systemsetup -getcomputersleep', stdout=True)
            if (
                f'Computer Sleep: {computer_sleep_time}' !=
                computer_sleep.stdout.rstrip().replace('after ', '').replace('minutes', '')
            ):
                self.run(f'systemsetup -setcomputersleep {computer_sleep_time}')
                changed = True

        # Configure the display sleep
        if display_sleep_time:
            display_sleep = self.run('systemsetup -getdisplaysleep', stdout=True)
            if (
                f'Display Sleep: {display_sleep_time}' !=
                display_sleep.stdout.rstrip().replace('after ', '').replace('minutes', '')
            ):
                self.run(f'systemsetup -setdisplaysleep {display_sleep_time}')
                changed = True

        self.changed() if changed else self.ok()


if __name__ == '__main__':
    system_setup = SystemSetup(
        Argument('timezone', optional=True),
        Argument('computer_sleep_time', optional=True),
        Argument('display_sleep_time', optional=True)
    )
    system_setup.invoke()
