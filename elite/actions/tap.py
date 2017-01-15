from . import Argument, Action


class Tap(Action):
    def process(self, name, state, url):
        # We'll work in lowercase as brew is case insensitive
        name = name.lower()

        # Obtain information about installed taps
        tap_list_proc = self.run('brew tap', stdout=True, ignore_fail=True)

        # Check whether the package is installed
        if tap_list_proc.returncode:
            tapped = False
        else:
            tap_list = tap_list_proc.stdout.rstrip().split('\n')
            tapped = name in tap_list

        # Prepare the URL if provided options
        url_list = [url] if url else []

        # Install or remove the package as requested
        if state == 'present':
            if tapped:
                self.ok()
            else:
                self.run(
                    ['brew', 'tap'] + [name] + url_list,
                    fail_error='unable to tap the requested repository'
                )
                self.changed()

        elif state == 'absent':
            if not tapped:
                self.ok()
            else:
                self.run(
                    ['brew', 'untap', name],
                    fail_error='unable to untap the requested repository'
                )
                self.changed()


if __name__ == '__main__':
    tap = Tap(
        Argument('name'),
        Argument('state', choices=['present', 'absent'], default='present'),
        Argument('url', optional=True)
    )
    tap.invoke()
