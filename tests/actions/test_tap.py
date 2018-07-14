import pytest

from elite.actions import ActionResponse, ActionError
from elite.actions.tap import Tap

from .helpers import CommandMapping, build_run


def test_invalid_state():
    with pytest.raises(ValueError):
        Tap(name='homebrew/cask-fonts', state='hmmm')


def test_invalid_command(monkeypatch):
    monkeypatch.setattr(Tap, 'run', build_run(
        fixture_subpath='tap',
        command_mappings=[
            CommandMapping(
                command='brew tap',
                returncode=2
            )
        ]
    ))

    tap = Tap(name='homebrew/cask-fonts', state='present')
    with pytest.raises(ActionError):
        tap.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Tap, 'run', build_run(
        fixture_subpath='tap',
        command_mappings=[
            CommandMapping(
                command='brew tap',
                stdout_filename='brew_tap_tapped.stdout'
            )
        ]
    ))

    tap = Tap(name='homebrew/cask-fonts', state='present')
    assert tap.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Tap, 'run', build_run(
        fixture_subpath='tap',
        command_mappings=[
            CommandMapping(
                command='brew tap',
                stdout_filename='brew_tap_untapped.stdout'
            ),
            CommandMapping(
                command=['brew', 'tap', 'homebrew/cask-fonts']
            )
        ]
    ))

    tap = Tap(name='homebrew/cask-fonts', state='present')
    assert tap.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Tap, 'run', build_run(
        fixture_subpath='tap',
        command_mappings=[
            CommandMapping(
                command='brew tap',
                stdout_filename='brew_tap_untapped.stdout'
            ),
            CommandMapping(
                command=['brew', 'untap', 'homebrew/cask-fonts']
            )
        ]
    ))

    tap = Tap(name='homebrew/cask-fonts', state='absent')
    assert tap.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Tap, 'run', build_run(
        fixture_subpath='tap',
        command_mappings=[
            CommandMapping(
                command='brew tap',
                stdout_filename='brew_tap_tapped.stdout'
            ),
            CommandMapping(
                command=['brew', 'untap', 'homebrew/cask-fonts']
            )
        ]
    ))

    tap = Tap(name='homebrew/cask-fonts', state='absent')
    assert tap.process() == ActionResponse(changed=True)
