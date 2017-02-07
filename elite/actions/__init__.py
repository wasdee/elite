import ast
import grp
import keyword
import os
import pwd
import shlex
import subprocess
import sys
from pprint import pprint

from ..constants import FLAGS


# A list of reserved argument names that may not be used by actions
FORBIDDEN_ARGS = ['sudo', 'ok', 'changed', 'ignore_failed']


class Argument(object):
    def __init__(self, name, optional=False, default=None, choices=None):
        self.name = name
        self.optional = True if default is not None else optional
        self.default = default
        self.choices = choices

    def __repr__(self):
        args = [f'name={self.name!r}']
        if not self.optional:
            args.append(f'optional={self.optional!r}')
        if self.default is not None:
            args.append(f'default={self.default!r}')
        if self.choices is not None:
            args.append(f'choices={self.choices!r}')
        return f"{type(self).__name__}({', '.join(args)})"


# Convenience list of useful arguments to add for actions that modify files
FILE_ATTRIBUTE_ARGS = [
    Argument('mode', optional=True),
    Argument('owner', optional=True),
    Argument('group', optional=True),
    Argument('flags', optional=True),
]


class Action(object):
    def __init__(self, *arg_specs):
        for arg_spec in arg_specs:
            # Check for forbidden arguments used be elite
            if arg_spec.name in FORBIDDEN_ARGS:
                self.fail(f"module uses argument '{arg_spec.name}' which is forbidden")

            # Check for arguments that override Python keywords
            if arg_spec.name in keyword.kwlist:
                self.fail(f"module uses argument '{arg_spec.name}' which is a Python keyword")

            # Check for arguments that override Python builtins
            # TODO: something not right here dawg
            # if arg_spec.name in dir(__builtins__):
            #     self.fail(f"module uses argument '{arg_spec.name}' which is a Python builtin")

        self.arg_specs = list(arg_specs)

        # Parse and validate arguments via stdin
        try:
            self.args = ast.literal_eval(sys.stdin.read())
        except KeyboardInterrupt:
            exit(2)
        except ValueError:
            self.fail('the arguments provided could not be parsed')

        self.validate_args_against_spec()

        # Perform any further argument validation as required
        self.validate_args(**self.args)

        # Open /dev/null for our run method
        self.devnull = open(os.devnull, 'w')

    def hide_pyobjc_app(self):
        # When certain actions use PyObjC, we must set the spawned app to run in the background
        # so it # doesn't show up in the Dock.
        # Please only call this when necessary as it does require some processing and time.
        from AppKit import NSBundle
        bundle_info = NSBundle.mainBundle().infoDictionary()
        bundle_info["LSBackgroundOnly"] = True

    def invoke(self):
        """Run the main process function for the action with the appropriate args."""
        self.process(**self.args)

    def validate_args_against_spec(self):
        # Check that only supported arguments were provided
        arg_spec_names = [a.name for a in self.arg_specs]
        for arg_name in self.args.keys():
            if arg_name not in arg_spec_names:
                self.fail(f"provided argument '{arg_name}' is not supported by this action")

        # Validate our argument specification
        for arg_spec in self.arg_specs:
            # Check that each of the arguments are provided or set the default if optional
            if arg_spec.name not in self.args:
                if arg_spec.optional:
                    self.args[arg_spec.name] = arg_spec.default
                    continue
                else:
                    self.fail(f"mandatory argument '{arg_spec.name}' was not provided")

            # Verify that the provided value is one of the choices
            if (
                arg_spec.choices and
                self.args[arg_spec.name] not in arg_spec.choices
            ):
                self.fail(f"argument '{arg_spec.name}' must be one of {arg_spec.choices}")

    def validate_args(self, **args):
        pass

    def ok(self, **data):
        pprint({'changed': False, 'ok': True, **data})
        exit(0)

    def changed(self, **data):
        pprint({'changed': True, 'ok': True, **data})
        exit(0)

    def fail(self, message, **data):
        pprint({'message': message, 'ok': False, **data})
        exit(1)

    def run(self, command, ignore_fail=False, fail_error=None, **kwargs):
        # Allow for the user to send in a string instead of a list for the command
        if isinstance(command, str) and not kwargs.get('shell'):
            command = shlex.split(command)

        # Allow for the user to simply set stdout to a bool to enable them
        kwargs['stdout'] = subprocess.PIPE if kwargs.get('stdout') else self.devnull

        # Allow for a bool to enable stderr or enable it anyway if the command will fail on
        # error and no message has been provided
        if kwargs.get('stderr') or not ignore_fail and not fail_error:
            kwargs['stderr'] = subprocess.PIPE
        else:
            kwargs['stderr'] = self.devnull

        # Run the command
        try:
            proc = subprocess.run(command, encoding='utf-8', **kwargs)
        except FileNotFoundError:
            self.fail(f'unable to find executable for command {command}')

        # Fail if the command returned a non-zero returrn code
        if proc.returncode and not ignore_fail:
            if proc.stderr:
                self.fail(proc.stderr.rstrip())
            elif fail_error:
                self.fail(fail_error)
            else:
                self.fail(f'unable to execute command {command}')

        return proc

    def set_file_attributes(self, path):
        # Obtain the associated arguments to set file attributes
        mode = self.args.get('mode')
        owner = self.args.get('owner')
        group = self.args.get('group')
        flags = self.args.get('flags')

        # No file attributes have been set, so we bail and advise that no changes were made
        if not any([mode, owner, group]) and flags is None:
            return False

        changed = False
        stat = os.stat(path)

        # Set the file mode if required
        if mode and oct(stat.st_mode)[-4:] != mode:
            changed = True

            # Determine the binary representation of the mode requseted
            mode_bin = int(mode, 8)

            try:
                os.chmod(path, mode_bin, follow_symlinks=False)
            except OSError:
                self.fail('unable to set the requested mode on the path specified')

        # Set the file owner and/or groups
        if owner or group:
            # Obtain the uid of the owner requested
            if owner:
                try:
                    uid = pwd.getpwnam(owner).pw_uid
                except KeyError:
                    self.fail('the owner requested was not found')
            else:
                uid = -1

            # Obtain the gid of the group requested
            if group:
                try:
                    gid = grp.getgrnam(group).gr_gid
                except KeyError:
                    self.fail('the group requested was not found')
            else:
                gid = -1

            # Update the owner and/or group if required
            if owner and stat.st_uid != uid or group and stat.st_gid != gid:
                changed = True
                try:
                    os.chown(path, uid, gid)
                except OSError:
                    self.fail('unable to set the requested owner on the path specified')

        # Set the file flags
        if flags is not None:
            # Determine the binary representation of the flags requseted
            flags_bin = 0

            for flag in flags:
                if flag not in FLAGS:
                    self.fail('the specified flag is unsupported')

                flags_bin |= FLAGS[flag]

            # Update the flags if required
            if stat.st_flags != flags_bin:
                changed = True
                try:
                    os.chflags(path, flags_bin)
                except OSError:
                    self.fail('unable to set the requested flags on the path specified')

        return changed
