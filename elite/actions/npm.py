import json
import shlex
import shutil

from . import Argument, Action


class Npm(Action):
    def validate_args(self, name, version, state, path, mode, executable, options):
        if mode == 'local' and not path:
            self.fail("you must specify the 'path' parameter when 'mode' is set to 'local'")

        if state == 'latest' and version:
            self.fail(
                "you may not request 'state' to be 'latest' and provide a 'version' argument"
            )

    def process(self, name, version, state, path, mode, executable, options):
        # Determine the npm executable
        if not executable:
            executable = shutil.which('npm')
            if not executable:
                self.fail('unable to determine npm executable to use')

        location_options = []
        if mode == 'global':
            location_options.append('--global')
        if path:
            location_options.extend(['--prefix', path])

        # We'll work in lowercase as npm is case insensitive
        name = name.lower()

        # Obtain a list of the requested package
        npm_list_proc = self.run(
            [executable, 'list', '--json', '--depth 0'] + location_options + [name],
            stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if npm_list_proc.returncode:
            npm_installed = False
        else:
            # Determine if the package is installed and/or outdated
            try:
                npm_list_multiple = json.loads(npm_list_proc.stdout)
                npm_list = {
                    p.lower(): i['version']
                    for p, i in npm_list_multiple['dependencies'].items()
                }

                npm_installed = name in npm_list

                if npm_installed:
                    npm_view_proc = self.run(
                        [executable, 'view', '--json', name], stdout=True, ignore_fail=True
                    )

                    npm_view = json.loads(npm_view_proc.stdout)

                    npm_version = npm_list[name]
                    npm_outdated = npm_version != npm_view['version']
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                print(e)
                self.fail('unable to parse package information')

        # Prepare any user provided options
        options_list = shlex.split(options) if options else []

        # Install, upgrade or remove the package as requested
        if state == 'present':
            if version:
                if npm_installed and version == npm_version:
                    self.ok()
                elif npm_installed:
                    self.run(
                        [executable, 'install'] + location_options + options_list +
                        [f'{name}@{version}'],
                        fail_error='unable to reinstall the requested package version'
                    )
                    self.changed('package reinstalled to requested version successfully')
                else:
                    self.run(
                        [executable, 'install'] + location_options + options_list +
                        [f'{name}@{version}'],
                        fail_error='unable to install the requested package version'
                    )
                    self.changed('package installed to requested version successfully')
            else:
                if npm_installed:
                    self.ok()
                else:
                    self.run(
                        [executable, 'install'] + location_options + options_list + [name],
                        fail_error='unable to install the requested package'
                    )
                    self.changed('package installed successfully')

        elif state == 'latest':
            if npm_installed and not npm_outdated:
                self.ok()
            elif npm_installed and npm_outdated:
                self.run(
                    [executable, 'install'] + location_options + options_list + [name],
                    fail_error='unable to upgrade the requested package'
                )
                self.changed('existing outdated package found and upgraded successfully')
            else:
                self.run(
                    [executable, 'install'] + location_options + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed('package installed successfully')

        elif state == 'absent':
            if not npm_installed:
                self.ok()
            else:
                self.run(
                    [executable, 'uninstall'] + location_options + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                self.changed('package was removed successfully')


if __name__ == '__main__':
    npm = Npm(
        Argument('name'),
        Argument('version', optional=True),
        Argument('state', choices=['present', 'latest', 'absent'], default='present'),
        Argument('path', optional=True),
        Argument('mode', choices=['local', 'global'], default='local'),
        Argument('executable', optional=True),
        Argument('options', optional=True)
    )
    npm.invoke()
