from . import Action


class SystemSetup(Action):
    """
    Provides the ability to control various system properties via the systemsetup command.

    :param timezone: the timezone of the system
    :param computer_sleep_time: the amount of idle time until the computer sleeps
    :param display_sleep_time: the amount of idle time until display sleeps
    :param hard_disk_sleep_time: the amount of idle time until hard disk sleeps
    """

    __action_name__ = 'system_setup'

    def __init__(
        self, timezone=None, computer_sleep_time=None, display_sleep_time=None,
        hard_disk_sleep_time=None
    ):
        self.timezone = timezone
        self.computer_sleep_time = computer_sleep_time
        self.display_sleep_time = display_sleep_time
        self.hard_disk_sleep_time = hard_disk_sleep_time

    def process(self):
        changed = False

        # Coonfigure the timezone
        if self.timezone:
            current_timezone = self.run(['systemsetup', '-gettimezone'], stdout=True)
            if f'Time Zone: {self.timezone}' != current_timezone.stdout.rstrip():
                self.run(['systemsetup', '-settimezone', self.timezone])
                changed = True

        # Configure the computer sleep time
        if self.computer_sleep_time:
            computer_sleep = self.run(['systemsetup', '-getcomputersleep'], stdout=True)
            if (
                f'Computer Sleep: {self.computer_sleep_time}' !=
                computer_sleep.stdout.rstrip().replace('after ', '').replace(' minutes', '')
            ):
                self.run(['systemsetup', '-setcomputersleep', self.computer_sleep_time])
                changed = True

        # Configure the display sleep
        if self.display_sleep_time:
            display_sleep = self.run(['systemsetup', '-getdisplaysleep'], stdout=True)
            if (
                f'Display Sleep: {self.display_sleep_time}' !=
                display_sleep.stdout.rstrip().replace('after ', '').replace(' minutes', '')
            ):
                self.run(['systemsetup', '-setdisplaysleep', self.display_sleep_time])
                changed = True

        # Configure the hard disk sleep
        if self.hard_disk_sleep_time:
            display_sleep = self.run(['systemsetup', '-getharddisksleep'], stdout=True)
            if (
                f'Hard Disk Sleep: {self.hard_disk_sleep_time}' !=
                display_sleep.stdout.rstrip().replace('after ', '').replace(' minutes', '')
            ):
                self.run(['systemsetup', '-setharddisksleep', self.hard_disk_sleep_time])
                changed = True

        return self.changed() if changed else self.ok()
