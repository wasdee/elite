import hashlib
import os
import shutil

from . import Argument, Action


class File(Action):
    def validate_args(self, path, source, state, mode, owner, group):
        if source and state in ['directory', 'absent']:
            self.fail(
                "the 'source' argument may not be provided when 'state' is "
                "'directory' or 'absent'"
            )

        if state == 'symlink' and not path:
            self.fail("the 'path' argument must be provided when 'state' is 'symlink'")

    def process(self, path, source, state, mode, owner, group):
        if state == 'file':
            if source and not os.path.isfile(source):
                self.fail('the source provided could not be found or is not a file')

            # An existing file was found
            if os.path.isfile(path):
                if source:
                    # The source and destination are identical so no changes are required
                    if self.md5(path) == self.md5(source):
                        self.ok()

                    # Replace the path with the source as it differed
                    try:
                        shutil.copy(source, path)
                    except IOError:
                        self.fail('unable to copy source file to path requested')

                    self.set_file_attributes(path)
                    self.changed('updated the existing path using the source successfully')
                else:
                    self.ok()

            # Clean any existing item in the path requested
            exists = self.remove(path)

            # A source file was provided and must be copied to the path
            if source:
                try:
                    shutil.copy(source, path)
                except IOError:
                    self.fail('unable to copy source file to path requested')

                self.set_file_attributes(path)
                self.changed('copied source to path successfully')
            # A new empty file must be created at the path requesed
            else:
                try:
                    with open(path, 'w'):
                        pass
                except IOError:
                    self.fail('unable to create the file requested')

                self.set_file_attributes(path)
                self.changed('created requested file successfully')

        elif state == 'directory':
            # An existing directory was found
            if os.path.isdir(path):
                self.ok()

            # Clean any existing item in the path requested
            exists = self.remove(path)

            # Create the directory requested
            try:
                os.makedirs(path)
            except IOError:
                if exists:
                    self.fail('existing item removed but a new directory could not be created')
                else:
                    self.fail('the requested directory could not be created')

            self.set_file_attributes(path)

            if exists:
                self.changed('existing item found and replaced with directory successfully')
            else:
                self.changed('directory was created successfully')

        elif state == 'symlink':
            if os.path.islink(path):
                self.ok()

            exists = self.remove(path)

            try:
                os.symlink(source, path)
            except IOError:
                self.fail('the requested symlink could not be created')

            self.set_file_attributes(path)
            self.changed('symlink was created successfully')

        elif state == 'absent':
            exists = self.remove(path)
            if exists:
                self.changed('existing item was removed successfully')
            else:
                self.ok()

    def remove(self, path):
        if not os.path.exists(path) and not os.path.islink(path):
            return False

        if os.path.isdir(path):
            print(path)
            try:
                shutil.rmtree(path)
            except IOError:
                self.fail('existing directory could not be recursively removed')

        elif os.path.isfile(path):
            try:
                os.remove(path)
            except IOError:
                self.fail('existing file could not be removed')

        elif os.path.islink(path):
            try:
                os.remove(path)
            except IOError:
                self.fail('existing symlink could not be removed')

        return True

    def md5(self, path):
        block_size = 1024 * 8
        hash = hashlib.md5()

        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(block_size), b''):
                    hash.update(chunk)
        except IOError:
            self.fail('unable to determine checksum of file')

        return hash.hexdigest()


if __name__ == '__main__':
    file = File(
        Argument('path'),
        Argument('source', optional=True),
        Argument('state', choices=['file', 'directory', 'symlink', 'absent'], default='file'),
        add_file_attribute_args=True
    )
    file.invoke()
