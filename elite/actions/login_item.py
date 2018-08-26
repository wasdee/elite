import os

from AppKit import NSBundle  # pylint: disable=no-name-in-module
from ScriptingBridge import SBApplication  # pylint: disable=no-name-in-module
# Note that the import of SystemEventsLoginItem must occur after we initialise
# system events or it simply won't work.
# https://bitbucket.org/ronaldoussoren/pyobjc/issues/179/strange-import-behaviour-with
system_events = SBApplication.applicationWithBundleIdentifier_('com.apple.systemevents')  # noqa
# pylint: disable=wrong-import-position
from Foundation import SystemEventsLoginItem  # noqa: I100, pylint: disable=no-name-in-module

from . import Action, ActionError
# pylint: enable=wrong-import-position


class LoginItem(Action):
    """
    Manages a macOS login item.

    :param path: the path of the app
    :param state: the state that the login item must be in
    :param hidden: whether the app should start hidden or not
    """

    def __init__(self, path, state='present', hidden=False, **kwargs):
        self._state = state
        self.path = path
        self.state = state
        self.hidden = hidden
        super().__init__(**kwargs)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['present', 'absent']:
            raise ValueError('state must be present or absent')
        self._state = state

    def process(self):
        # Veriify if the path provided exists
        if not os.path.exists(self.path):
            raise ActionError('the path provided could not be found')

        # The scripting bridge pops up in the Dock, so we must explicitly hide the app
        # before starting
        bundle_info = NSBundle.mainBundle().infoDictionary()
        bundle_info['LSBackgroundOnly'] = True

        # Find a specific login item
        login_items = system_events.loginItems()

        if self.state == 'present':
            # Search for the login item in the existing login items
            for login_item in login_items:
                # The item path was found
                if login_item.path() == self.path:
                    # Compare to confirm that the item has the same hidden attribute
                    if login_item.hidden() == self.hidden:
                        return self.ok()

                    # Update the hidden attribute as they differ
                    login_item.setHidden_(self.hidden)
                    return self.changed()

            # Create a new login item
            login_item = SystemEventsLoginItem.alloc().initWithProperties_({
                'path': self.path,
                'hidden': self.hidden
            })

            # Add the login item to the list
            login_items.addObject_(login_item)
            return self.changed()

        else:  # 'absent'
            # Search for the login item in the existing login items
            for login_item in login_items:
                # The item path was found so we delete it
                if login_item.path() == self.path:
                    login_item.delete()
                    return self.changed()

            # The item was not found as requested
            return self.ok()
