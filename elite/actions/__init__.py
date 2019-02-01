import grp
import hashlib
import os
import pickle
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

    :param cache_base_dir: the base directory containing the Elite cache or None to disable caching
    :param preexec_fn: the function to call prior exec of commands that are run
    """

    def __init__(self, cache_base_dir=None, preexec_fn=None):
        self.cache_base_dir = cache_base_dir
        self.preexec_fn = preexec_fn

    @property
    def cache_dir(self):
        if self.cache_base_dir:
            return os.path.join(self.cache_base_dir, self.__class__.__name__)
        else:
            return None

    def ok(self, **data):
        return ActionResponse(changed=False, data=data)

    def changed(self, **data):
        if self.cache_dir and os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        return ActionResponse(changed=True, data=data)

    def run(self, command, ignore_fail=False, fail_error=None, cache=False, **kwargs):
        # Determine the cache path based on the command and return the cached item if it exists
        if self.cache_dir:
            command_bytes = b' '.join(a.encode('utf-8') for a in command)
            cache_path = os.path.join(self.cache_dir, hashlib.md5(command_bytes).hexdigest())

            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as fp:
                    return pickle.load(fp)

        # Allow for the user to simply set stdout to a bool to enable them
        if kwargs.get('stdout'):
            kwargs['stdout'] = subprocess.PIPE
        else:
            kwargs['stdout'] = devnull

        # Allow for a bool to enable stderr or enable it anyway if the command will fail on
        # error and no message has been provided
        if kwargs.get('stderr') or not ignore_fail:
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
                if process.stderr:
                    raise ActionError(f'{fail_error}: {process.stderr.rstrip()}')
                else:
                    raise ActionError(fail_error)
            elif process.stderr:
                raise ActionError(process.stderr.rstrip())
            else:
                raise ActionError(f'unable to execute command {command}')

        # Cache the output of the command if required
        if self.cache_dir and cache:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(cache_path, 'wb') as fp:
                pickle.dump(process, fp)

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
