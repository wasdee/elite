#!/usr/bin/env python3
import os
import sqlite3
import subprocess
from collections import defaultdict

from ..utils import batch, generate_uuid


def get_launchpad_db_dir():
    """Determines the user's Launchpad database directory containing the SQLite database."""
    darwin_user_dir = subprocess.check_output(
        ['getconf', 'DARWIN_USER_DIR']
    ).decode('utf-8').rstrip()
    return os.path.join(darwin_user_dir, 'com.apple.dock.launchpad', 'db')


class Types:
    ROOT = 1
    FOLDER_ROOT = 2
    PAGE = 3
    APP = 4
    DOWNLOADING_APP = 5
    WIDGET = 6


class LaunchpadValidationError(Exception):
    """An error that occurs when validating a provided Launchpad layout"""


class LaunchpadBuilder:
    def __init__(self, launchpad_db_path, widget_layout=None, app_layout=None):
        if widget_layout is None:
            widget_layout = []

        if app_layout is None:
            app_layout = []

        # The Launchpad database location
        self.launchpad_db_path = launchpad_db_path

        # Widget and app layouts
        self.widget_layout = widget_layout
        self.app_layout = app_layout

        # Widgets or apps that were not in the layout but found in the db
        self.extra_widgets = []
        self.extra_apps = []

        # Connect to the Launchpad SQLite database
        self.conn = sqlite3.connect(self.launchpad_db_path)

    def _get_title_id_mapping(self, table):
        """
        Obtain a mapping between app titles and their ids.

        :param table: The table to obtain a mapping for (should be apps, widgets or
                      downloading_apps)

        :return: A tuple with two items.  The first value is a dict containing a mapping between
                 the title and (id, uuid, flags) for each item.  The second item contains the
                 maximum id of the items found.
        """
        mapping = {}
        max_id = 0

        for item_id, title, uuid, flags in self.conn.execute(f'''
            SELECT {table}.item_id, {table}.title, items.uuid, items.flags
            FROM {table}
            JOIN items ON items.rowid = {table}.item_id
        '''):
            # Add the item to our mapping
            mapping[title] = (item_id, uuid, flags)

            # Obtain the maximum id in this table
            max_id = max(max_id, item_id)

        return mapping, max_id

    def _validate_layout(self, type_, layout, mapping):
        """
        Validates the provided layout to confirm that all items exist and that folders are
        correctly structured.

        :param type_: The type of item being validated (usually Types.APP or Types.WIDGET)
        :param layout: The layout requested by the user provided as a list (pages) of lists (items)
                       whereby items are strings.  If the item is a folder, then it is to be a dict
                       with a folder_title and folder_items key and associated values.
        :param mapping: The title to data mapping for the respective items being validated.

        :raises: A LaunchpadValidationError is raised with a suitable message if an issue is found
        """
        # Iterate through pages
        for page in layout:
            # Iterate through items
            for item in page:
                # A folder has been encountered
                if isinstance(item, dict):
                    # Verify that folder information was provided correctly
                    if 'folder_title' not in item or 'folder_layout' not in item:
                        raise LaunchpadValidationError(
                            'each folder layout must contain a folder_title and folder_layout'
                        )

                    folder_layout = item['folder_layout']

                    # Iterate through folder pages
                    for folder_page in folder_layout:

                        # Iterate through folder items
                        for title in folder_page:

                            # Verify that the widget or app requested exists
                            if title not in mapping:
                                if type_ == Types.WIDGET:
                                    raise LaunchpadValidationError(
                                        f"the widget '{title}' does not exist"
                                    )
                                elif type_ == Types.APP:
                                    raise LaunchpadValidationError(
                                        f"the app '{title}' does not exist"
                                    )
                # Flat items
                else:
                    title = item

                    # Verify that the widget or app requested exists
                    if title not in mapping:
                        if type_ == Types.WIDGET:
                            raise LaunchpadValidationError(
                                f"the widget '{title}' does not exist"
                            )
                        elif type_ == Types.APP:
                            raise LaunchpadValidationError(
                                f"the app '{title}' does not exist"
                            )

    def _add_extra_items(self, layout, mapping):
        """
        Adds additional pages to the layout containing all items that the user forgot to specify
        in the provided layout.

        :param layout: The layout of items.
        :param mapping: The mapping of the respective items (as obtained by get_mapping).
        """
        items_in_layout = []

        # Iterate through each page of the layout and obtain a list of items contained
        for page in layout:
            # Items on a page
            for item in page:
                # Folders
                if isinstance(item, dict):
                    folder_layout = item['folder_layout']

                    for folder_page in folder_layout:
                        for title in folder_page:
                            items_in_layout.append(title)

                # Regular items
                else:
                    title = item
                    items_in_layout.append(title)

        # Determine which items are extra items are present compared to the layout provided
        extra_items = list(set(mapping.keys()).difference(items_in_layout))

        # If extra items are found, add them to the layout
        if extra_items:
            for extra_items_batch in batch(extra_items, 30):
                layout.append(extra_items_batch)

        return extra_items

    def _setup_items(self, type_, layout, mapping, group_id, root_parent_id):
        """
        Manipulates the appropriate database table to layout the items as requested by the user.

        :param type_: The type of item being manipulated (usually Types.APP or Types.WIDGET)
        :param layout: The layout requested by the user provided as a list (pages) of lists (items)
                       whereby items are strings.  If the item is a folder, then it is to be a dict
                       with a folder_title and folder_items key and associated values.
        :param mapping: The title to data mapping for the respective items being setup.
        :param group_id: The group id to continue from when adding groups.
        :param root_parent_id: The root parent id to add child items to.

        :return: The resultant group id after additions to continue working from.
        """
        cursor = self.conn.cursor()

        # Iterate through pages
        for page_ordering, page in enumerate(layout):

            # Start a new page (note that the ordering starts at 1 instead of 0 as there is a
            # holding page at an ordering of 0)
            group_id += 1

            cursor.execute('''
                INSERT INTO items (rowid, uuid, flags, type, parent_id, ordering)
                VALUES (?, ?, 2, ?, ?, ?)
            ''', (group_id, generate_uuid(), Types.PAGE, root_parent_id, page_ordering + 1)
            )

            cursor.execute('''
                INSERT INTO groups (item_id, category_id, title)
                VALUES (?, NULL, NULL)
            ''', (group_id,)
            )
            self.conn.commit()

            # Capture the group id of the page to be used for child items
            page_parent_id = group_id

            # Iterate through items
            item_ordering = 0
            for item in page:
                # A folder has been encountered
                if isinstance(item, dict):
                    folder_title = item['folder_title']
                    folder_layout = item['folder_layout']

                    # Start a new folder
                    group_id += 1

                    cursor.execute('''
                        INSERT INTO items (rowid, uuid, flags, type, parent_id, ordering)
                        VALUES (?, ?, 0, ?, ?, ?)
                    ''', (
                        group_id, generate_uuid(), Types.FOLDER_ROOT, page_parent_id,
                        item_ordering)
                    )

                    cursor.execute('''
                        INSERT INTO groups (item_id, category_id, title)
                        VALUES (?, NULL, ?)
                    ''', (group_id, folder_title)
                    )
                    self.conn.commit()

                    item_ordering += 1

                    # Capture the group id of the folder root to be used for child items
                    folder_root_parent_id = group_id

                    # Iterate through folder pages
                    for folder_page_ordering, folder_page in enumerate(folder_layout):
                        # Start a new folder page
                        group_id += 1

                        cursor.execute('''
                            INSERT INTO items (rowid, uuid, flags, type, parent_id, ordering)
                            VALUES (?, ?, 2, ?, ?, ?)
                        ''', (
                            group_id, generate_uuid(), Types.PAGE, folder_root_parent_id,
                            folder_page_ordering)
                        )

                        cursor.execute('''
                            INSERT INTO groups (item_id, category_id, title)
                            VALUES (?, NULL, NULL)
                        ''', (group_id,)
                        )
                        self.conn.commit()

                        # Iterate through folder items
                        folder_item_ordering = 0
                        for title in folder_page:
                            item_id, uuid, flags = mapping[title]
                            cursor.execute('''
                                UPDATE items
                                SET uuid = ?, flags = ?, type = ?, parent_id = ?, ordering = ?
                                WHERE rowid = ?
                            ''', (uuid, flags, type_, group_id, folder_item_ordering, item_id)
                            )
                            self.conn.commit()

                            folder_item_ordering += 1

                # Flat items
                else:
                    title = item
                    item_id, uuid, flags = mapping[title]
                    cursor.execute('''
                        UPDATE items
                        SET uuid = ?, flags = ?, type = ?, parent_id = ?, ordering = ?
                        WHERE rowid = ?
                    ''', (uuid, flags, type_, page_parent_id, item_ordering, item_id)
                    )
                    self.conn.commit()

                    item_ordering += 1

        return group_id

    def build(self):
        """
        Builds the requested layout for both the Launchpad apps and Dashboard widgets by updating
        the user's Launchpad SQlite database.
        """
        # Obtain app and widget mappings
        widget_mapping, widget_max_id = self._get_title_id_mapping('widgets')
        app_mapping, app_max_id = self._get_title_id_mapping('apps')

        # Validate widget layout
        self._validate_layout(Types.WIDGET, self.widget_layout, widget_mapping)

        # Validate app layout
        self._validate_layout(Types.APP, self.app_layout, app_mapping)

        # We will begin our group records using the max ids found (groups always appear after
        # apps and widgets)
        group_id = max(app_max_id, widget_max_id)

        # Add any extra widgets not found in the user's layout to the end of the layout
        self.extra_widgets = self._add_extra_items(self.widget_layout, widget_mapping)

        # Add any extra apps not found in the user's layout to the end of the layout
        self.extra_apps = self._add_extra_items(self.app_layout, app_mapping)

        # Grab a cursor for our operations
        cursor = self.conn.cursor()

        # Clear all items related to groups so we can re-create them
        cursor.execute('''
            DELETE FROM items
            WHERE type IN (?, ?, ?)
        ''', (Types.ROOT, Types.FOLDER_ROOT, Types.PAGE))
        self.conn.commit()

        # Disable triggers on the items table temporarily so that we may create the rows with our
        # required ordering (including items which have an ordering of 0)
        cursor.execute('''
            UPDATE dbinfo
            SET value = 1
            WHERE key = 'ignore_items_update_triggers'
        ''')
        self.conn.commit()

        # Add root and holding pages to items and groups
        for rowid, uuid, type_, parent_id in [
            # Root for Launchpad apps
            (1, 'ROOTPAGE', Types.ROOT, 0),
            (2, 'HOLDINGPAGE', Types.PAGE, 1),

            # Root for dashboard widgets
            (3, 'ROOTPAGE_DB', Types.ROOT, 0),
            (4, 'HOLDINGPAGE_DB', Types.PAGE, 3),

            # Root for Launchpad version
            (5, 'ROOTPAGE_VERS', Types.ROOT, 0),
            (6, 'HOLDINGPAGE_VERS', Types.PAGE, 5)
        ]:
            cursor.execute('''
                INSERT INTO items (rowid, uuid, flags, type, parent_id, ordering)
                VALUES (?, ?, NULL, ?, ?, 0)
            ''', (rowid, uuid, type_, parent_id))

            cursor.execute('''
                INSERT INTO groups (item_id, category_id, title)
                VALUES (?, NULL, NULL)
            ''', (rowid,))

            self.conn.commit()

        # Setup the widgets
        group_id = self._setup_items(
            Types.WIDGET, self.widget_layout, widget_mapping, group_id, root_parent_id=3
        )

        # Setup the apps
        group_id = self._setup_items(
            Types.APP, self.app_layout, app_mapping, group_id, root_parent_id=1
        )

        # Enable triggers on the items again so ordering is auto-generated
        cursor.execute('''
            UPDATE dbinfo
            SET value = 0
            WHERE key = 'ignore_items_update_triggers'
        ''')
        self.conn.commit()

    def _build_layout(self, root, parent_mapping):
        """
        Builds a data structure containing the layout for a particular type of data.

        :param root: The root id of the tree being built.
        :param parent_mapping: The mapping between parent_ids and items.

        :returns: The layout data structure that was built as a tuple where the first item is the
                  widget layout and the second item is the app layout.
        """
        layout = []

        # Iterate through pages
        for page_id, _, _, _, _ in parent_mapping[root]:
            page_items = []

            # Iterate through items
            for row_id, type_, app_title, widget_title, group_title in parent_mapping[page_id]:
                # An app has been encountered which is added to the page
                if type_ == Types.APP:
                    page_items.append(app_title)

                # A widget has been encountered which is added to the page
                elif type_ == Types.WIDGET:
                    page_items.append(widget_title)

                # A folder has been encountered
                elif type_ == Types.FOLDER_ROOT:
                    # Start a dict for the folder with its title and layout
                    folder = {
                        'folder_title': group_title,
                        'folder_layout': []
                    }

                    # Iterate through folder pages
                    for folder_page_id, _, _, _, _ in parent_mapping[row_id]:
                        folder_page_items = []

                        # Iterate through folder items
                        for (
                            _, folder_item_type, folder_item_app_title, folder_widget_title, _
                        ) in parent_mapping[folder_page_id]:

                            # An app has been encountered which is being added to the folder page
                            if folder_item_type == Types.APP:
                                folder_page_items.append(folder_item_app_title)

                            # A widget has been encountered which is being added to the folder page
                            elif folder_item_type == Types.WIDGET:
                                folder_page_items.append(folder_widget_title)

                        # Add the page to the folder
                        folder['folder_layout'].append(folder_page_items)

                    # Add the folder item to the page
                    page_items.append(folder)

            # Add the page to the layout
            layout.append(page_items)

        return layout

    def extract(self):
        # Reset extra widgets and apps as we are reading a config that won't have such items
        self.extra_widgets = []
        self.extra_apps = []

        # Iterate through root elements for Launchpad apps and Dashboard widgets
        for key, value in self.conn.execute('''
            SELECT key, value
            FROM dbinfo
            WHERE key IN ('launchpad_root', 'dashboard_root');
        '''):
            if key == 'launchpad_root':
                launchpad_root = int(value)
            elif key == 'dashboard_root':
                dashboard_root = int(value)

        # Build a mapping between the parent_id and the associated items
        parent_mapping = defaultdict(list)

        # Obtain all items and their associated titles
        for row_id, parent_id, type_, app_title, widget_title, group_title in self.conn.execute('''
            SELECT items.rowid, items.parent_id, items.type,
                   apps.title AS app_title,
                   widgets.title AS widget_title,
                   groups.title AS group_title
            FROM items
            LEFT JOIN apps ON apps.item_id = items.rowid
            LEFT JOIN widgets ON widgets.item_id = items.rowid
            LEFT JOIN groups ON groups.item_id = items.rowid
            WHERE items.uuid NOT IN ('ROOTPAGE', 'HOLDINGPAGE',
                                     'ROOTPAGE_DB', 'HOLDINGPAGE_DB',
                                     'ROOTPAGE_VERS', 'HOLDINGPAGE_VERS')
            ORDER BY items.parent_id, items.ordering
        '''):
            parent_mapping[parent_id].append((row_id, type_, app_title, widget_title, group_title))

        self.widget_layout = self._build_layout(dashboard_root, parent_mapping)
        self.app_layout = self._build_layout(launchpad_root, parent_mapping)

        return (self.widget_layout, self.app_layout)
