import json as jsonlib
import os

from . import ActionError, FileAction
from ..utils import deep_equal, deep_merge


class JSON(FileAction):
    def __init__(self, path, values, indent=2, **kwargs):
        self.path = path
        self.values = values
        self.indent = indent
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Load the JSON or create a fresh data structure if it doesn't exist
        try:
            with open(path, 'r') as f:
                json = jsonlib.load(f)
        except OSError:
            json = {}
        except jsonlib.JSONDecodeError:
            raise ActionError('an invalid JSON file already exists')

        # Check if the current JSON is the same as the values provided
        if deep_equal(self.values, json):
            changed = self.set_file_attributes(path)
            return self.changed(path=path) if changed else self.ok(path=path)

        # Update the JSON with the values provided
        deep_merge(self.values, json)

        # Write the updated JSON file
        try:
            with open(path, 'w') as f:
                jsonlib.dump(json, f, indent=self.indent)
                # Add a new line at the end of the file
                print(file=f)

            self.set_file_attributes(path)
            return self.changed(path=path)
        except OSError:
            raise ActionError('unable to update the requested JSON file')
