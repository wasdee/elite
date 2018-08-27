import os
import plistlib

from . import ActionError, FileAction


def get_ncprefs_plist_path():
    return os.path.expanduser('~/Library/Preferences/com.apple.ncprefs.plist')


class Notifications(FileAction):
    """
    Configures notifications for a particular application.

    :param path: the path of the app
    :param alert_style: the alert style to use
    :param lock_screen: whether notifications should appear on the lock screen
    :param notification_center: whether notifications should appear in notification center
    :param badge_app_icon: whether to display a badge app icon for notifications
    :param sound: whether to play a sound for notifications
    """

    def __init__(
        self, path, alert_style=None, lock_screen=None, notification_center=None,
        badge_app_icon=None, sound=None, **kwargs
    ):
        self._alert_style = alert_style
        self.path = path
        self.alert_style = alert_style
        self.lock_screen = lock_screen
        self.notification_center = notification_center
        self.badge_app_icon = badge_app_icon
        self.sound = sound
        super().__init__(**kwargs)

    @property
    def alert_style(self):
        return self._alert_style

    @alert_style.setter
    def alert_style(self, alert_style):
        if alert_style not in [None, 'None', 'Banners', 'Alerts']:
            raise ValueError('alert style must be unspecified or None, Banners or Alerts')
        self._alert_style = alert_style

    def process(self):
        # Determine the location of the Notification Center preferences plist file
        ncprefs_plist_path = get_ncprefs_plist_path()

        # Read the existing notification center preferences
        try:
            with open(ncprefs_plist_path, 'rb') as fp:
                ncprefs_plist = plistlib.load(fp)
        except OSError:
            raise ActionError('unable to find the notification center preferences file')
        except plistlib.InvalidFileException:
            raise ActionError('unable to parse notification center preferences')

        # Search for the requested app and obtain its current flags
        try:
            app = next(
                filter(
                    lambda a: 'path' in a and 'flags' in a and a['path'] == self.path,
                    ncprefs_plist['apps']
                )
            )
            flags = app['flags']
        except StopIteration:
            raise ActionError('unable to find the app with the path provided')

        # Update flags as requested by the user
        alert_style_changed = False
        if self.alert_style is not None:
            original_flags = flags

            # Clear the current alert style (which is also equivalent to an alert style of 'None')
            flags &= ~0b111000

            if self.alert_style == 'Banners':
                flags |= 0b001000
            elif self.alert_style == 'Alerts':
                flags |= 0b010000

            alert_style_changed = original_flags != flags

        if self.lock_screen is not None:
            if self.lock_screen:
                flags &= ~0b1000000000000
            else:
                flags |= 0b1000000000000

        notification_center_changed = False
        if self.notification_center is not None:
            original_flags = flags

            if self.notification_center:
                flags &= ~0b1
            else:
                flags |= 0b1

            notification_center_changed = original_flags != flags

        if self.badge_app_icon is not None:
            if self.badge_app_icon:
                flags |= 0b10
            else:
                flags &= ~0b10

        if self.sound is not None:
            if self.sound:
                flags |= 0b100
            else:
                flags &= ~0b100

        # The existing flags are identical to that provided
        if flags == app['flags']:
            changed = self.set_file_attributes(ncprefs_plist_path)
            return self.changed() if changed else self.ok()

        if notification_center_changed:
            # Set a permanent bit indicating that the notification center setting has been
            # modified from defaults
            flags |= 0b100000000

        if alert_style_changed:
            # Set a permanent bit indicating that the alert style has been modified from defaults
            flags |= 0b1000000

        # Update the ncprefs plist with the updated flags
        app['flags'] = flags

        try:
            with open(ncprefs_plist_path, 'wb') as fp:
                plistlib.dump(ncprefs_plist, fp)

            # The rebuild was successful
            self.set_file_attributes(ncprefs_plist_path)
            return self.changed()
        except OSError:
            raise ActionError('unable to update the notification center preferences')
