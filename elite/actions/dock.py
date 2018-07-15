from . import FileAction
from ..libraries.dock_builder import DockBuilder, get_dock_plist_path


class Dock(FileAction):
    __action_name__ = 'dock'

    def __init__(self, app_layout, other_layout, **kwargs):
        self.app_layout = app_layout
        self.other_layout = other_layout
        super().__init__(**kwargs)

    def process(self):
        # Determine the location of the Dock plist file
        dock_db_path = get_dock_plist_path()

        # Extract the existing database
        dock_builder = DockBuilder(dock_db_path)
        dock_builder.extract()

        # Normalise the provided config
        dock_builder_config = DockBuilder(dock_db_path, self.app_layout, self.other_layout)

        # The existing layout is identical to that provided
        if (
            dock_builder.app_layout == dock_builder_config.app_layout and
            dock_builder.other_layout == dock_builder_config.other_layout
        ):
            changed = self.set_file_attributes(dock_db_path)
            return self.changed(path=dock_db_path) if changed else self.ok()

        # Rebuild the layout of the Dock
        dock_builder = DockBuilder(dock_db_path, self.app_layout, self.other_layout)
        dock_builder.build()

        # The rebuild was successful
        self.set_file_attributes(dock_db_path)
        return self.changed(path=dock_db_path)
