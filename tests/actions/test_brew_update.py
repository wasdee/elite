from elite.actions import ActionResponse
from elite.actions.brew_update import BrewUpdate

from .helpers import CommandMapping, build_run


def test_up_to_date(monkeypatch):
    monkeypatch.setattr(BrewUpdate, 'run', build_run(
        fixture_subpath='brew_update',
        command_mappings=[
            CommandMapping(
                command=['brew', 'update'],
                stdout_filename='brew_update_up_to_date.stdout'
            )
        ]
    ))

    brew_update = BrewUpdate()
    assert brew_update.process() == ActionResponse(changed=False)


def test_outdated(monkeypatch):
    monkeypatch.setattr(BrewUpdate, 'run', build_run(
        fixture_subpath='brew_update',
        command_mappings=[
            CommandMapping(
                command=['brew', 'update'],
                stdout_filename='brew_update_outdated.stdout'
            )
        ]
    ))

    brew_update = BrewUpdate()
    assert brew_update.process() == ActionResponse(changed=True)
