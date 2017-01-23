from . import Argument, Action
from ..libraries.dock_builder import get_dock_plist_path, DockBuilder


class Dock(Action):
    def process(self, app_layout, other_layout):
        # Determine the location of the Dock plist file
        dock_db_path = get_dock_plist_path()

        # Extract the existing database
        dock_builder = DockBuilder(dock_db_path)
        dock_builder.extract()

        # Normalise the provided config
        dock_builder_config = DockBuilder(dock_db_path, app_layout, other_layout)

        # The existing layout is identical to that provided
        if (
            dock_builder.app_layout == dock_builder_config.app_layout and
            dock_builder.other_layout == dock_builder_config.other_layout
        ):
            self.ok()

        # Rebuild the layout of the Dock
        dock_builder = DockBuilder(dock_db_path, app_layout, other_layout)
        dock_builder.build()

        # The rebuild was successful
        self.changed()


if __name__ == '__main__':
    dock = Dock(
        Argument('app_layout'),
        Argument('other_layout')
    )
    dock.invoke()
