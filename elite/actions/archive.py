import os
import zipfile

import rarfile

from . import Action, Argument


class Archive(Action):
    def process(self, path, source, preserve_mode, ignore_files, base_dir):
        # Determine the type of archive provided
        extension = os.path.splitext(source)[1]
        archive_type = extension[1:].lower()
        if archive_type not in ['rar', 'zip']:
            self.fail('the archive source provided is not a RAR or ZIP file')

        # Create an object of the appropriate type based on the archive type
        if archive_type == 'zip':
            archive = zipfile.ZipFile(source)
        else:
            try:
                archive = rarfile.RarFile(source)
            except rarfile.NeedFirstVolume:
                self.fail('the archive provided is not the first volume of a multi-part set')

        changed = False

        # Iterate through all files in the archive
        for filepath in sorted(archive.namelist()):
            # Skip any requested files
            filepath_parts = os.path.normpath(filepath).split(os.sep)
            if set(filepath_parts).intersection(ignore_files):
                continue

            # Determine the full output path of the current file
            if base_dir:
                if filepath_parts[0] != base_dir:
                    continue

                output_filepath = os.path.join(path, *filepath_parts[1:])
            else:
                output_filepath = os.path.join(path, filepath)

            # Obtain useful information about the file
            info = archive.getinfo(filepath)
            mode = info.external_attr >> 16 if archive_type == 'zip' else info.mode
            is_dir = info.is_dir() if archive_type == 'zip' else info.isdir()

            # If the file has already been extracted, determine its size (for potential comparison)
            try:
                output_file_size = os.path.getsize(output_filepath)
            except FileNotFoundError:
                output_file_size = -1

            # A directory has been encountered
            if is_dir:
                try:
                    os.makedirs(output_filepath)
                    changed = True
                except FileExistsError:
                    pass

            # A file has been encountered which is the same size as a previously extracted file
            elif info.file_size == output_file_size:
                pass

            # A file has been encountered
            else:
                # Set the block size to an optimal value (based on performance testing)
                block_size = 131_072

                # Verify that the directory we're writing in is present (especially useful
                # for ZIP archives)
                output_dirname = os.path.dirname(output_filepath)
                if not os.path.exists(output_dirname):
                    os.makedirs(output_dirname)

                # Extract the file
                with archive.open(filepath) as a:
                    with open(output_filepath, 'wb') as f:
                        for block in iter(lambda: a.read(block_size), b''):
                            f.write(block)

                changed = True

            # Set the file mode if required
            if mode and preserve_mode:
                os.chmod(output_filepath, mode)

        self.changed(path=path) if changed else self.ok()


if __name__ == '__main__':
    archive = Archive(
        Argument('path'),
        Argument('source'),
        Argument('preserve_mode', default=True),
        Argument('ignore_files', default=[]),
        Argument('base_dir', optional=True)
    )
    archive.invoke()
