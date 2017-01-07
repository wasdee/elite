import shlex

from . import Argument, Action


class Cask(Action):
    def process(self, name, state, options):
        # Obtain information about installed packages
        cask_list_proc = self.run('brew cask list', stdout=True, ignore_fail=True)

        # Check whether the package is installed
        if cask_list_proc.returncode:
            cask_installed = False
        else:
            cask_list = cask_list_proc.stdout.strip().split('\n')
            cask_installed = name in cask_list

        # Prepare any user provided options
        options_list = shlex.split(options) if options else []

        # Install or remove the package as requested
        if state == 'present':
            if cask_installed:
                self.ok()
            else:
                self.run(
                    ['brew', 'cask', 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed('package installed successfully')

        elif state == 'absent':
            if not cask_installed:
                self.ok()
            else:
                self.run(
                    ['brew', 'cask', 'remove'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                self.changed('package was removed successfully')


if __name__ == '__main__':
    cask = Cask(
        Argument('name'),
        Argument('state', choices=['present', 'absent'], default='present'),
        Argument('options', optional=True)
    )
    cask.invoke()
