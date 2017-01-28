import os

from Foundation import NSURL, kCFAllocatorDefault
from LaunchServices import (
    LSSharedFileListCreate, LSSharedFileListInsertItemURL, LSSharedFileListRemoveAllItems,
    kLSSharedFileListFavoriteItems, kLSSharedFileListItemLast
)

from . import Argument, Action


class Favourites(Action):
    def process(self, layout):
        # Build a data structure containing the layout of the requested favourites
        structure = []

        for item in layout:
            # All My Files
            if item == 'All My Files':
                url = NSURL.fileURLWithPath_(
                    '/System/Library/CoreServices/Finder.app'
                    '/Contents/Resources/MyLibraries/myDocuments.cannedSearch/'
                )
                name = 'All My Files'
                properties = {}

            # iCloud Drive
            elif item == 'iCloud Drive':
                url = NSURL.URLWithString_('x-apple-finder:icloud')
                name = 'iCloud'
                properties = {
                    'kLSSharedFileListItemUserIsiCloud': True
                }

            # AirDrop
            elif item == 'AirDrop':
                url = NSURL.URLWithString_('nwnode://domain-AirDrop')
                name = 'domain-AirDrop'
                properties = {
                    'com.apple.LSSharedFileList.SpecialItemIdentifier':
                    'com.apple.LSSharedFileList.IsMeetingRoom'
                }

            # Folder
            else:
                # Ensure that the folder is a normalised absolute path
                item = os.path.normpath(os.path.abspath(os.path.expanduser(item)))

                url = NSURL.fileURLWithPath_(item)
                name = os.path.basename(item)
                properties = {}

            structure.append((url, name, properties))

        # Obtain current favourites in the sidebar
        current_favourites = LSSharedFileListCreate(
            kCFAllocatorDefault, kLSSharedFileListFavoriteItems, None
        )

        # Build a data structure containing the layout of the current favourites
        current_structure = []

        for sidebar_item in current_favourites.items():
            url = sidebar_item.URL()
            name = str(sidebar_item.name())
            properties = dict(sidebar_item.properties() or {})

            current_structure.append((url, name, properties))

        # The existing layout is identical to that provided
        if structure == current_structure:
            self.ok()

        # Remove all items from the Finder sidebar
        LSSharedFileListRemoveAllItems(current_favourites)

        # Add the requested items to the Filder sidebar in the order specified
        for url, name, properties in structure:
            LSSharedFileListInsertItemURL(
                current_favourites,          # inList
                kLSSharedFileListItemLast,  # insertAfterThisItem
                name,                       # inDisplayName
                None,                       # inIconRef
                url,                        # inURL
                properties,                 # inPropertiesToSet
                None                        # inPropertiesToClear
            )

        # The rebuild was successful
        self.changed()


if __name__ == '__main__':
    favourites = Favourites(
        Argument('layout'),
    )
    favourites.invoke()
