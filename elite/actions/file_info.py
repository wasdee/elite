import os

from Foundation import (  # pylint: disable=no-name-in-module
    NSURL, NSURLBookmarkResolutionWithoutUI
)

from . import Action
from ..constants import FLAGS


class FileInfo(Action):
    """
    Obtains details about a specified file and returns it as data to the caller.

    :param path: the path of the file to obtain information about
    :param source: the source file that should be copied or linked
    :param aliases: whether to process macOS aliases
    """

    def __init__(self, path, aliases=True, **kwargs):
        self.path = path
        self.aliases = aliases
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Check if the filepath exists
        if os.path.exists(path) or os.path.islink(path):
            exists = os.path.exists(path)

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
                bookmark_data, _error = NSURL.bookmarkDataWithContentsOfURL_error_(alias_url, None)

                if bookmark_data:
                    file_type = 'alias'
                    source_url, _is_stale, _error = (
                        # pylint: disable=line-too-long
                        NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # noqa: E501
                            bookmark_data, NSURLBookmarkResolutionWithoutUI, None, None, None
                        )
                        # pylint: enable=line-too-long
                    )
                    source = source_url.path() if source_url else None
                else:
                    file_type = 'file'
                    source = None
            else:
                file_type = 'file'
                source = None

            # Determine if the path is a mountpoint
            mount = os.path.ismount(path)

            # Determine what flags are set on the file
            stat = os.stat(path, follow_symlinks=False)
            flags_bin = stat.st_flags
            flags = [flag for flag, flag_bin in FLAGS.items() if flags_bin & flag_bin]
        else:
            exists = False
            file_type = None
            source = None
            mount = None
            flags = None

        return self.ok(exists=exists, file_type=file_type, source=source, mount=mount, flags=flags)
