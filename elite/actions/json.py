import json as jsonlib
import os

from . import ActionError, FileAction
from ..utils import deep_equal, deep_merge


class JSON(FileAction):
    """
    Provides the ability to manipulate JSON configuration files.

    :param path: the full path of the JSON file to manipulate
    :param values: a dictionary containing the data to be incorporated into the config
    :param indent: the indentation level of the written JSON file
    """

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
            with open(path, 'r') as fp:
                json = jsonlib.load(fp)
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
            with open(path, 'w') as fp:
                jsonlib.dump(json, fp, indent=self.indent)
                # Add a new line at the end of the file
                print(file=fp)

            self.set_file_attributes(path)
            return self.changed(path=path)
        except OSError:
            raise ActionError('unable to update the requested JSON file')
