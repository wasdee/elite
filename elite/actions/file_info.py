import os

from . import Argument, Action
from ..constants import FLAGS


class FileInfo(Action):
    def process(self, path, aliases):
        # Only import PyObjC libraries if necessary (as they take time)
        if aliases:
            from Foundation import NSURL, NSURLBookmarkResolutionWithoutUI

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
            elif aliases:
                # Determine if the file is an alias
                alias_url = NSURL.fileURLWithPath_(path)
                bookmark_data, error = NSURL.bookmarkDataWithContentsOfURL_error_(
                    alias_url, None
                )

                if bookmark_data:
                    file_type = 'alias'
                    source_url, is_stale, error = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # flake8: noqa
                        bookmark_data, NSURLBookmarkResolutionWithoutUI, None, None, None
                    )
                    source = source_url.path()
                else:
                    file_type = 'file'
                    source = None
            else:
                file_type = 'file'
                source = None

            # Determine if the path is a mountpoint
            mount = os.path.ismount(path)

            # Determine what flags are set on the file
            stat = os.stat(path)
            flags_bin = stat.st_flags
            flags = [flag for flag, flag_bin in FLAGS.items() if flags_bin & flag_bin]
        else:
            exists = False
            file_type = None
            source = None
            mount = None
            flags = None

        self.ok(exists=exists, file_type=file_type, source=source, mount=mount, flags=flags)


if __name__ == '__main__':
    file_info = FileInfo(
        Argument('path'),
        Argument('aliases', default=True)
    )
    file_info.invoke()
