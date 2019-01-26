from unittest import mock

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.go import Go

from .helpers import CommandMapping, build_run


def test_argument_state_invalid():
    with pytest.raises(ValueError):
        Go(name='github.com/gin-gonic/gin', state='hmmm')


def test_command_invalid(monkeypatch):
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                returncode=2
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='present')
    with pytest.raises(ActionError):
        go.process()


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                stdout_filename='go_list_installed.stdout'
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='present')
    assert go.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                stdout_filename='go_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['go', 'get', 'github.com/gin-gonic/gin']
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='present')
    assert go.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                stdout_filename='go_list_not_installed.stdout'
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='absent')
    assert go.process() == ActionResponse(changed=False)


@mock.patch('shutil.rmtree')
def test_absent_installed(rmtree_mock, monkeypatch):
    monkeypatch.delenv('GOPATH', raising=False)
    monkeypatch.setenv('USER', 'fots')
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                stdout_filename='go_list_installed.stdout'
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='absent')
    assert go.process() == ActionResponse(changed=True)
    assert rmtree_mock.call_args_list == [mock.call('/Users/fots/go/src/github.com/gin-gonic/gin')]


@mock.patch('shutil.rmtree')
def test_absent_installed_custom_go_path(rmtree_mock, monkeypatch):
    monkeypatch.setenv('GOPATH', '/programming/gostuff')
    monkeypatch.setenv('USER', 'mario')
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                stdout_filename='go_list_installed.stdout'
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='absent')
    assert go.process() == ActionResponse(changed=True)
    assert rmtree_mock.call_args_list == [
        mock.call('/programming/gostuff/src/github.com/gin-gonic/gin')
    ]


def test_absent_installed_not_writable(monkeypatch):
    def rmtree(path):  # pylint: disable=unused-argument
        raise PermissionError(13, 'Permission denied', path)

    monkeypatch.setattr('shutil.rmtree', rmtree)
    monkeypatch.setattr(Go, 'run', build_run(
        fixture_subpath='go',
        command_mappings=[
            CommandMapping(
                command=['go', 'list', 'all'],
                stdout_filename='go_list_installed.stdout'
            )
        ]
    ))

    go = Go(name='github.com/gin-gonic/gin', state='absent')
    with pytest.raises(ActionError):
        go.process()
