import hashlib
import os
import shutil

from . import ActionError, FileAction


class File(FileAction):
    __action_name__ = 'file'

    def __init__(self, path, source=None, state='file', **kwargs):
        self._source = source
        self._state = state
        self.path = path
        self.source = source
        self.state = state
        super().__init__(**kwargs)

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        if source and self.state == 'absent':
            raise ValueError("the 'source' argument may not be provided when 'state' is 'absent'")
        if not source and self.state == 'symlink':
            raise ValueError("the 'source' argument must be provided when 'state' is 'symlink'")
        self._source = source

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['file', 'directory', 'alias', 'symlink', 'absent']:
            raise ValueError('state must be file, directory, alias, symlink or absent')
        if self.source and state == 'absent':
            raise ValueError("the 'source' argument may not be provided when 'state' is 'absent'")
        if not self.source and state == 'symlink':
            raise ValueError("the 'source' argument must be provided when 'state' is 'symlink'")
        self._state = state

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)
        source = os.path.expanduser(self.source) if self.source else None

        if self.state == 'file':
            if source:
                # The source provided does not exist or is not a file
                if not os.path.isfile(source):
                    raise ActionError('the source provided could not be found or is not a file')

                # If the destination provided is a path, then we place the file in it
                if os.path.isdir(path):
                    path = os.path.join(path, os.path.basename(source))

                # An existing file at the destination path was found so we compare them
                # and avoid making changes if they're identical
                exists = os.path.isfile(path)
                if exists and self.md5(source) == self.md5(path):
                    changed = self.set_file_attributes(path)
                    return self.changed(path=path) if changed else self.ok(path=path)

                # Copy the source to the destination
                self.copy(source, path)

                self.set_file_attributes(path)
                return self.changed(path=path)
            else:
                # An existing file at the destination path was found
                if os.path.isfile(path):
                    changed = self.set_file_attributes(path)
                    return self.changed(path=path) if changed else self.ok(path=path)

                # Create an empty file at the destination path
                self.create_empty(path)

                self.set_file_attributes(path)
                return self.changed(path=path)

        elif self.state == 'directory':
            if source:
                raise ActionError(
                    "the file action doesn't support copyng one directory to another, use the "
                    'rsync action instead'
                )
            else:
                # An existing directory was found
                if os.path.isdir(path):
                    changed = self.set_file_attributes(path)
                    return self.changed(path=path) if changed else self.ok(path=path)

                # Clean any existing item in the path requested
                self.remove(path)

                # Create the directory requested
                try:
                    os.mkdir(path)
                except OSError:
                    raise ActionError('the requested directory could not be created')

                self.set_file_attributes(path)
                return self.changed(path=path)

        elif self.state == 'alias':
            # Only import PyObjC libraries if necessary (as they take time)
            # pylint: disable=no-name-in-module
            from Foundation import (
                NSURL, NSURLBookmarkCreationSuitableForBookmarkFile,
                NSURLBookmarkResolutionWithoutUI
            )

            # If the destination provided is a path, then we place the file in it
            if os.path.isdir(path):
                path = os.path.join(path, os.path.basename(source))

            # When creating an alias, the source must be an absolute path and exist
            source = os.path.abspath(source)
            if not os.path.exists(source):
                raise ActionError('the source file provided does not exist')

            # An existing alias at the destination path was found so we compare them
            # and avoid making changes if they're identical
            exists = os.path.isfile(path)
            path_url = NSURL.fileURLWithPath_(path)

            if exists:
                bookmark_data, _error = NSURL.bookmarkDataWithContentsOfURL_error_(path_url, None)

                if bookmark_data:
                    source_url, _is_stale, _error = (
                        # pylint: disable=line-too-long
                        NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # noqa: E501
                            bookmark_data, NSURLBookmarkResolutionWithoutUI, None, None, None
                        )
                    )
                    if source_url.path() == source:
                        changed = self.set_file_attributes(path)
                        return self.changed(path=path) if changed else self.ok(path=path)

            # Delete any existing file or symlink at the path
            self.remove(path)

            # Create an NSURL object for the source (absolute paths must be used for aliases)
            source_url = NSURL.fileURLWithPath_(source)

            # Build the bookmark for the alias
            bookmark_data, _error = (
                # pylint: disable=line-too-long
                source_url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(  # noqa: E501
                    NSURLBookmarkCreationSuitableForBookmarkFile, None, None, None
                )
            )

            # Write the alias using the bookmark data
            if bookmark_data:
                _success, _error = NSURL.writeBookmarkData_toURL_options_error_(
                    bookmark_data, path_url, NSURLBookmarkCreationSuitableForBookmarkFile, None
                )
            else:
                raise ActionError('unable to create alias')

            self.set_file_attributes(path)
            return self.changed(path=path)

        elif self.state == 'symlink':
            # If the destination provided is a path, then we place the file in it
            if os.path.isdir(path) and not os.path.islink(path):
                path = os.path.join(path, os.path.basename(source))

            # An existing symlink at the destination path was found so we compare them
            # and avoid making changes if they're identical
            exists = os.path.islink(path)
            if exists and os.readlink(path) == source:
                changed = self.set_file_attributes(path)
                return self.changed(path=path) if changed else self.ok(path=path)

            # Delete any existing file or symlink at the path
            self.remove(path)

            # Create the symlink requested
            try:
                os.symlink(source, path)
            except OSError:
                raise ActionError('the requested symlink could not be created')

            self.set_file_attributes(path)
            return self.changed(path=path)

        else:  # 'absent'
            removed = self.remove(path)
            return self.changed(path=path) if removed else self.ok(path=path)

    def copy(self, source, path, buffer_size=1024 * 8):
        try:
            with open(source, 'rb') as fsource:
                with open(path, 'wb') as fpath:
                    for buffer in iter(lambda: fsource.read(buffer_size), b''):
                        fpath.write(buffer)
        except OSError:
            raise ActionError('unable to copy source file to path requested')

    def create_empty(self, path):
        try:
            with open(path, 'w'):
                pass
        except IsADirectoryError:
            raise ActionError('the destination path is a directory')
        except OSError:
            raise ActionError('unable to create an empty file at the path requested')

    def remove(self, path):
        if not os.path.exists(path) and not os.path.islink(path):
            return False

        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                raise ActionError('existing file could not be removed')

        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except OSError:
                raise ActionError('existing directory could not be recursively removed')

        elif os.path.islink(path):
            try:
                os.remove(path)
            except OSError:
                raise ActionError('existing symlink could not be removed')

        return True

    def md5(self, path, block_size=1024 * 8):
        hash_md5 = hashlib.md5()

        try:
            with open(path, 'rb') as f:
                for buffer in iter(lambda: f.read(block_size), b''):
                    hash_md5.update(buffer)
        except OSError:
            raise ActionError('unable to determine checksum of file')

        return hash_md5.hexdigest()
