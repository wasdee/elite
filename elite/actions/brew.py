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

        # Obtain information about installed packages
        brew_list_proc = self.run(
            ['brew', 'list'], stdout=True, ignore_fail=True, cache=True
        )

        # Check whether the package is installed and whether it is outdated
        if brew_list_proc.returncode != 0:
            raise ActionError('unable to obtain a list of brew packages')

        # Determine if the package is installed
        brew_list = brew_list_proc.stdout.rstrip().split('\n')
        brew_installed = self.name in brew_list

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
            if brew_installed:
                # Determine if the installed package is outdated
                brew_outdated = False

                brew_outdated_proc = self.run(
                    ['brew', 'outdated', '--json=v1'], stdout=True, ignore_fail=True, cache=True
                )
                if brew_outdated_proc.returncode == 0:
                    brew_outdated_multiple = json.loads(brew_outdated_proc.stdout)
                    brew_outdated_list = [b['name'] for b in brew_outdated_multiple]
                    brew_outdated = self.name in brew_outdated_list

                if not brew_outdated:
                    return self.ok()
                else:
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
