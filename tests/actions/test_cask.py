import pytest

from elite.actions import ActionResponse, ActionError
from elite.actions.cask import Cask

from .helpers import CommandMapping, build_run


def test_invalid_state():
    with pytest.raises(ValueError):
        Cask(name='musescore', state='hmmm')


def test_invalid_list_output(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/present',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                returncode=1
            )
        ]
    ))

    cask = Cask(name='musescore', state='present')
    with pytest.raises(ActionError):
        cask.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/present',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_installed.stdout'
            )
        ]
    ))

    cask = Cask(name='musescore', state='present')
    assert cask.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/present',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'cask', 'install', 'musescore']
            )
        ]
    ))

    cask = Cask(name='musescore', state='present')
    assert cask.process() == ActionResponse(changed=True)


def test_latest_installed_and_up_to_date(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/latest',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_installed_and_up_to_date.stdout'
            ),
            CommandMapping(
                command='brew cask outdated',
                stdout_filename='brew_cask_outdated_and_up_to_date.stdout'
            )
        ]
    ))

    cask = Cask(name='musescore', state='latest')
    assert cask.process() == ActionResponse(changed=False)


def test_latest_installed_but_outdated(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/latest',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command='brew cask outdated',
                stdout_filename='brew_cask_outdated_outdated.stdout'
            ),
            CommandMapping(
                command=['brew', 'cask', 'upgrade', 'musescore']
            )
        ]
    ))

    cask = Cask(name='musescore', state='latest')
    assert cask.process() == ActionResponse(changed=True)


def test_latest_not_installed(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/latest',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'cask', 'install', 'musescore']
            )
        ]
    ))

    cask = Cask(name='musescore', state='latest')
    assert cask.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/absent',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'cask', 'remove', 'musescore']
            )
        ]
    ))

    cask = Cask(name='musescore', state='absent')
    assert cask.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Cask, 'run', build_run(
        fixture_subpath='cask/absent',
        command_mappings=[
            CommandMapping(
                command='brew cask list',
                stdout_filename='brew_cask_list_installed.stdout'
            ),
            CommandMapping(
                command=['brew', 'cask', 'remove', 'musescore']
            )
        ]
    ))

    cask = Cask(name='musescore', state='absent')
    assert cask.process() == ActionResponse(changed=True)
