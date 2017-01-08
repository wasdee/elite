import json
import os
import shlex
import shutil

from . import Argument, Action


class Pip(Action):
    def validate_args(self, name, version, state, executable, virtualenv, options):
        if virtualenv and executable:
            self.fail("you must not specify both the 'virtualenv' and 'executable' arguments")

        if state == 'latest' and version:
            self.fail(
                "you may not request 'state' to be 'latest' and provide a 'version' argument"
            )

    def process(self, name, version, state, executable, virtualenv, options):
        # Determine the pip executable
        if virtualenv:
            for pip in ['pip', 'pip3', 'pip2']:
                if os.path.exists(os.path.join(virtualenv, 'bin', pip)):
                    executable = os.path.join(virtualenv, 'bin', pip)
                    break
            else:
                self.fail('unable to find a pip executable in the virtualenv supplied')
        elif not executable:
            executable = shutil.which('pip') or shutil.which('pip3') or shutil.which('pip2')
            if not executable:
                self.fail('unable to determine pip executable to use')

        # We'll work in lowercase as pip is case insensitive
        name = name.lower()

        # Obtain a list of installed packages
        pip_list_proc = self.run(
            [executable, 'list', '--format', 'json'], stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if pip_list_proc.returncode:
            pip_installed = False
        else:
            # Determine if the package is installed and/or outdated
            try:
                pip_list_multiple = json.loads(pip_list_proc.stdout)
                pip_list = {p['name'].lower(): p['version'] for p in pip_list_multiple}

                pip_installed = name in pip_list

                if pip_installed:
                    pip_list_outdated_proc = self.run(
                        [executable, 'list', '--format', 'json', '--outdated'],
                        stdout=True, ignore_fail=True
                    )

                    pip_list_outdated_multiple = json.loads(pip_list_outdated_proc.stdout)
                    pip_list_outdated_names = [
                        p['name'].lower() for p in pip_list_outdated_multiple
                    ]

                    pip_version = pip_list[name]
                    pip_outdated = name in pip_list_outdated_names
            except (json.JSONDecodeError, IndexError, KeyError):
                self.fail('unable to parse installed package listing')

        # Prepare any user provided options
        options_list = shlex.split(options) if options else []

        # Install, upgrade or remove the package as requested
        if state == 'present':
            if version:
                if pip_installed and version == pip_version:
                    self.ok()
                elif pip_installed:
                    self.run(
                        [executable, 'install'] + options_list + [f'{name}=={version}'],
                        fail_error='unable to reinstall the requested package version'
                    )
                    self.changed('package reinstalled to requested version successfully')
                else:
                    self.run(
                        [executable, 'install'] + options_list + [f'{name}=={version}'],
                        fail_error='unable to install the requested package version'
                    )
                    self.changed('package installed to requested version successfully')
            else:
                if pip_installed:
                    self.ok()
                else:
                    self.run(
                        [executable, 'install'] + options_list + [name],
                        fail_error='unable to install the requested package'
                    )
                    self.changed('package installed successfully')

        elif state == 'latest':
            if pip_installed and not pip_outdated:
                self.ok()
            elif pip_installed and pip_outdated:
                self.run(
                    [executable, 'install', '--upgrade'] + options_list + [name],
                    fail_error='unable to upgrade the requested package'
                )
                self.changed('existing outdated package found and upgraded successfully')
            else:
                self.run(
                    [executable, 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed('package installed successfully')

        elif state == 'absent':
            if not pip_installed:
                self.ok()
            else:
                self.run(
                    [executable, 'uninstall', '--yes'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                self.changed('package was removed successfully')


if __name__ == '__main__':
    pip = Pip(
        Argument('name'),
        Argument('version', optional=True),
        Argument('state', choices=['present', 'latest', 'absent'], default='present'),
        Argument('executable', optional=True),
        Argument('virtualenv', optional=True),
        Argument('options', optional=True)
    )
    pip.invoke()
