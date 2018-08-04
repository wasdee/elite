import pytest
from elite.actions import Action, ActionError
from elite.elite import Elite, EliteError, EliteResponse


class Printer:
    def action(self, state, action, args, response=None):
        pass

    def summary(self, actions):
        pass


def test_not_run_as_root():
    printer = Printer()
    with pytest.raises(EliteError):
        Elite(printer)


def test_invalid_sudo_uid_gid(monkeypatch):
    monkeypatch.setenv('SUDO_UID', 'hmm')
    monkeypatch.setenv('SUDO_GID', 'wow')

    printer = Printer()
    with pytest.raises(EliteError):
        Elite(printer)


def test_initialisation(elite):
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


def test_register_action_which_already_exists(elite):
    class MyAction(Action):
        def process(self):
            return self.ok(cool=True)

    elite.register_action('my_action', MyAction)
    with pytest.raises(ValueError):
        elite.register_action('my_action', MyAction)


def test_run_action_inexistent(elite):
    with pytest.raises(AttributeError):
        elite.my_action()


def test_run_action_ok(elite):
    class MyAction(Action):
        def process(self):
            return self.ok(cool=True)

    elite.register_action('my_action', MyAction)
    assert elite.my_action() == EliteResponse(changed=False, ok=True, data={'cool': True})


def test_run_action_changed(elite):
    class MyAction(Action):
        def process(self):
            return self.changed()

    elite.register_action('my_action', MyAction)
    assert elite.my_action() == EliteResponse(changed=True, ok=True)


def test_run_action_failed(elite):
    class MyAction(Action):
        def process(self):
            raise ActionError('oh no')

    elite.register_action('my_action', MyAction)
    with pytest.raises(EliteError):
        elite.my_action()
