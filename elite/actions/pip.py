import json
import os
import shlex
import shutil

from . import Action, ActionError


class Pip(Action):
    """
    Provides the ability to manage packages using the Python pip package manager.

    :param name: the name of the package
    :param version: the version of the package to install
    :param state: the state that the package must be in
    :param executable: the pip executable to use
    :param virtualenv: the path of a virtualenv to install packages into
    :param options: additional command line options to pass to the pip command
    """
    __action_name__ = 'pip'

    def __init__(
        self, name, version=None, state='present', executable=None, virtualenv=None, options=None
    ):
        self._state = None
        self._version = None
        self._executable = None
        self._virtualenv = None

        self.name = name
        self.version = version
        self.state = state
        self.executable = executable
        self.virtualenv = virtualenv
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
    def virtualenv(self):
        return self._virtualenv

    @virtualenv.setter
    def virtualenv(self, virtualenv):
        if virtualenv and self.executable:
            raise ValueError(
                "you must not specify both the 'virtualenv' and 'executable' arguments"
            )
        self._virtualenv = virtualenv

    @property
    def executable(self):
        return self._executable

    @executable.setter
    def executable(self, executable):
        if self.virtualenv and executable:
            raise ValueError(
                "you must not specify both the 'virtualenv' and 'executable' arguments"
            )
        self._executable = executable

    def process(self):
        # Determine the pip executable
        if self.virtualenv:
            for pip in ['pip', 'pip3', 'pip2']:
                if os.path.exists(os.path.join(self.virtualenv, 'bin', pip)):
                    executable = os.path.join(self.virtualenv, 'bin', pip)
                    break
            else:
                raise ActionError('unable to find a pip executable in the virtualenv supplied')
        elif self.executable:
            executable = self.executable
        else:
            executable = shutil.which('pip') or shutil.which('pip3') or shutil.which('pip2')
            if not executable:
                raise ActionError('unable to determine pip executable to use')

        # We'll work in lowercase as pip is case insensitive
        name = self.name.lower()

        # Obtain a list of installed packages
        pip_list_proc = self.run(
            [executable, 'list', '--format', 'json'], stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if pip_list_proc.returncode:
            raise ActionError('unable to obtain a list of pip packages')
        else:
            # Determine if the package is installed and/or outdated
            try:
                pip_list_multiple = json.loads(pip_list_proc.stdout)
                pip_list = {p['name'].lower(): p['version'] for p in pip_list_multiple}

                pip_installed = name in pip_list

                if pip_installed:
                    pip_version = pip_list[name]

                if pip_installed and self.state == 'latest':
                    pip_list_outdated_proc = self.run(
                        [executable, 'list', '--format', 'json', '--outdated'],
                        stdout=True, ignore_fail=True
                    )

                    pip_list_outdated_multiple = json.loads(pip_list_outdated_proc.stdout)
                    pip_list_outdated_names = [
                        p['name'].lower() for p in pip_list_outdated_multiple
                    ]

                    pip_outdated = name in pip_list_outdated_names
            except (json.JSONDecodeError, IndexError, KeyError):
                raise ActionError('unable to parse installed package listing')

        # Prepare any user provided options
        options_list = shlex.split(self.options) if self.options else []

        # Install, upgrade or remove the package as requested
        if self.state == 'present':
            if self.version:
                if pip_installed and self.version == pip_version:
                    return self.ok()
                elif pip_installed:
                    self.run(
                        [executable, 'install'] + options_list + [f'{name}=={self.version}'],
                        fail_error='unable to reinstall the requested package version'
                    )
                    return self.changed()
                else:
                    self.run(
                        [executable, 'install'] + options_list + [f'{name}=={self.version}'],
                        fail_error='unable to install the requested package version'
                    )
                    return self.changed()
            else:
                if pip_installed:
                    return self.ok()
                else:
                    self.run(
                        [executable, 'install'] + options_list + [name],
                        fail_error='unable to install the requested package'
                    )
                    return self.changed()

        elif self.state == 'latest':
            if pip_installed and not pip_outdated:
                return self.ok()
            elif pip_installed and pip_outdated:
                self.run(
                    [executable, 'install', '--upgrade'] + options_list + [name],
                    fail_error='unable to upgrade the requested package'
                )
                return self.changed()
            else:
                self.run(
                    [executable, 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        else:  # 'absent'
            if not pip_installed:
                return self.ok()
            else:
                self.run(
                    [executable, 'uninstall', '--yes'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                return self.changed()
