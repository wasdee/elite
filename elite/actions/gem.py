import shlex
import shutil

import yaml

from . import Argument, Action


def ruby_object(loader, node):
    return loader.construct_mapping(node)


# Register YAML constructors to convert Ruby objects from gem specification to dicts
for ruby_type in [
    '!ruby/object:Gem::Specification',
    '!ruby/object:Gem::Requirement',
    '!ruby/object:Gem::Dependency',
    '!ruby/object:Gem::Version'
]:
    yaml.add_constructor(ruby_type, ruby_object)


class Gem(Action):
    def validate_args(self, name, version, state, executable, options):
        if state == 'latest' and version:
            self.fail(
                "you may not request 'state' to be 'latest' and provide a 'version' argument"
            )

    def process(self, name, version, state, executable, options):
        # Determine the gem executable
        if not executable:
            executable = shutil.which('gem')
            if not executable:
                self.fail('unable to find a gem executable to use')

        # Obtain the specification of the requested package containing all installed versions
        # of the requested package
        gem_spec_proc = self.run(
            [executable, 'specification', '--all', name], stdout=True, ignore_fail=True
        )

        # Check whether the package is installed and whether it is outdated
        if gem_spec_proc.returncode:
            gem_installed = False
        else:
            gem_installed = True

            # Determine if the package is installed and/or outdated
            try:
                gem_spec = yaml.load_all(gem_spec_proc.stdout)
                gem_versions = [p['version']['version'] for p in gem_spec]

                if state == 'latest':
                    # Obtain the latest package version details
                    gem_spec_remote_proc = self.run(
                        [executable, 'specification', '--remote', name],
                        stdout=True, ignore_fail=True
                    )
                    gem_spec_remote = yaml.load(gem_spec_remote_proc.stdout)
                    gem_remote_version = gem_spec_remote['version']['version']

                    # Determine if the latest package is already installed
                    gem_outdated = gem_remote_version not in gem_versions
            except (yaml.scanner.ScannerError, KeyError):
                self.fail('unable to parse installed package listing')

        # Prepare any user provided options
        options_list = shlex.split(options) if options else []

        # Install, upgrade or remove the package as requested
        if state == 'present':
            if version:
                if gem_installed and version in gem_versions:
                    self.ok()
                else:
                    self.run(
                        [executable, 'install', '--version', version] + options_list + [name],
                        fail_error='unable to install the requested package version'
                    )
                    self.changed()
            else:
                if gem_installed:
                    self.ok()
                else:
                    self.run(
                        [executable, 'install'] + options_list + [name],
                        fail_error='unable to install the requested package'
                    )
                    self.changed()

        elif state == 'latest':
            if gem_installed and not gem_outdated:
                self.ok()
            else:
                self.run(
                    [executable, 'install'] + options_list + [name],
                    fail_error='unable to install the requested package'
                )
                self.changed()

        elif state == 'absent':
            if not gem_installed:
                self.ok()
            elif version:
                if version not in gem_versions:
                    self.ok()

                self.run(
                    [executable, 'uninstall', '--version', version] + options_list + [name],
                    fail_error='unable to remove the requested package version'
                )
                self.changed()
            else:
                self.run(
                    [executable, 'uninstall', '--all', '--executable'] + options_list + [name],
                    fail_error='unable to remove the requested package'
                )
                self.changed()


if __name__ == '__main__':
    gem = Gem(
        Argument('name'),
        Argument('version', optional=True),
        Argument('state', choices=['present', 'latest', 'absent'], default='present'),
        Argument('executable', optional=True),
        Argument('options', optional=True)
    )
    gem.invoke()
