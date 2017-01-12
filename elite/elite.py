#!/usr/bin/env python3
from enum import Enum
import json
import os
import shutil
import subprocess
import sys

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


class Elite(object):
    """
    Provides a way to run the requested Elite action with the appropriate arguments.

    :param printer: A printer object that will be used to display output.
    :param action_search_paths: The paths to search for actions that should be made available in
                                addition to Elite's core library.
    """
    def __init__(self, printer, action_search_paths=[]):
        # Capture user parameters.
        self.printer = printer
        self.action_search_paths = action_search_paths

        # Available Elite actions and their location.
        self._elite_actions = {}
        self._find_elite_actions()

        # Keep track of totals for the summary.
        self.total_tasks = 0
        self.ok_tasks = 0
        self.changed_tasks = 0
        self.failed_tasks = 0

        # Capture failud and changed tasks to show them in the summary.
        self.failed_task_info = []
        self.changed_task_info = []

    def _find_elite_actions(self):
        """
        Determine what Elite actions are available along with their full path.  This method
        updates self._elite_actions with a dict containing the action name as the key and the path
        as the value.
        """
        # Find the Elite core actions directory
        actions_base = os.path.join(os.path.dirname(__file__), 'actions')

        # Search through all action paths for actions
        for search_path in [actions_base] + self.action_search_paths:
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    # Skip any files that don't match *.py or start with an underscore
                    extension = os.path.splitext(filename)
                    if extension[1] != '.py' or filename.startswith('_'):
                        continue

                    # Add the action to our dict
                    action_name = filename[:-3]
                    action_path = os.path.join(root, filename)
                    self._elite_actions[action_name] = action_path

    def __getattr__(self, action):
        """
        Provides an easy way to call any action as a method.

        :param action: The action being requested.

        :return: The respective function that implements that action.
        """
        def _call_action(sudo=False, ok=None, changed=None, ignore_failed=False, **args):
            """
            A sub-method that calls the requested action with the provided raw parameters and
            arguments.

            :param sudo: Whether or not to run the action via sudo.
            :param ok: A boolean which overrides the success of an action regardless.
            :param change: A boolean that overrides whether an action changed regardless.
            :param args: Action arguments to be sent to the action.

            :return: A named tuple containing the results of the action run.
            """
            # Track the number of tasks run
            self.total_tasks += 1

            # Run the progress callback to indicate we have started running the task
            self.printer.progress(EliteState.RUNNING, action, args, result=None)

            # Run the requested action
            # -S - read password from stdin
            # -p '<prompt>' - the prompt to display
            # -u '<user>' - the user to sudo as
            cwd = os.path.dirname(os.path.dirname(self._elite_actions[action]))
            module = self._elite_actions[action].split(cwd)[-1][1:-3].replace('/', '.')
            proc_args = [shutil.which('sudo'), '-n'] if sudo else []
            proc_args.extend([sys.executable, '-m', module])

            proc = subprocess.Popen(
                proc_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = proc.communicate(json.dumps(args).encode('utf-8'))

            # Parse the result upon successful command run
            if proc.returncode != 0 and stderr:
                result = {
                    'ok': False,
                    'message': stderr.decode('utf-8').strip(),
                    'return_code': proc.returncode
                }
            else:
                result = json.loads(stdout.decode('utf-8'))

            if result['ok'] and changed is not None:
                result['changed'] = changed

            # Determine the final state of the task.
            if not result['ok']:
                state = EliteState.FAILED
            elif result["changed"]:
                state = EliteState.CHANGED
            else:
                state = EliteState.OK

            # Run the progress callback with details of the completed task.
            self.printer.progress(state, action, args, result)

            # Update totals and task info based on the outcome
            if state == EliteState.FAILED:
                self.failed_tasks += 1
                self.failed_task_info.append((action, args, result))

                # If the task failed and was not to be ignored, we bail.
                if not ignore_failed:
                    raise EliteError(result['message'])
            elif result['changed']:
                self.changed_tasks += 1
                self.changed_task_info.append((action, args, result))
            else:
                self.ok_tasks += 1

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
        self.printer.summary(
            self.total_tasks, self.ok_tasks,
            self.changed_tasks, self.failed_tasks,
            self.changed_task_info, self.failed_task_info
        )
