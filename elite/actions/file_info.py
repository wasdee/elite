import os

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
            elif os.path.isdir(path):
                file_type = 'directory'
            else:
                file_type = 'file'

            # Determine if the path is a mountpoint
            mount = os.path.ismount(path)
        else:
            exists = False
            file_type = None
            mount = None

        self.ok(exists=exists, file_type=file_type, mount=mount)


if __name__ == '__main__':
    file_info = FileInfo(
        Argument('path')
    )
    file_info.invoke()
