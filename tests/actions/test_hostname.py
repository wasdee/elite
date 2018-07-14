from elite.actions import ActionResponse
from elite.actions.hostname import Hostname

from .helpers import CommandMapping, build_run


def test_local_host_name_same(monkeypatch):
    monkeypatch.setattr(Hostname, 'run', build_run(
        fixture_subpath='hostname',
        command_mappings=[
            CommandMapping(
                command='scutil --get LocalHostName',
                stdout_filename='systemsetup_local_host_name_same.stdout'
            )
        ]
    ))

    hostname = Hostname(local_host_name='Fotsies-MacBook-Pro')
    assert hostname.process() == ActionResponse(changed=False)


def test_local_host_name_different(monkeypatch):
    monkeypatch.setattr(Hostname, 'run', build_run(
        fixture_subpath='hostname',
        command_mappings=[
            CommandMapping(
                command='scutil --get LocalHostName',
                stdout_filename='systemsetup_local_host_name_different.stdout'
            ),
            CommandMapping(
                command='scutil --set LocalHostName "Fotsies-MacBook-Pro"'
            )
        ]
    ))

    hostname = Hostname(local_host_name='Fotsies-MacBook-Pro')
    assert hostname.process() == ActionResponse(changed=True)


def test_computer_name_same(monkeypatch):
    monkeypatch.setattr(Hostname, 'run', build_run(
        fixture_subpath='hostname',
        command_mappings=[
            CommandMapping(
                command='scutil --get ComputerName',
                stdout_filename='systemsetup_computer_name_same.stdout'
            )
        ]
    ))

    hostname = Hostname(computer_name='Fotsies MacBook Pro')
    assert hostname.process() == ActionResponse(changed=False)


def test_computer_name_different(monkeypatch):
    monkeypatch.setattr(Hostname, 'run', build_run(
        fixture_subpath='hostname',
        command_mappings=[
            CommandMapping(
                command='scutil --get ComputerName',
                stdout_filename='systemsetup_computer_name_different.stdout'
            ),
            CommandMapping(
                command='scutil --set ComputerName "Fotsies MacBook Pro"'
            )
        ]
    ))

    hostname = Hostname(computer_name='Fotsies MacBook Pro')
    assert hostname.process() == ActionResponse(changed=True)
