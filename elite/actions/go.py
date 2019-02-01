import os
import shutil

from . import Action, ActionError


class Go(Action):
    """
    Provides the ability to manage Go packages.

    :param name: the name of the package
    :param state: the state that the package must be in
    """

    def __init__(self, name, state='present', **kwargs):
        self._state = state
        self.name = name
        self.state = state
        super().__init__(**kwargs)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['present', 'absent']:
            raise ValueError('state must be present or absent')
        self._state = state

    def process(self):
        # Determine the $GOPATH
        go_path = os.environ.get('GOPATH', os.path.expanduser('~/go'))

        # Obtain information about installed packages
        go_list_proc = self.run(['go', 'list', 'all'], stdout=True, ignore_fail=True, cache=True)

        # Check whether the package is installed
        if go_list_proc.returncode != 0:
            raise ActionError('unable to obtain a list of packages')

        package_list = go_list_proc.stdout.rstrip().split('\n')
        installed = self.name in package_list

        # Install or remove the package as requested
        if self.state == 'present':
            if installed:
                return self.ok()
            else:
                self.run(
                    ['go', 'get'] + [self.name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        else:  # 'absent'
            if not installed:
                return self.ok()
            else:
                try:
                    shutil.rmtree(os.path.join(go_path, 'src', self.name))
                    return self.changed()
                except OSError:
                    raise ActionError('unable to remove the requested package')
