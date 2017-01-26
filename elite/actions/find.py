from fnmatch import fnmatch
import os

from . import Argument, Action


class Find(Action):
    def process(self, path, min_depth, max_depth, types, patterns, aliases):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)

        # Check that the path exists
        if not os.path.isdir(path):
            self.fail('unable to find a directory with the path provided')

        # Find all the paths with the filters provided and return them to the user
        paths = self.walk(
            path, path.count(os.sep), min_depth, max_depth, types, patterns, aliases
        )
        self.ok(paths=paths)

    def walk(
        self, path, root_depth, min_depth=None, max_depth=None, types=None, patterns=None,
        aliases=True
    ):
        # Only import PyObjC libraries if necessary (as they take time)
        if aliases:
            from Foundation import NSURL, NSURLIsAliasFileKey

        # Create a list to store all the files found
        paths = []

        # Walk through the base path provided using scandir (for speed)
        for item in os.scandir(path):
            # Determine the current depth
            depth = item.path.count(os.sep) - root_depth

            # Impose a maximum depth
            if max_depth and depth > max_depth:
                continue

            # Determine the file type if a type filter is requested
            if types:
                if item.is_dir():
                    file_type = 'directory'
                elif item.is_symlink():
                    file_type = 'symlink'
                elif aliases:
                    # Determine if the file is an alias
                    url = NSURL.fileURLWithPath_(item.path)
                    ok, is_alias, error = url.getResourceValue_forKey_error_(
                        None, NSURLIsAliasFileKey, None
                    )
                    file_type = 'alias' if ok and is_alias else 'file'
                else:
                    file_type = 'file'

            # Determine if the current item should be added to our paths list based on filters
            if (
                (not min_depth or depth >= min_depth) and
                (not types or file_type in types) and
                (not patterns or any(fnmatch(item.path, p) for p in patterns))
            ):
                paths.append(item.path)

            # Recurse through directories
            if item.is_dir() and not item.is_symlink():
                paths.extend(self.walk(
                    item.path, root_depth, min_depth, max_depth, types, patterns, aliases
                ))

        return paths


if __name__ == '__main__':
    find = Find(
        Argument('path'),
        Argument('min_depth', optional=True),
        Argument('max_depth', optional=True),
        Argument('types', optional=True),
        Argument('patterns', optional=True),
        Argument('aliases', default=True)
    )
    find.invoke()
