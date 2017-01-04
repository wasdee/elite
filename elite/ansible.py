#!/usr/bin/env python3
import contextlib
from enum import Enum
import json
import os
import subprocess
import sys

from .utils import dict_to_namedtuple


class AnsibleState(Enum):
    """
    Denotes the current state of an Ansible task in a callback function.
    """
    RUNNING = 1
    OK = 2
    FAILED = 3


class Ansible(object):
    """
    Provides a way to run the requested Ansible modules with the appropriate arguments.

    :param callback: A callback function that will be called as progress occurs.
    :param module_search_paths: The paths to search for modules that should be made available in
                                addition to Ansible's core library.
    """
    def __init__(self, callback, module_search_paths=[]):
        self.callback = callback
        self.module_search_paths = module_search_paths

        self._ansible_modules = {}
        self._ansible_settings = None

        self._find_ansible_modules()

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
            :param args: Module arguments to be sent to the module.

            :return: A named tuple containing the results of the module run.
            """
            # Run the callback to indicate we have started running the task
            self.callback(
                AnsibleState.RUNNING, module, raw_params, args, self._ansible_settings,
                result=None
            )

            # Build the JSON to send to the module
            input_json = {'ANSIBLE_MODULE_ARGS': args}
            if raw_params:
                input_json['ANSIBLE_MODULE_ARGS']['_raw_params'] = raw_params

            # Run the requested module
            proc = subprocess.Popen(
                [sys.executable, self._ansible_modules[module]],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(json.dumps(input_json).encode('utf-8'))

            # Parse the result
            result = json.loads(stdout.decode('utf-8'))

            # Determine if a failure occurred and run the callback appropriately
            if result.get('rc', 0) != 0:
                result['failed'] = True

            state = AnsibleState.FAILED if result.get('failed', False) else AnsibleState.OK
            self.callback(state, module, raw_params, args, self._ansible_settings, result)

            # Return a named tuple containing the result
            return dict_to_namedtuple('Result', result)

        # Check if the module requested exists
        if module not in self._ansible_modules:
            raise AttributeError(f"the requested Ansible module '{module}' does not exist")

        # Return the sub-method for the requested module
        return _call_module

    @contextlib.contextmanager
    def settings(self, **settings):
        self._ansible_settings = settings
        yield
        self._ansible_settings = None
