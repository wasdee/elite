from . import FileAction
from ..libraries import dock


class Dock(FileAction):
    def __init__(self, app_layout, other_layout, **kwargs):
        self.app_layout = app_layout
        self.other_layout = other_layout
        super().__init__(**kwargs)

    def process(self):
        # Determine the location of the Dock plist file
        dock_plist_path = dock.get_dock_plist_path()

        # Extract the existing database
        app_layout_existing, other_layout_existing = dock.extract(dock_plist_path)

        # Normalise the provided config
        app_layout_normalised, other_layout_normalised = dock.normalise(
            self.app_layout, self.other_layout
        )

        # The existing layout is identical to that provided
        if (
            app_layout_existing == app_layout_normalised and
            other_layout_existing == other_layout_normalised
        ):
            changed = self.set_file_attributes(dock_plist_path)
            return self.changed(path=dock_plist_path) if changed else self.ok(path=dock_plist_path)

        # Rebuild the layout of the Dock
        dock.build(
            app_layout_normalised, other_layout_normalised, dock_plist_path,
            perform_normalise=False
        )

        # The rebuild was successful
        self.set_file_attributes(dock_plist_path)
        return self.changed(path=dock_plist_path)
