import json
import shlex
import shutil

from . import Action, ActionError


class Npm(Action):
    """
    Provides the ability to manage packages using the Node.js npm package manager.

    :param name: the name of the package
    :param version: the version of the package to install
    :param state: the state that the package must be in
    :param executable: the npm executable to use
    :param mode: whether the installation should be local or global
    :param path: the path in which to install the package (when mode is local)
    :param options: additional command line options to pass to the npm command
    """
    __action_name__ = 'npm'

    def __init__(
        self, name, version=None, state='present', executable=None, mode='local', path=None,
        options=None
    ):
        self._mode = None
        self._version = None
        self._state = None
        self._path = None

        self.name = name
        self.version = version
        self.state = state
        self.path = path
        self.mode = mode
        self.executable = executable
        self.options = options

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        if self.state == 'latest' and version:
            raise ValueError(
                "you may not request 'state' to be 'latest' and provide a 'version' argument"
            )
        self._version = version

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ['present', 'latest', 'absent']:
            raise ValueError('state must be present, latest or absent')
        if state == 'latest' and self.version:
            raise ValueError(
                "you may not request 'state' to be 'latest' and provide a 'version' argument"
            )
        self._state = state

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode not in ['local', 'global']:
            raise ValueError('mode must be local or global')
        if mode == 'local' and not self.path:
            raise ValueError(
                "you must specify the 'path' parameter when 'mode' is set to 'local'"
            )
        self._mode = mode

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        if self.mode == 'local' and not path:
            raise ValueError(
                "you must specify the 'path' parameter when 'mode' is set to 'local'"
            )
        self._path = path

    def process(self):
        # Determine the npm executable
        if self.executable:
            executable = self.executable
        else:
            executable = shutil.which('npm')
            if not executable:
                raise ActionError('unable to determine npm executable to use')

        if self.mode == 'global':
            location_options = ['--global']
        else:
            location_options = ['--prefix', self.path]

        # We'll work in lowercase as npm is case insensitive
        name = self.name.lower()

        # Obtain a list of the requested package
        npm_list_proc = self.run(
            [executable, 'list', '--json', '--depth 0'] + location_options + [name],
            stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if npm_list_proc.returncode:
            raise ActionError('unable to obtain a list of npm packages')
        else:
            # Determine if the package is installed and/or outdated
            try:
                npm_list_multiple = json.loads(npm_list_proc.stdout)
                npm_list = {
                    p.lower(): i['version']
                    for p, i in npm_list_multiple.get('dependencies', {}).items()
                }

                npm_installed = name in npm_list

                if npm_installed:
                    npm_version = npm_list[name]

                if npm_installed and self.state == 'latest':
                    npm_view_proc = self.run(
                        [executable, 'view', '--json', name], stdout=True, ignore_fail=True
                    )

                    npm_view = json.loads(npm_view_proc.stdout)

                    npm_outdated = npm_version != npm_view['version']
            except (json.JSONDecodeError, IndexError, KeyError):
                raise ActionError('unable to parse package information')

        # Prepare any user provided options
        options_list = shlex.split(self.options) if self.options else []

        # Install, upgrade or remove the package as requested
        if self.state == 'present':
            if self.version:
                if npm_installed and self.version == npm_version:
                    return self.ok()
                elif npm_installed:
                    self.run(
                        [executable, 'install'] + location_options + options_list +
                        [f'{name}@{self.version}'],
                        fail_error='unable to reinstall the requested package version'
                    )
                    return self.changed()
                else:
                    self.run(
                        [executable, 'install'] + location_options + options_list +
                        [f'{name}@{self.version}'],
                        fail_error='unable to install the requested package version'
                    )
                    return self.changed()
            else:
                if npm_installed:
                    return self.ok()
                else:
                    self.run(
                        [executable, 'install'] + location_options + options_list + [name],
                        fail_error='unable to install the requested package'
                    )
                    return self.changed()

        elif self.state == 'latest':
            if npm_installed and not npm_outdated:
                return self.ok()
            elif npm_installed and npm_outdated:
                self.run(
                    [executable, 'install'] + location_options + options_list + [name],
                    fail_error='unable to upgrade the requested package'
                )
                return self.changed()
            else:
                self.run(
                    [executable, 'install'] + location_options + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        else:  # 'absent'
            if not npm_installed:
                return self.ok()
            else:
                self.run(
                    [executable, 'uninstall'] + location_options + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                return self.changed()
