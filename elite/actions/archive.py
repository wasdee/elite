import os
import shutil
import zipfile

import rarfile

from . import Action, ActionError


class Archive(Action):
    """
    Extracts ZIP and RAR archives to a specified destination.

    :param path: the destination where the archive should be extracted
    :param source: the path of the archive
    :param preserve_mode: preserve the archived mode of all files being extracted
    :param ignore_files: file or directory names to ignore
    :param base_dir: extract from a particular sub-directory as the base
    """

    def __init__(
        self, path, source, preserve_mode=True, ignore_files=None, base_dir=None, **kwargs
    ):
        self.path = path
        self.source = source
        self.preserve_mode = preserve_mode
        self.ignore_files = [] if ignore_files is None else ignore_files
        self.base_dir = base_dir
        super().__init__(**kwargs)

    def process(self):
        # Determine the type of archive provided
        extension = os.path.splitext(self.source)[1]
        archive_type = extension[1:].lower()
        if archive_type not in ['rar', 'zip']:
            raise ActionError('the archive source provided is not a RAR or ZIP file')

        # Create an object of the appropriate type based on the archive type
        try:
            if archive_type == 'zip':
                archive = zipfile.ZipFile(self.source)
            else:
                try:
                    archive = rarfile.RarFile(self.source)
                except rarfile.NeedFirstVolume:
                    raise ActionError(
                        'the archive provided is not the first volume of a multi-part set'
                    )
        except (rarfile.BadRarFile, zipfile.BadZipFile):
            raise ActionError('the contents of the archive provided are not valid')

        changed = False

        # Iterate through all files in the archive
        for filepath in sorted(archive.namelist()):
            # Skip any requested files
            filepath_parts = os.path.normpath(filepath).split(os.sep)
            if set(filepath_parts).intersection(self.ignore_files):
                continue

            # Determine the full output path of the current file
            if self.base_dir:
                if filepath_parts[0] != self.base_dir:
                    continue

                output_filepath = os.path.join(self.path, *filepath_parts[1:])
            else:
                output_filepath = os.path.join(self.path, filepath)

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
                # Verify that the directory we're writing in is present (especially useful
                # for archives where only the files have been added and not the directories)
                output_dirname = os.path.dirname(output_filepath)
                if not os.path.exists(output_dirname):
                    os.makedirs(output_dirname)

                # Extract the file
                with archive.open(filepath) as archive_fp:
                    with open(output_filepath, 'wb') as output_fp:
                        shutil.copyfileobj(archive_fp, output_fp)

                changed = True

            # Set the file mode if required
            if mode and self.preserve_mode:
                os.chmod(output_filepath, mode)

        return self.changed() if changed else self.ok()
