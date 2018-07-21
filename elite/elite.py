import os
import pwd
from collections import namedtuple
from contextlib import contextmanager
from enum import Enum

from .actions import ActionError
from .actions.archive import Archive
from .actions.brew import Brew
from .actions.brew_update import BrewUpdate
from .actions.cask import Cask
from .actions.dock import Dock
from .actions.download import Download
from .actions.fail import Fail
from .actions.file import File
from .actions.file_info import FileInfo
from .actions.find import Find
from .actions.gem import Gem
from .actions.git import Git
from .actions.handler import Handler
from .actions.hostname import Hostname
from .actions.info import Info
from .actions.json import JSON
from .actions.launchpad import Launchpad
from .actions.login_item import LoginItem
from .actions.npm import NPM
from .actions.package import Package
from .actions.package_choices import PackageChoices
from .actions.pip import Pip
from .actions.plist import Plist
from .actions.rsync import Rsync
from .actions.run import Run
from .actions.spotify import Spotify
from .actions.system_setup import SystemSetup
from .actions.tap import Tap


EliteResponse = namedtuple(
    'EliteResponse', ['changed', 'ok', 'data', 'failed_message'], defaults=(True, {}, None)
)
Options = namedtuple('Options', ['uid', 'gid', 'changed', 'ignore_failed'])


def demote(uid, gid):
    def demoter():
        os.setegid(0)
        os.seteuid(0)
        os.setgid(gid)
        os.setuid(uid)
        os.setegid(gid)
        os.seteuid(uid)

    return demoter


class EliteState(Enum):
    """Denotes the current state of an Elite action."""

    RUNNING = 1
    OK = 2
    CHANGED = 3
    FAILED = 4


class EliteError(Exception):
    """An exception raised when an action fails to execute with the given arguments."""


class EliteRuntimeError(EliteError):
    pass


