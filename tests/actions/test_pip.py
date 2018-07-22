import os
import shutil

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.pip import Pip

from .helpers import CommandMapping, build_run


def test_invalid_state():
    with pytest.raises(ValueError):
        Pip(name='pycodestyle', state='hmmm')


def test_invalid_version_state_combination():
    with pytest.raises(ValueError):
        Pip(name='pycodestyle', state='latest', version='2.3.1')


def test_invalid_version_after_init():
    pip = Pip(name='pycodestyle', state='latest')
    with pytest.raises(ValueError):
        pip.version = '2.3.1'


def test_invalid_state_after_init():
    pip = Pip(name='pycodestyle', version='2.3.1')
    with pytest.raises(ValueError):
        pip.state = 'latest'


def test_invalid_virtualenv_executable_combination():
    with pytest.raises(ValueError):
        Pip(
            name='pycodestyle', executable='pip3.6',
            virtualenv='/Users/fots/.virtualenvs/myenv'
        )


def test_invalid_virtualenv_after_init():
    pip = Pip(name='pycodestyle', executable='pip3.6')
    with pytest.raises(ValueError):
        pip.virtualenv = '/Users/fots/.virtualenvs/myenv'


def test_invalid_executable_after_init():
    pip = Pip(name='pycodestyle', virtualenv='/Users/fots/.virtualenvs/myenv')
    with pytest.raises(ValueError):
        pip.executable = 'pip3.6'


def test_invalid_list_command(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                returncode=2
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present', executable='pip')
    with pytest.raises(ActionError):
        pip.process()


def test_invalid_list_output(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_invalid_output.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present', executable='pip')
    with pytest.raises(ActionError):
        pip.process()


def test_virtualenv_executable_found(monkeypatch):
    monkeypatch.setattr(
        os.path, 'exists', lambda path: path == '/Users/fots/.virtualenvs/myenv/bin/pip3'
    )
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['/Users/fots/.virtualenvs/myenv/bin/pip3', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present', virtualenv='/Users/fots/.virtualenvs/myenv')
    assert pip.process() == ActionResponse(changed=False)


def test_virtualenv_executable_not_found(monkeypatch):
    def exists(path):
        return path not in [
            '/Users/fots/.virtualenvs/myenv/bin/pip',
            '/Users/fots/.virtualenvs/myenv/bin/pip3',
            '/Users/fots/.virtualenvs/myenv/bin/pip2'
        ]

    monkeypatch.setattr(os.path, 'exists', exists)
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['/Users/fots/.virtualenvs/myenv/bin/pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present', virtualenv='/Users/fots/.virtualenvs/myenv')
    with pytest.raises(ActionError):
        pip.process()


def test_find_executable_found(monkeypatch):
    monkeypatch.setattr(
        shutil, 'which', lambda cmd: '/opt/python/bin/pip' if cmd == 'pip' else None
    )
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['/opt/python/bin/pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present')
    assert pip.process() == ActionResponse(changed=False)


def test_find_executable_not_found(monkeypatch):
    monkeypatch.setattr(shutil, 'which', lambda cmd: None)
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['/opt/python/bin/pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present')
    with pytest.raises(ActionError):
        pip.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present', executable='pip')
    assert pip.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['pip', 'install', 'pycodestyle']
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='present', executable='pip')
    assert pip.process() == ActionResponse(changed=True)


def test_present_with_version_installed_same(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', version='2.4.0', state='present', executable='pip')
    assert pip.process() == ActionResponse(changed=False)


def test_present_with_version_installed_different(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            ),
            CommandMapping(
                command=['pip', 'install', 'pycodestyle==2.3.1']
            )
        ]
    ))

    pip = Pip(name='pycodestyle', version='2.3.1', state='present', executable='pip')
    assert pip.process() == ActionResponse(changed=True)


def test_present_with_version_not_installed(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['pip', 'install', 'pycodestyle==2.4.0']
            )
        ]
    ))

    pip = Pip(name='pycodestyle', version='2.4.0', state='present', executable='pip')
    assert pip.process() == ActionResponse(changed=True)


def test_latest_installed_and_up_to_date(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            ),
            CommandMapping(
                command=['pip', 'list', '--format', 'json', '--outdated'],
                stdout_filename='pip_list_outdated_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='latest', executable='pip')
    assert pip.process() == ActionResponse(changed=False)


def test_latest_installed_but_outdated(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command=['pip', 'list', '--format', 'json', '--outdated'],
                stdout_filename='pip_list_outdated_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command=['pip', 'install', '--upgrade', 'pycodestyle']
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='latest', executable='pip')
    assert pip.process() == ActionResponse(changed=True)


def test_latest_not_installed(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['pip', 'install', 'pycodestyle']
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='latest', executable='pip')
    assert pip.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_not_installed.stdout'
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='absent', executable='pip')
    assert pip.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Pip, 'run', build_run(
        fixture_subpath='pip',
        command_mappings=[
            CommandMapping(
                command=['pip', 'list', '--format', 'json'],
                stdout_filename='pip_list_installed.stdout'
            ),
            CommandMapping(
                command=['pip', 'uninstall', '--yes', 'pycodestyle']
            )
        ]
    ))

    pip = Pip(name='pycodestyle', state='absent', executable='pip')
    assert pip.process() == ActionResponse(changed=True)
