from elite.actions import ActionResponse
from elite.actions.system_setup import SystemSetup

from .helpers import CommandMapping, build_run


def test_timezone_same(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-gettimezone'],
                stdout_filename='systemsetup_timezone_same.stdout'
            )
        ]
    ))

    system_setup = SystemSetup(timezone='Australia/Brisbane')
    assert system_setup.process() == ActionResponse(changed=False)


def test_timezone_different(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-gettimezone'],
                stdout_filename='systemsetup_timezone_different.stdout'
            ),
            CommandMapping(
                command=['systemsetup', '-settimezone', 'Australia/Brisbane']
            )
        ]
    ))

    system_setup = SystemSetup(timezone='Australia/Brisbane')
    assert system_setup.process() == ActionResponse(changed=True)


def test_computer_sleep_time_same(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-getcomputersleep'],
                stdout_filename='systemsetup_computer_sleep_same.stdout'
            )
        ]
    ))

    system_setup = SystemSetup(computer_sleep_time=5)
    assert system_setup.process() == ActionResponse(changed=False)


def test_computer_sleep_time_different(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-getcomputersleep'],
                stdout_filename='systemsetup_computer_sleep_different.stdout'
            ),
            CommandMapping(
                command=['systemsetup', '-setcomputersleep', 5]
            )
        ]
    ))

    system_setup = SystemSetup(computer_sleep_time=5)
    assert system_setup.process() == ActionResponse(changed=True)


def test_display_sleep_time_same(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-getdisplaysleep'],
                stdout_filename='systemsetup_display_sleep_same.stdout'
            )
        ]
    ))

    system_setup = SystemSetup(display_sleep_time=10)
    assert system_setup.process() == ActionResponse(changed=False)


def test_display_sleep_time_different(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-getdisplaysleep'],
                stdout_filename='systemsetup_display_sleep_different.stdout'
            ),
            CommandMapping(
                command=['systemsetup', '-setdisplaysleep', 10]
            )
        ]
    ))

    system_setup = SystemSetup(display_sleep_time=10)
    assert system_setup.process() == ActionResponse(changed=True)


def test_hard_disk_sleep_time_same(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-getharddisksleep'],
                stdout_filename='systemsetup_hard_disk_sleep_same.stdout'
            )
        ]
    ))

    system_setup = SystemSetup(hard_disk_sleep_time=15)
    assert system_setup.process() == ActionResponse(changed=False)


def test_hard_disk_sleep_time_different(monkeypatch):
    monkeypatch.setattr(SystemSetup, 'run', build_run(
        fixture_subpath='system_setup',
        command_mappings=[
            CommandMapping(
                command=['systemsetup', '-getharddisksleep'],
                stdout_filename='systemsetup_hard_disk_sleep_different.stdout'
            ),
            CommandMapping(
                command=['systemsetup', '-setharddisksleep', 15]
            )
        ]
    ))

    system_setup = SystemSetup(hard_disk_sleep_time=15)
    assert system_setup.process() == ActionResponse(changed=True)
