import os
from unittest import mock

import pytest
from elite.actions import Action, ActionError
from elite.elite import Elite, EliteError, EliteResponse, demote

from . import helpers


class Printer:
    def action(self, state, action, args, response=None):
        pass

    def summary(self, actions):
        pass


def test_elite_not_run_as_root():
    printer = Printer()
    with pytest.raises(EliteError):
        Elite(printer)


def test_elite_sudo_uid_gid_invalid(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)
    monkeypatch.setenv('SUDO_UID', 'hmm')
    monkeypatch.setenv('SUDO_GID', 'wow')

    with pytest.raises(EliteError):
        Elite(printer)


def test_elite_initialisation(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    elite = Elite(printer)

    assert elite.user_uid == 501
    assert elite.user_gid == 20

    assert elite.root_env['USER'] == 'root'
    assert elite.root_env['LOGNAME'] == 'root'
    assert elite.root_env['SHELL'] == '/bin/sh'
    assert elite.root_env['USERNAME'] == 'root'
    assert elite.root_env['MAIL'] == '/var/mail/root'

    assert elite.user_env['USER'] == 'fots'
    assert elite.user_env['LOGNAME'] == 'fots'
    assert elite.user_env['HOME'] == '/Users/fots'
    assert elite.user_env['SHELL'] == '/bin/bash'
    assert elite.user_env['PWD'] == '/Users/fots/Documents/Development/macbuild/elite'
    assert 'OLDPWD' not in elite.user_env
    assert 'USERNAME' not in elite.user_env
    assert 'MAIL' not in elite.user_env


def test_elite_register_action_which_already_exists(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            return self.ok(cool=True)

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    with pytest.raises(ValueError):
        elite.register_action('my_action', MyAction)


def test_elite_run_action_inexistent(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    elite = Elite(printer)
    with pytest.raises(AttributeError):
        elite.my_action()


def test_elite_run_action_ok(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            return self.ok(cool=True)

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    assert elite.my_action() == EliteResponse(changed=False, ok=True, data={'cool': True})


def test_elite_run_action_changed(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            return self.changed()

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    assert elite.my_action() == EliteResponse(changed=True, ok=True)


def test_elite_run_action_failed(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            raise ActionError('oh no')

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    with pytest.raises(EliteError):
        elite.my_action()


@mock.patch('elite.elite.demote')
@mock.patch('os.setegid')
@mock.patch('os.seteuid')
def test_elite_options_sudo(seteuid_mock, setegid_mock, demote_mock, monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            return self.ok()

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    with elite.options(sudo=True):
        assert elite.my_action() == EliteResponse(changed=False, ok=True)

    assert seteuid_mock.call_args_list == [mock.call(0), mock.call(501)]
    assert setegid_mock.call_args_list == [mock.call(0), mock.call(20)]
    assert demote_mock.call_args == mock.call(0, 0)


def test_elite_options_changed(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            return self.changed()

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    with elite.options(changed=False):
        assert elite.my_action() == EliteResponse(changed=False, ok=True)


def test_elite_options_ignore_failed(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            raise ActionError('oh no')

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    with elite.options(ignore_failed=True):
        assert elite.my_action() == EliteResponse(changed=False, ok=False, failed_message='oh no')


def test_elite_options_env(monkeypatch, printer):
    helpers.patch_root_runtime(monkeypatch)

    class MyAction(Action):
        def process(self):
            return self.ok(
                favourite_animal=os.environ['FAVOURITE_ANIMAL'],
                enjoy_mooing=bool(os.environ['ENJOY_MOOING'])
            )

    elite = Elite(printer)
    elite.register_action('my_action', MyAction)
    with elite.options(env={'FAVOURITE_ANIMAL': 'cows', 'ENJOY_MOOING': '1'}):
        assert elite.my_action() == EliteResponse(changed=False, ok=True, data={
            'favourite_animal': 'cows',
            'enjoy_mooing': True
        })


@mock.patch('os.setegid')
@mock.patch('os.seteuid')
@mock.patch('os.setgid')
@mock.patch('os.setuid')
def test_demote_user(setuid_mock, setgid_mock, seteuid_mock, setegid_mock):
    demoter = demote(501, 20)
    demoter()
    assert setuid_mock.call_args == mock.call(501)
    assert setgid_mock.call_args == mock.call(20)
    assert seteuid_mock.call_args_list == [mock.call(0), mock.call(501)]
    assert setegid_mock.call_args_list == [mock.call(0), mock.call(20)]


@mock.patch('os.setegid')
@mock.patch('os.seteuid')
@mock.patch('os.setgid')
@mock.patch('os.setuid')
def test_demote_root(setuid_mock, setgid_mock, seteuid_mock, setegid_mock):
    demoter = demote(0, 0)
    demoter()
    assert not setuid_mock.called
    assert not setgid_mock.called
    assert seteuid_mock.call_args_list == [mock.call(0)]
    assert setegid_mock.call_args_list == [mock.call(0)]
