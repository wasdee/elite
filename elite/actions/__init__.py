import grp
import os
import pwd
import shutil
import subprocess
from collections import namedtuple

from ..constants import FLAGS


# Open /dev/null for our run method
devnull = open(os.devnull, 'w')


class ActionError(Exception):
    pass


ActionResponse = namedtuple('ActionResponse', ['changed', 'data'], defaults=({},))


class Action:
    """
    The action base class which actions may inherit from.

    :param preexec_fn: the function to call prior exec of commands that are run
    """

    def __init__(self, preexec_fn=None):
        self.preexec_fn = preexec_fn

    def ok(self, **data):
        return ActionResponse(changed=False, data=data)

    def changed(self, **data):
        return ActionResponse(changed=True, data=data)

    def run(self, command, ignore_fail=False, fail_error=None, **kwargs):
        # Allow for the user to simply set stdout to a bool to enable them
        if kwargs.get('stdout'):
            kwargs['stdout'] = subprocess.PIPE
        else:
            kwargs['stdout'] = devnull

        # Allow for a bool to enable stderr or enable it anyway if the command will fail on
        # error and no message has been provided
        if kwargs.get('stderr') or not ignore_fail and not fail_error:
            kwargs['stderr'] = subprocess.PIPE
        else:
            kwargs['stderr'] = devnull

        # Run the command
        try:
            process = subprocess.run(
                command, encoding='utf-8', preexec_fn=self.preexec_fn, **kwargs
            )
        except FileNotFoundError:
            raise ActionError(f'unable to find executable for command {command}')

        # Fail if the command returned a non-zero returrn code
        if process.returncode != 0 and not ignore_fail:
            if fail_error:
                raise ActionError(fail_error)
            elif process.stderr:
                raise ActionError(process.stderr.rstrip())
            else:
                raise ActionError(f'unable to execute command {command}')

        return process


class FileAction(Action):
    """
    The file action base class which file-based actions may inherit from.

    :param mode: the mode of the file being written
    :param owner: the username which should own the file being written
    :param group: the group that should own the file being written
    :param flags: any BSD flags that should be applied to the file being written
    """

    def __init__(self, mode=None, owner=None, group=None, flags=None, **kwargs):
        self.mode = mode
        self.owner = owner
        self.group = group
        self.flags = flags
        super().__init__(**kwargs)

    def set_file_attributes(self, path):
        # No file attributes have been set, so we bail and advise that no changes were made
        if not any([self.mode, self.owner, self.group]) and self.flags is None:
            return False

        changed = False
        try:
            stat = os.stat(path)
        except OSError:
            raise ActionError('unable to find the requested path specified')

        # Set the file mode if required
        if self.mode and oct(stat.st_mode)[-4:] != self.mode:
            changed = True

            # Determine the binary representation of the mode requseted
            mode_bin = int(self.mode, 8)

            try:
                os.chmod(path, mode_bin, follow_symlinks=False)
            except OSError:
                raise ActionError('unable to set the requested mode on the path specified')

        # Set the file owner and/or groups
        if self.owner or self.group:
            # Obtain the uid of the owner requested
            if self.owner:
                try:
                    uid = pwd.getpwnam(self.owner).pw_uid
                except KeyError:
                    raise ActionError('the owner requested was not found')
            else:
                uid = -1

            # Obtain the gid of the group requested
            if self.group:
                try:
                    gid = grp.getgrnam(self.group).gr_gid
                except KeyError:
                    raise ActionError('the group requested was not found')
            else:
                gid = -1

            # Update the owner and/or group if required
            if self.owner and stat.st_uid != uid or self.group and stat.st_gid != gid:
                changed = True
                try:
                    os.chown(path, uid, gid)
                except OSError:
                    raise ActionError('unable to set the requested owner on the path specified')

        # Set the file flags
        if self.flags is not None:
            # Determine the binary representation of the flags requseted
            flags_bin = 0

            for flag in self.flags:
                if flag not in FLAGS:
                    raise ActionError('the specified flag is unsupported')

                flags_bin |= FLAGS[flag]

            # Update the flags if required
            if stat.st_flags != flags_bin:
                changed = True
                try:
                    os.chflags(path, flags_bin)
                except OSError:
                    raise ActionError('unable to set the requested flags on the path specified')

        return changed

    def remove(self, path):
        if os.path.isfile(path):
            try:
                os.remove(path)
                return True
            except OSError:
                raise ActionError('existing file could not be removed')
        elif os.path.islink(path):
            try:
                os.remove(path)
                return True
            except OSError:
                raise ActionError('existing symlink could not be removed')
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
                return True
            except OSError:
                raise ActionError('existing directory could not be recursively removed')
        else:
            return False
