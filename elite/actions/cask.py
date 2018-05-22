import shlex

from . import Argument, Action


class Cask(Action):
    def process(self, name, state, options):
        # Obtain information about installed packages
        cask_list_proc = self.run('brew cask list', stdout=True, ignore_fail=True)

        # Check whether the package is installed using only its short name
        # (e.g. fgimian/general/cog will check for a cask called cog)
        if cask_list_proc.returncode:
            cask_installed = False
        else:
            cask_list = cask_list_proc.stdout.rstrip().split('\n')
            cask_installed = name.split('/')[-1] in cask_list

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
                self.changed()

        if state == 'latest':
            if cask_installed:
                # Determine if the installed package is outdated
                cask_outdated = False

                cask_outdated_proc = self.run('brew cask outdated', stdout=True, ignore_fail=True)
                if not cask_outdated_proc.returncode:
                    cask_list = cask_outdated_proc.stdout.rstrip().split('\n')
                    cask_outdated = name.split('/')[-1] in cask_list

                if not cask_outdated:
                    self.ok()
                else:
                    self.run(
                        ['brew', 'cask', 'upgrade'] + options_list + [name],
                        fail_error='unable to upgrade the requested package'
                    )
                    self.changed()
            else:
                self.run(
                    ['brew', 'cask', 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed()

        elif state == 'absent':
            if not cask_installed:
                self.ok()
            else:
                self.run(
                    ['brew', 'cask', 'remove'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                self.changed()


if __name__ == '__main__':
    cask = Cask(
        Argument('name'),
        Argument('state', choices=['present', 'latest', 'absent'], default='present'),
        Argument('options', optional=True)
    )
    cask.invoke()
