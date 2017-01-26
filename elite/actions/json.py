import json as jsonlib
import os

from ..utils import deep_equal, deep_merge
from . import Argument, Action, FILE_ATTRIBUTE_ARGS


class Json(Action):
    def process(self, path, values, indent, mode, owner, group, flags):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)

        # Load the JSON or create a fresh data structure if it doesn't exist
        try:
            with open(path, 'r') as f:
                json = jsonlib.load(f)
        except OSError:
            json = {}
        except jsonlib.JSONDecodeError:
            self.fail('an invalid JSON file already exists')

        # Check if the current JSON is the same as the values provided
        if deep_equal(values, json):
            self.ok()

        # Update the JSON with the values provided
        deep_merge(values, json)

        # Create the directory to place the JSON file in if required
        json_dir = os.path.dirname(path)
        try:
            if not os.path.exists(json_dir):
                os.makedirs(json_dir)
        except OSError:
            self.fail('unable to create the directory to store the JSON file')

        # Write the updated JSON file
        try:
            with open(path, 'w') as f:
                jsonlib.dump(json, f, indent=indent)

            self.set_file_attributes(path)
            self.changed(path=path)
        except OSError:
            self.fail('unable to update the requested JSON file')


if __name__ == '__main__':
    json = Json(
        Argument('path', optional=True),
        Argument('values'),
        Argument('indent', default=2),
        *FILE_ATTRIBUTE_ARGS
    )
    json.invoke()
