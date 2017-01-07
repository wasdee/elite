import cgi
import os
import urllib.error
import urllib.parse
import urllib.request

from . import Argument, Action


class Download(Action):
    def process(self, url, path):
        # Download the requested URL to the destination path
        try:
            with urllib.request.urlopen(url) as r:
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
                        self.fail('unable to determine the filename of the download')

                    # Build the full filepath using the path given and filename determined
                    filepath = os.path.join(path, filename)

                    # Check if the file already exists in the destination path
                    if os.path.exists(filepath):
                        self.ok()

                    # Create the directory to place the download in if required
                    try:
                        if not os.path.exists(path):
                            os.makedirs(path)
                    except IOError:
                        self.fail('unable to create the directory to store the download')

                # Perform the download to a binary file in chunks
                block_size = 1024 * 8
                try:
                    with open(filepath, 'wb') as f:
                        while True:
                            block = r.read(block_size)
                            if not block:
                                break
                            f.write(block)
                except IOError:
                    self.fail('unable to write the download to the path requester')

        except urllib.error.URLError:
            self.fail('unable to retrieve the download URL requested')

        # Download was successful
        self.changed('file downloaded successfully', path=filepath)


if __name__ == '__main__':
    download = Download(
        Argument('url'),
        Argument('path')
    )
    download.invoke()
