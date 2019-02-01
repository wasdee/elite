import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.brew import Brew

from .helpers import CommandMapping, build_run


def test_argument_state_invalid():
    with pytest.raises(ValueError):
        Brew(name='youtube-dl', state='hmmm')


def test_list_output_invalid(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                returncode=1
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='present')
    with pytest.raises(ActionError):
        brew.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_installed.stdout'
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='present')
    assert brew.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'install', 'youtube-dl']
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='present')
    assert brew.process() == ActionResponse(changed=True)


def test_latest_installed_and_up_to_date(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'outdated', '--json=v1'],
                stdout_filename='brew_outdated_up_to_date.stdout'
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='latest')
    assert brew.process() == ActionResponse(changed=False)


def test_latest_installed_but_outdated(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'outdated', '--json=v1'],
                stdout_filename='brew_outdated_outdated.stdout'
            ),
            CommandMapping(
                command=['brew', 'upgrade', 'youtube-dl']
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='latest')
    assert brew.process() == ActionResponse(changed=True)


def test_latest_not_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'install', 'youtube-dl']
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='latest')
    assert brew.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'remove', 'youtube-dl']
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='absent')
    assert brew.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Brew, 'run', build_run(
        fixture_subpath='brew',
        command_mappings=[
            CommandMapping(
                command=['brew', 'list'],
                stdout_filename='brew_list_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'remove', 'youtube-dl']
            )
        ]
    ))

    brew = Brew(name='youtube-dl', state='absent')
    assert brew.process() == ActionResponse(changed=True)
