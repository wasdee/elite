#!/usr/bin/env python3
import ast
import os
import subprocess
import sys
from enum import Enum

from .utils import dict_to_namedtuple


class EliteState(Enum):
    """
    Denotes the current state of an Elite action.
    """

    RUNNING = 1
    OK = 2
    CHANGED = 3
    FAILED = 4


class EliteError(Exception):
    """An exception raised when an action fails to execute with the given arguments."""


class Elite:
    """
    Provides a way to run the requested Elite action with the appropriate arguments.

    :param printer: A printer object that will be used to display output.
    :param action_search_paths: The paths to search for actions that should be made available in
                                addition to Elite's core library.  Actions must be placed in the
                                sub-directory "actions" in the path provided.
    """

    def __init__(self, printer, action_search_paths=None):
        if action_search_paths is None:
            action_search_paths = []

        # Capture user parameters.
        self.printer = printer
        self.action_search_paths = action_search_paths

        # Available Elite actions and their location.
        self._elite_actions = {}
        self._find_elite_actions()

        # Capture task information to show them in the summary.
        self.ok_tasks = []
        self.failed_tasks = []
        self.changed_tasks = []

    def _find_elite_actions(self):
        """
        Determine what Elite actions are available along with their full module name.  This method
        updates self._elite_actions with a dict containing the action name as the key and the path
        as the value.  It also updates sys.path to ensure that modules can be loaded via
        python -m <full-module-name>.
        """

        # Start our list of library directories with the elite library
        library_dirs = self.action_search_paths + [os.path.join(os.path.dirname(__file__))]

        # Search through all action paths for actions
        for library_dir in library_dirs:
            # Determine the library containing the library that we will add to our syspath so that
            # Python can successfully run the module
            library_parent_dir = os.path.dirname(library_dir)
            sys.path.append(library_parent_dir)

            # Go through all files in the <module-name>/actions directory
            for root, _dirs, files in os.walk(os.path.join(library_dir, 'actions')):
                for filename in files:
                    # Obtain the file's name (which is the action name) and the extension
                    action_name, extension = os.path.splitext(filename)

                    # Skip any files that don't match *.py or start with an underscore
                    if filename.startswith('_') or extension not in ['.py']:
                        continue

                    # Determine the full module name for the action based on the path we just added
                    # to sys.path (e.g. <module-name>.actions.<action-name>)
                    action_rel_name = os.path.join(
                        os.path.relpath(root, library_parent_dir), action_name
                    )
                    action_module = action_rel_name.replace(os.sep, '.')

                    self._elite_actions[action_name] = action_module

    def __getattr__(self, action):
        """
        Provides an easy way to call any action as a method.

        :param action: The action being requested.

        :return: The respective function that implements that action.
        """

        def _call_action(sudo=False, changed=None, ignore_failed=False, env=None, **args):
            """
            A sub-method that calls the requested action with the provided raw parameters and
            arguments.

            :param sudo: Whether or not to run the action via sudo.
            :param change: A boolean that overrides whether an action changed regardless.
            :param args: Action arguments to be sent to the action.

            :return: A named tuple containing the results of the action run.
            """
            if env is None:
                env = {}

            # Run the progress callback to indicate we have started running the task
            self.printer.progress(EliteState.RUNNING, action, args, result=None)

            # Run the requested action
            # -S - read password from stdin
            # -p '<prompt>' - the prompt to display
            # -u '<user>' - the user to sudo as
            action_module = self._elite_actions[action]
            proc_args = ['sudo', '-n'] if sudo else []
            proc_args.extend([sys.executable, '-m', action_module])

            # Build the final env by merging our existing environment with provided overrides
            merged_env = os.environ.copy()
            merged_env.update(env)

            proc = subprocess.Popen(
                proc_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=merged_env
            )
            stdout, stderr = proc.communicate(repr(args).encode('utf-8'))

            # Parse the result upon successful command run
            if proc.returncode != 0 and stderr:
                result = {
                    'ok': False,
                    'message': stderr.decode('utf-8').rstrip(),
                    'return_code': proc.returncode
                }
            else:
                try:
                    result = ast.literal_eval(stdout.decode('utf-8'))
                except SyntaxError:
                    result = {
                        'ok': False,
                        'message': 'unable to parse the result returned by this action'
                    }

            if result['ok'] and changed is not None:
                result['changed'] = changed

            # Determine the final state of the task.
            if not result['ok']:
                state = EliteState.FAILED
            elif result['changed']:
                state = EliteState.CHANGED
            else:
                state = EliteState.OK

            # Run the progress callback with details of the completed task.
            self.printer.progress(state, action, args, result)

            # Update totals and task info based on the outcome
            if state == EliteState.FAILED:
                self.failed_tasks.append((action, args, result))

                # If the task failed and was not to be ignored, we bail.
                if not ignore_failed:
                    raise EliteError(result['message'])
            elif result['changed']:
                self.changed_tasks.append((action, args, result))
            else:
                self.ok_tasks.append((action, args, result))

            # Return a named tuple containing the result
            return dict_to_namedtuple('Result', result)

        # Check if the action requested exists
        if action not in self._elite_actions:
            raise AttributeError(f"the requested Elite action '{action}' does not exist")

        # Return the sub-method for the requested action
        return _call_action

    def summary(self):
        """
        Call the summary printer object method with the appropriate totals and task info so the
        method may display the final summary to the user.
        """
        self.printer.summary(self.ok_tasks, self.changed_tasks, self.failed_tasks)
