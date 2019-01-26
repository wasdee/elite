import os

from CoreFoundation import NSURL  # pylint: disable=no-name-in-module
from LaunchServices import (  # pylint: disable=no-name-in-module
    LSSharedFileListCreate, LSSharedFileListInsertItemURL, LSSharedFileListItemCopyResolvedURL,
    LSSharedFileListItemRemove, kLSSharedFileListItemLast, kLSSharedFileListSessionLoginItems
)

from . import Action, ActionError


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

        # Create the new item's bookmark and properties
        url = NSURL.fileURLWithPath_(self.path)
        properties = {'com.apple.loginitem.HideOnLaunch': self.hidden}

        # Find a specific login item
        login_items = LSSharedFileListCreate(None, kLSSharedFileListSessionLoginItems, None)

        if self.state == 'present':
            # Search for the login item in the existing login items
            for login_item in login_items.allItems():
                login_item_url, error = LSSharedFileListItemCopyResolvedURL(login_item, 0, None)
                # The item path was found and has the same hidden setting
                if (
                    not error and login_item_url.path() == url.path() and
                    login_item.properties()['com.apple.loginitem.HideOnLaunch'] == self.hidden
                ):
                    return self.ok()

            # Add (or update) the login item to the list
            LSSharedFileListInsertItemURL(
                login_items, kLSSharedFileListItemLast, None, None, url, properties, None
            )
            return self.changed()

        else:  # 'absent'
            # Search for the login item in the existing login items
            found_item = None
            for login_item in login_items.allItems():
                login_item_url, error = LSSharedFileListItemCopyResolvedURL(login_item, 0, None)

                # The item path was found so we delete it
                if not error and login_item_url.path() == url.path():
                    found_item = login_item
                    break

            if not found_item:
                return self.ok()

            LSSharedFileListItemRemove(login_items, found_item)
            return self.changed()
