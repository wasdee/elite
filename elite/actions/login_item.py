import os

from ScriptingBridge import SBApplication

from . import Action, Argument


class LoginItem(Action):
    def process(self, path, state, hidden):
        # Veriify if the path provided exists
        if not os.path.exists(path):
            self.fail('the path provided could not be found')

        # The scripting bridge pops up in the Dock, so we must explicitly hide the app
        # before starting
        from AppKit import NSBundle
        bundle_info = NSBundle.mainBundle().infoDictionary()
        bundle_info["LSBackgroundOnly"] = True

        # Obtain the System Events application
        system_events = SBApplication.applicationWithBundleIdentifier_('com.apple.systemevents')

        # Note that the import of SystemEventsLoginItem must occur after we initialise
        # system events or it simply won't work.
        # https://bitbucket.org/ronaldoussoren/pyobjc/issues/179/strange-import-behaviour-with
        from Foundation import SystemEventsLoginItem

        # Find a specific login item
        login_items = system_events.loginItems()

        if state == 'present':
            # Search for the login item in the existing login items
            for login_item in login_items:
                # The item path was found
                if login_item.path() == path:
                    # Compare to confirm that the item has the same hidden attribute
                    if login_item.hidden() == hidden:
                        self.ok()

                    # Update the hidden attribute as they differ
                    login_item.setHidden_(hidden)
                    self.changed()

            # Create a new login item
            login_item = SystemEventsLoginItem.alloc().initWithProperties_({
                'path': path,
                'hidden': hidden
            })

            # Add the login item to the list
            login_items.addObject_(login_item)
            self.changed()

        elif state == 'absent':
            # Search for the login item in the existing login items
            for login_item in login_items:
                # The item path was found so we delete it
                if login_item.path() == path:
                    login_item.delete()
                    self.changed()

            # The item was not found as requested
            self.ok()


if __name__ == '__main__':
    login_item = LoginItem(
        Argument('path'),
        Argument('state', choices=['present', 'absent'], default='present'),
        Argument('hidden', default=False)
    )
    login_item.invoke()
