import os

from . import Action, ActionError
from ..libraries.launchpad_builder import (
    LaunchpadBuilder, LaunchpadValidationError, get_launchpad_db_dir
)


class Launchpad(Action):
    __action_name__ = 'launchpad'

    def __init__(self, widget_layout, app_layout, **kwargs):
        self.widget_layout = widget_layout
        self.app_layout = app_layout
        super().__init__(**kwargs)

    def process(self):
        # Determine the location of the SQLite Launchpad database
        launchpad_db_dir = get_launchpad_db_dir()
        launchpad_db_path = os.path.join(launchpad_db_dir, 'db')

        # Extract the existing database
        launchpad_builder = LaunchpadBuilder(launchpad_db_path)
        launchpad_builder.extract()

        # All pages specified in the provided layout are identical to those present
        if (
            launchpad_builder.widget_layout[:len(self.widget_layout)] == self.widget_layout and
            launchpad_builder.app_layout[:len(self.app_layout)] == self.app_layout
        ):
            return self.ok()

        # Rebuild the layouts for Launchpad
        launchpad_builder = LaunchpadBuilder(launchpad_db_path, self.widget_layout, self.app_layout)

        try:
            launchpad_builder.build()
        except LaunchpadValidationError as e:
            raise ActionError(str(e))

        # The rebuild was successful
        return self.changed(
            extra_widgets=launchpad_builder.extra_widgets,
            extra_apps=launchpad_builder.extra_apps
        )