class Elite:
    """
    Provides a way to run the requested Elite action with the appropriate arguments.

    :param printer: A printer object that will be used to display output.
    """

    def __init__(self, printer):
        self.printer = printer
        self.actions = {}

        if (
            'SUDO_USER' not in os.environ or
            'SUDO_UID' not in os.environ or
            'SUDO_GID' not in os.environ or
            os.environ['SUDO_USER'] == 'root' or
            os.environ['SUDO_UID'] == '0' or
            os.environ['SUDO_GID'] == '0' or
            (os.getuid() != 0 and os.getgid() != 0)
        ):
            raise EliteRuntimeError('elite must be run using sudo via a regular user account')

        try:
            self.user_uid = int(os.environ['SUDO_UID'])
            self.user_gid = int(os.environ['SUDO_GID'])
        except ValueError:
            raise EliteRuntimeError('The sudo uid and/or gids contain an invalid value')

        self.current_options = Options(
            uid=self.user_uid, gid=self.user_gid, changed=None, ignore_failed=None
        )

        # Copy root's environment variables for future use
        self.root_env = os.environ.copy()

        # Build the user's environment using various details
        user = pwd.getpwuid(self.user_uid)
        self.user_env = os.environ.copy()
        self.user_env.update({
            'USER': user.pw_name,
            'LOGNAME': user.pw_name,
            'HOME': user.pw_dir,
            'SHELL': user.pw_shell,
            'PWD': os.getcwd()
        })
        for key in ['OLDPWD', 'USERNAME', 'MAIL']:
            self.user_env.pop(key, None)

        # Set effective permissions and environment to that of the calling user (demotion)
        self._switch_to_user()

        # Register the core actions provided with Elite
        self._register_core_actions()

        # Capture task information to show them in the summary.
        self.tasks = {
            EliteState.OK: [],
            EliteState.FAILED: [],
            EliteState.CHANGED: []
        }

    def register_action(self, action_name, action_class):
        """
        Registers a new action given its name and class.

        :param action_name: the action name to be registered
        :param action_class: the class that implements the action being added
        """

        if action_name in self.actions:
            raise ValueError(f'the action {action_name} is already registered')

        self.actions[action_name] = action_class

    def _register_core_actions(self):
        """Registers the core Elite actions that are included with the library."""
        self.register_action('archive', Archive)
        self.register_action('brew', Brew)
        self.register_action('brew_update', BrewUpdate)
        self.register_action('cask', Cask)
        self.register_action('dock', Dock)
        self.register_action('download', Download)
        self.register_action('fail', Fail)
        self.register_action('file', File)
        self.register_action('file_info', FileInfo)
        self.register_action('find', Find)
        self.register_action('gem', Gem)
        self.register_action('git', Git)
        self.register_action('handler', Handler)
        self.register_action('hostname', Hostname)
        self.register_action('info', Info)
        self.register_action('json', JSON)
        self.register_action('launchpad', Launchpad)
        self.register_action('login_item', LoginItem)
        self.register_action('npm', NPM)
        self.register_action('package', Package)
        self.register_action('package_choices', PackageChoices)
        self.register_action('pip', Pip)
        self.register_action('plist', Plist)
        self.register_action('rsync', Rsync)
        self.register_action('run', Run)
        self.register_action('spotify', Spotify)
        self.register_action('system_setup', SystemSetup)
        self.register_action('tap', Tap)

    def _switch_to_root(self):
        os.environ.clear()
        os.environ.update(self.root_env)
        os.setegid(0)
        os.seteuid(0)

    def _switch_to_user(self, currently_root=False):
        os.environ.clear()
        os.environ.update(self.user_env)
        if currently_root:
            os.setegid(self.user_gid)
            os.seteuid(self.user_uid)

    @contextmanager
    def options(self, sudo=False, changed=None, ignore_failed=None, env=None):
        # Switch to root if necessary and update options to the current values
        if sudo:
            self._switch_to_root()
            self.current_options = Options(
                uid=0, gid=0, changed=changed, ignore_failed=ignore_failed
            )
        else:
            self.current_options = Options(
                uid=self.user_uid, gid=self.user_gid, changed=changed, ignore_failed=ignore_failed
            )

        # Add any additionally provided environment  variables
        os.environ.update(env if env is not None else {})

        yield

        # Revert back to user permissions and reset options
        self._switch_to_user(currently_root=sudo)
        self.current_options = Options(
            uid=self.user_uid, gid=self.user_gid, changed=None, ignore_failed=None
        )

    def __getattr__(self, action_name):
        """
        Provides an easy way to call any action as a method.

        :param action: The action being requested.

        :return: The respective function that implements that action.
        """

        def _run_action(*args, **kwargs):
            """
            A sub-method that calls the requested action with the provided raw parameters and
            arguments.

            :param sudo: Whether or not to run the action via sudo.
            :param change: A boolean that overrides whether an action changed regardless.
            :param args: Action arguments to be sent to the action.

            :return: A named tuple containing the results of the action run.
            """
            # Run the progress callback to indicate we have started running the task
            self.printer.progress(EliteState.RUNNING, action_name, kwargs, response=None)

            # Run the requested action
            Action = self.actions[action_name]  # noqa: N806
            action = Action(
                *args, **kwargs,
                preexec_callback=demote(self.current_options.uid, self.current_options.gid)
            )

            try:
                action_response = action.process()

                if self.current_options.changed is None:
                    changed = action_response.changed
                else:
                    changed = self.current_options.changed

                elite_response = EliteResponse(changed=changed, ok=True, data=action_response.data)
                state = EliteState.CHANGED if changed else EliteState.OK
            except ActionError as e:
                elite_response = EliteResponse(
                    changed=False, ok=False, failed_message=str(e) if e.args else None
                )
                state = EliteState.FAILED

            # Run the progress callback with details of the completed task.
            self.printer.progress(state, action_name, kwargs, elite_response)

            # Update task info based on the outcome
            self.tasks[state].append((action_name, kwargs, elite_response))

            # If the task failed and was not to be ignored, we bail.
            if state == EliteState.FAILED and not self.current_options.ignore_failed:
                raise EliteError(elite_response.failed_message)

            return elite_response

        # Check if the action requested exists
        if action_name not in self.actions:
            raise AttributeError(f"the requested Elite action '{action_name}' does not exist")

        # Return the sub-method for the requested action
        return _run_action

    def summary(self):
        """
        Call the summary printer object method with the appropriate totals and task info so the
        method may display the final summary to the user.
        """
        self.printer.summary(self.tasks)
