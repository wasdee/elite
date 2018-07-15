import os

from . import Action
from ..constants import FLAGS


class FileInfo(Action):
    __action_name__ = 'file_info'

    def __init__(self, path, aliases=True):
        self.path = path
        self.aliases = aliases

    def process(self):
        # Only import PyObjC libraries if necessary (as they take time)
        if self.aliases:
            # pylint: disable=no-name-in-module
            from Foundation import NSURL, NSURLBookmarkResolutionWithoutUI

        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

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
            elif self.aliases:
                # Determine if the file is an alias
                alias_url = NSURL.fileURLWithPath_(path)
                bookmark_data, _error = NSURL.bookmarkDataWithContentsOfURL_error_(
                    alias_url, None
                )

                if bookmark_data:
                    file_type = 'alias'
                    source_url, _is_stale, _error = (
                        # pylint: disable=line-too-long
                        NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # noqa: E501
                            bookmark_data, NSURLBookmarkResolutionWithoutUI, None, None, None
                        )
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

        return self.ok(exists=exists, file_type=file_type, source=source, mount=mount, flags=flags)
