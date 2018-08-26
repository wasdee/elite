import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.brew import Brew

from .helpers import CommandMapping, build_run


def test_argument_state_invalid():
    with pytest.raises(ValueError):
        Brew(name='wget', state='hmmm')


def test_info_output_invalid(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget']
            )
        ]
    ))

    brew = Brew(name='wget', state='present')
    with pytest.raises(ActionError):
        brew.process()


def test_name_invalid(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'fake'],
                returncode=1
            )
        ]
    ))

    brew = Brew(name='fake', state='present')
    with pytest.raises(ActionError):
        brew.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget'],
                stdout_filename='brew_info_installed.stdout'
            )
        ]
    ))

    brew = Brew(name='wget', state='present')
    assert brew.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget'],
                stdout_filename='brew_info_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'install', 'wget']
            )
        ]
    ))

    brew = Brew(name='wget', state='present')
    assert brew.process() == ActionResponse(changed=True)


def test_latest_installed_and_up_to_date(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget'],
                stdout_filename='brew_info_installed.stdout'
            )
        ]
    ))

    brew = Brew(name='wget', state='latest')
    assert brew.process() == ActionResponse(changed=False)


def test_latest_installed_but_outdated(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'hugo'],
                stdout_filename='brew_info_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command=['brew', 'upgrade', 'hugo']
            )
        ]
    ))

    brew = Brew(name='hugo', state='latest')
    assert brew.process() == ActionResponse(changed=True)


def test_latest_not_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget'],
                stdout_filename='brew_info_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'install', 'wget']
            )
        ]
    ))

    brew = Brew(name='wget', state='latest')
    assert brew.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget'],
                stdout_filename='brew_info_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'remove', 'wget']
            )
        ]
    ))

    brew = Brew(name='wget', state='absent')
    assert brew.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'info', '--json=v1', 'wget'],
                stdout_filename='brew_info_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'remove', 'wget']
            )
        ]
    ))

    brew = Brew(name='wget', state='absent')
    assert brew.process() == ActionResponse(changed=True)
