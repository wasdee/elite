import shlex
import shutil

from ruamel.yaml import YAML, YAMLError

from . import Action, ActionError


# Configure YAML parsing to be safe by default
yaml = YAML(typ='safe')


def ruby_object(loader, node):
    return loader.construct_mapping(node)


# Register YAML constructors to convert Ruby objects from gem specification to dicts
for ruby_type in [
    '!ruby/object:Gem::Specification',
    '!ruby/object:Gem::Requirement',
    '!ruby/object:Gem::Dependency',
    '!ruby/object:Gem::Version'
]:
    yaml.Constructor.add_constructor(ruby_type, ruby_object)


class Gem(Action):
    """
    Provides the ability to manage packages using the Ruby gem package manager.

    :param name: the name of the package
    :param version: the version of the package to install
    :param state: the state that the package must be in
    :param executable: the gem executable to use
    :param options: additional command line options to pass to the gem command
    """
    __action_name__ = 'gem'

    def __init__(self, name, version=None, state='present', executable=None, options=None):
        self._version = None
        self._state = None

        self.name = name
        self.version = version
        self.state = state
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

    def process(self):
        # Determine the gem executable
        if self.executable:
            executable = self.executable
        else:
            executable = shutil.which('gem')
            if not executable:
                raise ActionError('unable to find a gem executable to use')

        # Obtain the specification of the requested package containing all installed versions
        # of the requested package
        gem_spec_proc = self.run(
            [executable, 'specification', '--all', self.name], stdout=True, ignore_fail=True
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

                if self.state == 'latest':
                    # Obtain the latest package version details
                    gem_spec_remote_proc = self.run(
                        [executable, 'specification', '--remote', self.name],
                        stdout=True, ignore_fail=True
                    )
                    gem_spec_remote = yaml.load(gem_spec_remote_proc.stdout)
                    gem_remote_version = gem_spec_remote['version']['version']

                    # Determine if the latest package is already installed
                    gem_outdated = gem_remote_version not in gem_versions
            except (YAMLError, KeyError):
                raise ActionError('unable to parse installed package listing')

        # Prepare any user provided options
        options_list = shlex.split(self.options) if self.options else []

        # Install, upgrade or remove the package as requested
        if self.state == 'present':
            if self.version:
                if gem_installed and self.version in gem_versions:
                    return self.ok()
                else:
                    self.run(
                        [executable, 'install', '--version', self.version] +
                        options_list + [self.name],
                        fail_error='unable to install the requested package version'
                    )
                    return self.changed()
            else:
                if gem_installed:
                    return self.ok()
                else:
                    self.run(
                        [executable, 'install'] + options_list + [self.name],
                        fail_error='unable to install the requested package'
                    )
                    return self.changed()

        elif self.state == 'latest':
            if gem_installed and not gem_outdated:
                return self.ok()
            else:
                self.run(
                    [executable, 'install'] + options_list + [self.name],
                    fail_error='unable to install the requested package'
                )
                return self.changed()

        else:  # 'absent'
            if not gem_installed:
                return self.ok()
            elif self.version:
                if self.version not in gem_versions:
                    return self.ok()

                self.run(
                    [executable, 'uninstall', '--version', self.version, '--executables'] +
                    options_list + [self.name],
                    fail_error='unable to remove the requested package version'
                )
                return self.changed()
            else:
                self.run(
                    [executable, 'uninstall', '--all', '--executables'] +
                    options_list + [self.name],
                    fail_error='unable to remove the requested package'
                )
                return self.changed()
