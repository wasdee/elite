import json
import shlex

from . import Argument, Action


class Brew(Action):
    def process(self, name, state, options):
        # We'll work in lowercase as brew is case insensitive
        name = name.lower()

        # Obtain information about the requested package
        brew_info_proc = self.run(
            ['brew', 'info', '--json=v1', name], stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if brew_info_proc.returncode:
            brew_installed = False
        else:
            # Determine if the package is installed and/or outdated
            try:
                brew_info_multiple = json.loads(brew_info_proc.stdout)
                brew_info = brew_info_multiple[0]

                brew_installed = True if brew_info['installed'] else False
                brew_outdated = brew_info['outdated']
            except (json.JSONDecodeError, IndexError, KeyError):
                self.fail('unable to parse installed package information')

        # Prepare any user provided options
        options_list = shlex.split(options) if options else []

        # Install, upgrade or remove the package as requested
        if state == 'present':
            if brew_installed:
                self.ok()
            else:
                self.run(
                    ['brew', 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed()

        elif state == 'latest':
            if brew_installed and not brew_outdated:
                self.ok()
            elif brew_installed and brew_outdated:
                self.run(
                    ['brew', 'upgrade'] + options_list + [name],
                    fail_error='unable to upgrade the requested package'
                )
                self.changed()
            else:
                self.run(
                    ['brew', 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed()

        elif state == 'absent':
            if not brew_installed:
                self.ok()
            else:
                self.run(
                    ['brew', 'remove'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                self.changed()


if __name__ == '__main__':
    brew = Brew(
        Argument('name'),
        Argument('state', choices=['present', 'latest', 'absent'], default='present'),
        Argument('options', optional=True)
    )
    brew.invoke()
