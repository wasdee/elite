from . import Action, ActionError


class Cask(Action):
    """
    Provides the ability to manage packages using Cask via the Homebrew package manager.

    :param name: the name of the package
    :param state: the state that the package must be in
    :param options: additional command line options to pass to the brew cask command
    """
    __action_name__ = 'cask'

    def __init__(self, name, state='present', options=None):
        self._state = None

        self.name = name
        self.state = state
        self.options = options

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['present', 'latest', 'absent']:
            raise ValueError('state must be present, latest or absent')
        self._state = state

    def process(self):
        # Obtain information about installed packages
        cask_list_proc = self.run(['brew', 'cask', 'list'], stdout=True, ignore_fail=True)

        # Check whether the package is installed using only its short name
        # (e.g. fgimian/general/cog will check for a cask called cog)
        if cask_list_proc.returncode != 0:
            raise ActionError('unable to obtain a list of cask packages')

        cask_list = cask_list_proc.stdout.rstrip().split('\n')
        cask_installed = self.name.split('/')[-1] in cask_list

        # Prepare any user provided options
        options_list = self.options if self.options else []

        # Install or remove the package as requested
        if self.state == 'present':
            if cask_installed:
                return self.ok()
            else:
                self.run(
                    ['brew', 'cask', 'install'] + options_list + [self.name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        if self.state == 'latest':
            if cask_installed:
                # Determine if the installed package is outdated
                cask_outdated = False

                cask_outdated_proc = self.run(
                    ['brew', 'cask', 'outdated'], stdout=True, ignore_fail=True
                )
                if cask_outdated_proc.returncode == 0:
                    cask_list = cask_outdated_proc.stdout.rstrip().split('\n')
                    cask_outdated = self.name.split('/')[-1] in cask_list

                if not cask_outdated:
                    return self.ok()
                else:
                    self.run(
                        ['brew', 'cask', 'upgrade'] + options_list + [self.name],
                        fail_error='unable to upgrade the requested package'
                    )
                    return self.changed()
            else:
                self.run(
                    ['brew', 'cask', 'install'] + options_list + [self.name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        else:  # 'absent'
            if not cask_installed:
                return self.ok()
            else:
                self.run(
                    ['brew', 'cask', 'remove'] + options_list + [self.name],
                    fail_error='unable to remove the requested package'
                )
                return self.changed()
