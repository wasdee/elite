import shutil

import pytest

from elite.actions import ActionResponse, ActionError
from elite.actions.gem import Gem

from .helpers import CommandMapping, build_run


def test_invalid_state():
    with pytest.raises(ValueError):
        Gem(name='rails', state='hmmm')


def test_invalid_version_state_combination():
    with pytest.raises(ValueError):
        Gem(name='rails', state='latest', version='5.2.0')


def test_invalid_version_after_init():
    gem = Gem(name='rails', state='latest')
    with pytest.raises(ValueError):
        gem.version = '5.2.0'


def test_invalid_state_after_init():
    gem = Gem(name='rails', version='5.2.0')
    with pytest.raises(ValueError):
        gem.state = 'latest'


def test_invalid_specification_output(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_invalid_output.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', state='present', executable='gem')
    with pytest.raises(ActionError):
        gem.process()


def test_find_executable_found(monkeypatch):
    monkeypatch.setattr(
        shutil, 'which', lambda cmd: '/opt/ruby/bin/gem' if cmd == 'gem' else None
    )
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['/opt/ruby/bin/gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', state='present')
    assert gem.process() == ActionResponse(changed=False)


def test_find_executable_not_found(monkeypatch):
    monkeypatch.setattr(shutil, 'which', lambda cmd: None)
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['/opt/ruby/bin/gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', state='present')
    with pytest.raises(ActionError):
        gem.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', state='present', executable='gem')
    assert gem.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                returncode=1
            ),
            CommandMapping(
                command=['gem', 'install', 'rails']
            )
        ]
    ))

    gem = Gem(name='rails', state='present', executable='gem')
    assert gem.process() == ActionResponse(changed=True)


def test_present_with_version_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', version='5.2.0', state='present', executable='gem')
    assert gem.process() == ActionResponse(changed=False)


def test_present_with_version_not_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                returncode=1
            ),
            CommandMapping(
                command=['gem', 'install', '--version', '5.1.6', 'rails']
            )
        ]
    ))

    gem = Gem(name='rails', version='5.1.6', state='present', executable='gem')
    assert gem.process() == ActionResponse(changed=True)


def test_latest_installed_and_up_to_date(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            ),
            CommandMapping(
                command=['gem', 'specification', '--remote', 'rails'],
                stdout_filename='gem_specification_remote.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', state='latest', executable='gem')
    assert gem.process() == ActionResponse(changed=False)


def test_latest_installed_but_outdated(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command=['gem', 'specification', '--remote', 'rails'],
                stdout_filename='gem_specification_remote.stdout'
            ),
            CommandMapping(
                command=['gem', 'install', 'rails']
            )
        ]
    ))

    gem = Gem(name='rails', state='latest', executable='gem')
    assert gem.process() == ActionResponse(changed=True)


def test_latest_not_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                returncode=1
            ),
            CommandMapping(
                command=['gem', 'install', 'rails']
            )
        ]
    ))

    gem = Gem(name='rails', state='latest', executable='gem')
    assert gem.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                returncode=1
            )
        ]
    ))

    gem = Gem(name='rails', state='absent', executable='gem')
    assert gem.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            ),
            CommandMapping(
                command=['gem', 'uninstall', '--all', '--executables', 'rails']
            )
        ]
    ))

    gem = Gem(name='rails', state='absent', executable='gem')
    assert gem.process() == ActionResponse(changed=True)


def test_absent_with_version_not_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                returncode=1
            )
        ]
    ))

    gem = Gem(name='rails', version='5.1.6', state='absent', executable='gem')
    assert gem.process() == ActionResponse(changed=False)


def test_absent_with_version_installed_other_version(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            )
        ]
    ))

    gem = Gem(name='rails', version='5.1.6', state='absent', executable='gem')
    assert gem.process() == ActionResponse(changed=False)


def test_absent_with_version_installed(monkeypatch):
    monkeypatch.setattr(Gem, 'run', build_run(
        fixture_subpath='gem',
        command_mappings=[
            CommandMapping(
                command=['gem', 'specification', '--all', 'rails'],
                stdout_filename='gem_specification_all_installed.stdout'
            ),
            CommandMapping(
                command=['gem', 'uninstall', '--version', '5.2.0', '--executables', 'rails']
            )
        ]
    ))

    gem = Gem(name='rails', version='5.2.0', state='absent', executable='gem')
    assert gem.process() == ActionResponse(changed=True)
