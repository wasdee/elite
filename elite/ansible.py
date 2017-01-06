#!/usr/bin/env python3
import contextlib
from enum import Enum
import json
import os
import random
import shutil
import subprocess
import sys
import time

from .utils import dict_to_namedtuple


class AnsibleState(Enum):
    """
    Denotes the current state of an Ansible task.
    """
    RUNNING = 1
    OK = 2
    CHANGED = 3
    FAILED = 4


class AnsibleError(Exception):
    """An exception raised when a module fails to execute with the given arguments."""


class Ansible(object):
    """
    Provides a way to run the requested Ansible modules with the appropriate arguments.

    :param printer: A printer object that will be used to display output.
    :param module_search_paths: The paths to search for modules that should be made available in
                                addition to Ansible's core library.
    """
    def __init__(self, printer, module_search_paths=[]):
        # Capture user parameters.
        self.printer = printer
        self.module_search_paths = module_search_paths

        # Available Ansible modules and their location.
        self._ansible_modules = {}
        self._find_ansible_modules()

        # Store Ansible settings the user has provided (e.g. sudo).
        self._ansible_settings = {}

        # Keep track of totals for the summary.
        self.total_tasks = 0
        self.ok_tasks = 0
        self.changed_tasks = 0
        self.failed_tasks = 0

        # Capture failud and changed tasks to show them in the summary.
        self.failed_task_info = []
        self.changed_task_info = []

        # Create a temporary location to store Ansible modules as they don't run
        # well in their installed location (primarily due to copy.py conflicting with Python's
        # copy library).
        self._tempdir = os.path.expanduser(os.path.join(
            '~', '.ansible', 'tmp', f'ansible-tmp-{time.time()}-{random.randint(0, 2**48)}'
        ))
        os.makedirs(self._tempdir)

    def cleanup(self):
        """
        Clean up any files contained in the temp directory we're using.
        """
        shutil.rmtree(self._tempdir)

    def _find_ansible_modules(self):
        """
        Determine what Ansible modules are available along with their full path.  This method
        updates self.modules with a dict containing the module name as the key and the path as
        the value.
        """
        # Find the Ansible core modules directory
        import ansible
        modules_base = os.path.join(os.path.dirname(ansible.__file__), 'modules')

        # Search through all module paths for modules
        for search_path in [modules_base] + self.module_search_paths:
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    # Skip any files that don't match *.py or start with an underscore
                    extension = os.path.splitext(filename)
                    if extension[1] != '.py' or filename.startswith('_'):
                        continue

                    # Add the module to our dict
                    module_name = filename[:-3]
                    module_path = os.path.join(root, filename)
                    self._ansible_modules[module_name] = module_path

    def __getattr__(self, module):
        """
        Provides an easy way to call any module as a method.

        :param module: The module being requested.

        :return: The respective function that implements that module.
        """
        def _call_module(raw_params=None, sudo=False, **args):
            """
            A sub-method that calls the requested module with the provided raw parameters and
            arguments.

            :param raw_params: Raw parameters (used for command and shell modules).
            :param args: Module arguments to be sent to the module.  You may add an underscore
                         suffix in case a module argument conflicts with a Python keyword
                         (e.g. the global argument in the npm module).

            :return: A named tuple containing the results of the module run.
            """
            # Replace any keys containing a underscore sufix
            keys_to_replace = [k for k in args.keys() if k.endswith('_')]
            for key in keys_to_replace:
                args[key[:-1]] = args[key]
                del args[key]

            # Track the number of tasks run
            self.total_tasks += 1

            # Run the progress callback to indicate we have started running the task
            self.printer.progress(
                AnsibleState.RUNNING, module, raw_params, args, self._ansible_settings,
                result=None
            )

            # Build the JSON to send to the module
            input_json = {'ANSIBLE_MODULE_ARGS': args}
            if raw_params:
                input_json['ANSIBLE_MODULE_ARGS']['_raw_params'] = raw_params

            # Copy the module to our temporary directory
            temp_module_path = shutil.copy(self._ansible_modules[module], self._tempdir)

            # Run the requested module
            sudo = self._ansible_settings.get('sudo', False)
            proc_args = [shutil.which('sudo'), '-n'] if sudo else []
            proc_args.extend([sys.executable, temp_module_path])

            proc = subprocess.Popen(
                proc_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(json.dumps(input_json).encode('utf-8'))

            # Delete the module that was copied
            os.remove(temp_module_path)

            # Parse the result upon successful command run
            if proc.returncode != 0 and stderr:
                result = {
                    'msg': stderr.decode('utf-8').strip(),
                    'rc': proc.returncode
                }
            else:
                result = json.loads(stdout.decode('utf-8'))

            # Determine if a failure occurred and add the failed and msg attributes if required.
            if result.get('rc', 0) != 0:
                result['failed'] = True
                if 'msg' not in result:
                    result['msg'] = result['stderr']

            # Determine the final state of the task.
            if result.get('failed', False):
                state = AnsibleState.FAILED
            elif result["changed"]:
                state = AnsibleState.CHANGED
            else:
                state = AnsibleState.OK

            # Run the progress callback with details of the completed task.
            self.printer.progress(state, module, raw_params, args, self._ansible_settings, result)

            # Update totals and task info based on the outcome
            if state == AnsibleState.FAILED:
                self.failed_tasks += 1
                self.failed_task_info.append(
                    (module, raw_params, args, self._ansible_settings, result)
                )

                # If the task failed and was not to be ignored, we bail.
                if not self._ansible_settings.get('ignore_errors', False):
                    raise AnsibleError(result['msg'])
            elif result['changed']:
                self.changed_tasks += 1
                self.changed_task_info.append(
                    (module, raw_params, args, self._ansible_settings, result)
                )
            else:
                self.ok_tasks += 1

            # Return a named tuple containing the result
            return dict_to_namedtuple('Result', result)

        # Check if the module requested exists
        if module not in self._ansible_modules:
            raise AttributeError(f"the requested Ansible module '{module}' does not exist")

        # Return the sub-method for the requested module
        return _call_module

    @contextlib.contextmanager
    def settings(self, **settings):
        """
        A simple contaext manager allowing the user to override settings for a set of tasks.

        :param settings: Settings to override (sudo, ignore_errors, changed and failed
                         each may be provided as booleans).
        """
        self._ansible_settings = settings
        yield
        self._ansible_settings = {}

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
