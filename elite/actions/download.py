import cgi
import os
import urllib.error
import urllib.parse
import urllib.request

from . import ActionError, FileAction


class Download(FileAction):
    def __init__(self, url, path, **kwargs):
        self.url = url
        self.path = path
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Download the requested URL to the destination path
        try:
            with urllib.request.urlopen(self.url) as r:
                # Determine if the user has provided a full filepath to download to
                if not os.path.isdir(path) and not path.endswith(os.sep):
                    filepath = path
                else:
                    # Use the download headers to determine the download filename
                    filename = None
                    if 'Content-Disposition' in r.headers:
                        content_type, options = cgi.parse_header(r.headers['Content-Disposition'])
                        if content_type == 'attachment' and 'filename' in options:
                            filename = options['filename']

                    # Use the URL to determine the download filename
                    if not filename:
                        url_path = urllib.parse.urlparse(r.url).path
                        filename = os.path.basename(url_path)

                    # No filename could be determined
                    if not filename:
                        raise ActionError('unable to determine the filename of the download')

                    # Build the full filepath using the path given and filename determined
                    filepath = os.path.join(path, filename)

                    # Check if the file already exists in the destination path
                    if os.path.exists(filepath):
                        changed = self.set_file_attributes(filepath)
                        return self.changed(path=filepath) if changed else self.ok()

                # Perform the download to a binary file in chunks
                block_size = 1024 * 8
                try:
                    with open(filepath, 'wb') as f:
                        for block in iter(lambda: r.read(block_size), b''):
                            f.write(block)
                except OSError:
                    raise ActionError('unable to write the download to the path requester')

        except urllib.error.URLError:
            raise ActionError('unable to retrieve the download URL requested')

        self.set_file_attributes(filepath)
        return self.changed(path=filepath)
