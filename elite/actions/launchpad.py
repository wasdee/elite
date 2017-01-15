import os

from . import Argument, Action
from ..libraries.launchpad_builder import get_launchpad_db_dir, LaunchpadBuilder


class Launchpad(Action):
    def process(self, widget_layout, app_layout):
        # Determine the location of the SQLite Launchpad database
        launchpad_db_dir = get_launchpad_db_dir()
        launchpad_db_path = os.path.join(launchpad_db_dir, 'db')

        # Extract the existing database
        launchpad_builder = LaunchpadBuilder(launchpad_db_path)
        launchpad_builder.extract()

        # The existing layout is identical to that provided
        if (
            launchpad_builder.widget_layout == widget_layout and
            launchpad_builder.app_layout == app_layout
        ):
            self.ok()

        # Rebuild the layouts for Launchpad
        launchpad_builder = LaunchpadBuilder(launchpad_db_path, widget_layout, app_layout)
        launchpad_builder.build()

        # The rebuild was successful
        self.changed(
            missing_widgets=launchpad_builder.missing_widgets,
            missing_apps=launchpad_builder.missing_apps,
            extra_widgets=launchpad_builder.extra_widgets,
            extra_apps=launchpad_builder.extra_apps
        )


if __name__ == '__main__':
    launchpad = Launchpad(
        Argument('widget_layout'),
        Argument('app_layout')
    )
    launchpad.invoke()
