import json

from . import Action, ActionError


class Brew(Action):
    """
    Provides the ability to manage packages using the Homebrew package manager.

    :param name: the name of the package
    :param state: the state that the package must be in
    :param options: additional command line options to pass to the brew command
    """

    def __init__(self, name, state='present', options=None, **kwargs):
        self._state = state
        self.name = name
        self.state = state
        self.options = options
        super().__init__(**kwargs)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['present', 'latest', 'absent']:
            raise ValueError('state must be present, latest or absent')
        self._state = state

    def process(self):
        # We'll work in lowercase as brew is case insensitive
        name = self.name.lower()

        # Obtain information about the requested package
        brew_info_proc = self.run(
            ['brew', 'info', '--json=v1', name], stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if brew_info_proc.returncode != 0:
            raise ActionError('unable to find a package matching the name provided')
        else:
            # Determine if the package is installed and/or outdated
            try:
                brew_info_multiple = json.loads(brew_info_proc.stdout)
                brew_info = brew_info_multiple[0]

                brew_installed = bool(brew_info['installed'])
                brew_outdated = brew_info['outdated']
            except (json.JSONDecodeError, IndexError, KeyError):
                raise ActionError('unable to parse installed package information')

        # Prepare any user provided options
        options_list = self.options if self.options else []

        # Install, upgrade or remove the package as requested
        if self.state == 'present':
            if brew_installed:
                return self.ok()
            else:
                self.run(
                    ['brew', 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        elif self.state == 'latest':
            if brew_installed and not brew_outdated:
                return self.ok()
            elif brew_installed and brew_outdated:
                self.run(
                    ['brew', 'upgrade'] + options_list + [name],
                    fail_error='unable to upgrade the requested package'
                )
                return self.changed()
            else:
                self.run(
                    ['brew', 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        else:  # 'absent'
            if not brew_installed:
                return self.ok()
            else:
                self.run(
                    ['brew', 'remove'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                return self.changed()
