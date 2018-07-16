from . import Action, ActionError


class Tap(Action):
    """
    Provides the ability to manage taps for the Homebrew package manager.

    :param name: the name of the tap
    :param state: the state that the tap must be in
    :param url: the url containing the tap
    """
    __action_name__ = 'tap'

    def __init__(self, name, state='present', url=None):
        self._state = None

        self.name = name
        self.state = state
        self.url = url

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['present', 'absent']:
            raise ValueError('state must be present or absent')
        self._state = state

    def process(self):
        # We'll work in lowercase as brew is case insensitive
        name = self.name.lower()

        # Obtain information about installed taps
        tap_list_proc = self.run(['brew', 'tap'], stdout=True, ignore_fail=True)

        # Check whether the package is installed
        if tap_list_proc.returncode != 0:
            raise ActionError('unable to obtain a list of taps')

        tap_list = tap_list_proc.stdout.rstrip().split('\n')
        tapped = name in tap_list

        # Prepare the URL if provided options
        url_list = [self.url] if self.url else []

        # Install or remove the package as requested
        if self.state == 'present':
            if tapped:
                return self.ok()
            else:
                self.run(
                    ['brew', 'tap'] + [name] + url_list,
                    fail_error='unable to tap the requested repository'
                )
                return self.changed()

        else:  # 'absent'
            if not tapped:
                return self.ok()
            else:
                self.run(
                    ['brew', 'untap', name],
                    fail_error='unable to untap the requested repository'
                )
                return self.changed()
