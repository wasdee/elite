import os

from . import Argument, Action
from ..libraries.launchpad_builder import (
    get_launchpad_db_dir, LaunchpadBuilder, LaunchpadValidationError
)


class Launchpad(Action):
    def process(self, widget_layout, app_layout):
        # Determine the location of the SQLite Launchpad database
        launchpad_db_dir = get_launchpad_db_dir()
        launchpad_db_path = os.path.join(launchpad_db_dir, 'db')

        # Extract the existing database
        launchpad_builder = LaunchpadBuilder(launchpad_db_path)
        launchpad_builder.extract()

        # All pages specified in the provided layout are identical to those present
        if (
            launchpad_builder.widget_layout[:len(widget_layout)] == widget_layout and
            launchpad_builder.app_layout[:len(app_layout)] == app_layout
        ):
            self.ok()

        # Rebuild the layouts for Launchpad
        launchpad_builder = LaunchpadBuilder(launchpad_db_path, widget_layout, app_layout)

        try:
            launchpad_builder.build()
        except LaunchpadValidationError as e:
            self.fail(str(e))

        # The rebuild was successful
        self.changed(
            extra_widgets=launchpad_builder.extra_widgets,
            extra_apps=launchpad_builder.extra_apps
        )


if __name__ == '__main__':
    launchpad = Launchpad(
        Argument('widget_layout'),
        Argument('app_layout')
    )
    launchpad.invoke()
