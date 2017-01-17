import os

from CoreFoundation import NSURL
from Foundation import NSURLBookmarkResolutionWithoutUI
import objc

from . import Argument, Action


class FileInfo(Action):
    def process(self, path):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)

        # Check if the filepath exists
        if os.path.exists(path):
            exists = True

            # Determine the type of file found
            if os.path.islink(path):
                file_type = 'symlink'
                source = os.readlink(path)
            elif os.path.isdir(path):
                file_type = 'directory'
                source = None
            else:
                # Determine if the file is an alias
                alias_url = NSURL.fileURLWithPath_(path)
                bookmark_data, error = NSURL.bookmarkDataWithContentsOfURL_error_(
                    alias_url, objc.nil
                )

                if bookmark_data:
                    file_type = 'alias'
                    source_url, is_stale, error = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # flake8: noqa
                        bookmark_data, NSURLBookmarkResolutionWithoutUI, None, objc.nil, objc.nil
                    )
                    source = source_url.path()
                else:
                    file_type = 'file'

            # Determine if the path is a mountpoint
            mount = os.path.ismount(path)
        else:
            exists = False
            file_type = None
            mount = None
            source = None

        self.ok(exists=exists, file_type=file_type, source=source, mount=mount)


if __name__ == '__main__':
    file_info = FileInfo(
        Argument('path')
    )
    file_info.invoke()
