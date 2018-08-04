import os
from collections import namedtuple
from subprocess import CompletedProcess


CommandMapping = namedtuple(
    'CommandMapping',
    ['command', 'returncode', 'stdout', 'stdout_filename', 'stderr', 'stderr_filename'],
    defaults=(0, None, None, None, None)
)


def build_run(fixture_subpath, command_mappings):
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', fixture_subpath)

    # pylint: disable=unused-argument
    def run(self, command, ignore_fail=False, fail_error=None, **kwargs):
        for (
            expected_command, expected_returncode, stdout, stdout_filename, stderr, stderr_filename
        ) in command_mappings:

            if command != expected_command:
                continue

            if stdout:
                expected_stdout = stdout
            elif stdout_filename:
                with open(os.path.join(fixture_path, stdout_filename), 'r') as fp:
                    expected_stdout = fp.read()
            else:
                expected_stdout = ''

            if stderr:
                expected_stderr = stderr
            elif stderr_filename:
                with open(os.path.join(fixture_path, stderr_filename), 'r') as fp:
                    expected_stderr = fp.read()
            else:
                expected_stderr = ''

            return CompletedProcess(
                args=command, returncode=expected_returncode,
                stdout=expected_stdout, stderr=expected_stderr
            )

        raise Exception(f'unexpected command {command} encountered')

    return run
