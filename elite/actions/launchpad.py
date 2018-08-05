from . import Action, ActionError
from ..libraries import launchpad


class Launchpad(Action):
    def __init__(self, widget_layout, app_layout, **kwargs):
        self.widget_layout = widget_layout
        self.app_layout = app_layout
        super().__init__(**kwargs)

    def process(self):
        # Determine the location of the SQLite Launchpad database
        launchpad_db_path = launchpad.get_launchpad_db_path()

        # Extract the existing database
        widget_layout_existing, app_layout_existing = launchpad.extract(launchpad_db_path)

        # All pages specified in the provided layout are identical to those present
        if (
            widget_layout_existing[:len(self.widget_layout)] == self.widget_layout and
            app_layout_existing[:len(self.app_layout)] == self.app_layout
        ):
            return self.ok()

        # Rebuild the layouts for Launchpad
        try:
            extra_widgets, extra_apps = launchpad.build(
                self.widget_layout, self.app_layout, launchpad_db_path
            )
        except launchpad.LaunchpadValidationError as e:
            raise ActionError(str(e))

        # The rebuild was successful
        return self.changed(
            extra_widgets=extra_widgets,
            extra_apps=extra_apps
        )
