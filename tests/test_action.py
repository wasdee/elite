import os
from unittest import mock

import pytest
from elite.actions import Action, ActionError, ActionResponse, FileAction
from tests import helpers


def test_action_ok():
    action = Action()
    assert action.ok(path='/Users/fots/data') == ActionResponse(
        changed=False, data={'path': '/Users/fots/data'}
    )


def test_action_changed():
    action = Action()
    assert action.changed(path='/Users/fots/data') == ActionResponse(
        changed=True, data={'path': '/Users/fots/data'}
    )


def test_action_run_ok():
    action = Action()
    process = action.run(['echo', '-n', 'hi'])
    assert process.returncode == 0
    assert process.stdout is None
    assert process.stderr == ''


def test_action_run_failed():
    action = Action()
    with pytest.raises(ActionError) as e:
        action.run(['false'])
    assert e.value.args[0] == "unable to execute command ['false']"


def test_action_run_failed_ignore():
    action = Action()
    process = action.run(['false'], ignore_fail=True)
    assert process.returncode == 1
    assert process.stdout is None
    assert process.stderr is None


def test_action_run_failed_not_found():
    action = Action()
    with pytest.raises(ActionError) as e:
        action.run(['falseeeeeey'])
    assert e.value.args[0] == "unable to find executable for command ['falseeeeeey']"


def test_action_run_failed_with_stderr():
    action = Action()
    with pytest.raises(ActionError) as e:
        action.run('>&2 echo -n oh no && false', shell=True, executable='/bin/bash')
    assert e.value.args[0] == 'oh no'


def test_action_run_failed_with_custom_error():
    action = Action()
    with pytest.raises(ActionError) as e:
        action.run(['false'], fail_error='no cows allowed')
    assert e.value.args[0] == 'no cows allowed'


def test_action_run_failed_with_custom_error_and_stderr():
    action = Action()
    with pytest.raises(ActionError) as e:
        action.run(
            '>&2 echo -n oh no && false', shell=True, executable='/bin/bash',
            fail_error='no cows allowed'
        )
    assert e.value.args[0] == 'no cows allowed: oh no'


def test_action_run_capture_stdout():
    action = Action()
    process = action.run(['echo', '-n', 'hi'], stdout=True)
    assert process.returncode == 0
    assert process.stdout == 'hi'
    assert process.stderr == ''


def test_action_run_capture_stderr():
    action = Action()
    process = action.run('>&2 echo -n hi', shell=True, executable='/bin/bash', stderr=True)
    assert process.returncode == 0
    assert process.stdout is None
    assert process.stderr == 'hi'


def test_file_action_set_file_attributes_no_changes(tmpdir):
    p = tmpdir.join('test.txt').ensure()

    file_action = FileAction()
    assert file_action.set_file_attributes(p.strpath) is False


def test_file_action_set_file_attributes_inexistent(tmpdir):
    p = tmpdir.join('test.txt')

    file_action = FileAction(mode='0644')
    with pytest.raises(ActionError):
        file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_mode_different(tmpdir):
    p = tmpdir.join('test.txt').ensure()
    p.chmod(0o600)

    file_action = FileAction(mode='0644')
    assert file_action.set_file_attributes(p.strpath) is True
    assert oct(p.stat().mode)[-4:] == '0644'


def test_file_action_set_file_attributes_change_mode_same(tmpdir):
    p = tmpdir.join('test.txt').ensure()
    p.chmod(0o644)

    file_action = FileAction(mode='0644')
    assert file_action.set_file_attributes(p.strpath) is False
    assert oct(p.stat().mode)[-4:] == '0644'


def test_file_action_set_file_attributes_change_mode_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt').ensure()
    p.chmod(0o600)

    def chmod(path, mode, follow_symlinks=True):  # pylint: disable=unused-argument
        raise PermissionError(1, 'Operation not permitted', p.strpath)
    monkeypatch.setattr('os.chmod', chmod)

    file_action = FileAction(mode='0644')
    with pytest.raises(ActionError):
        assert file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_owner_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 501, 20, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    file_action = FileAction(owner='hmmm')
    with pytest.raises(ActionError):
        file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_owner_same(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 501, 20, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    file_action = FileAction(owner='fots')
    assert file_action.set_file_attributes(p.strpath) is False


def test_file_action_set_file_attributes_change_owner_different(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 502, 20, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    with mock.patch('os.chown') as chown_mock:
        file_action = FileAction(owner='fots')
        assert file_action.set_file_attributes(p.strpath) is True
        assert chown_mock.called
        assert chown_mock.call_args == mock.call(p.strpath, 501, -1)


def test_file_action_set_file_attributes_change_owner_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 502, 20, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    def chown(path, uid, gid, follow_symlinks=True):  # pylint: disable=unused-argument
        raise PermissionError(1, 'Operation not permitted', p.strpath)
    monkeypatch.setattr('os.chown', chown)

    file_action = FileAction(owner='fots')
    with pytest.raises(ActionError):
        assert file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_group_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 501, 20, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    file_action = FileAction(group='hmmm')
    with pytest.raises(ActionError):
        file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_group_same(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 501, 20, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    file_action = FileAction(group='staff')
    assert file_action.set_file_attributes(p.strpath) is False


def test_file_action_set_file_attributes_change_group_different(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 501, 21, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    with mock.patch('os.chown') as chown_mock:
        file_action = FileAction(group='staff')
        assert file_action.set_file_attributes(p.strpath) is True
        assert chown_mock.called
        assert chown_mock.call_args == mock.call(p.strpath, -1, 20)


def test_file_action_set_file_attributes_change_group_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt')

    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)

    def stat(path, follow_symlinks=True):  # pylint: disable=unused-argument
        if path == p.strpath:
            return os.stat_result(
                (33188, 3955467, 16777220, 1, 501, 21, 1308, 1533358970, 1532951575, 1532951575)
            )
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path}'")
    monkeypatch.setattr('os.stat', stat)

    def chown(path, uid, gid, follow_symlinks=True):  # pylint: disable=unused-argument
        raise PermissionError(1, 'Operation not permitted', p.strpath)
    monkeypatch.setattr('os.chown', chown)

    file_action = FileAction(group='staff')
    with pytest.raises(ActionError):
        assert file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_flags_invalid(tmpdir):
    p = tmpdir.join('test.txt').ensure()

    file_action = FileAction(flags=['hmmm'])
    with pytest.raises(ActionError):
        file_action.set_file_attributes(p.strpath)


def test_file_action_set_file_attributes_change_flags_different(tmpdir):
    p = tmpdir.join('test.txt').ensure()

    file_action = FileAction(flags=['hidden'])
    assert file_action.set_file_attributes(p.strpath) is True
    assert p.stat().flags == 0b1000000000000000


def test_file_action_set_file_attributes_change_flags_same(tmpdir):
    p = tmpdir.join('test.txt').ensure()
    os.chflags(p.strpath, 0b1000000000000000)

    file_action = FileAction(flags=['hidden'])
    assert file_action.set_file_attributes(p.strpath) is False
    assert p.stat().flags == 0b1000000000000000


def test_file_action_set_file_attributes_change_flags_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.txt').ensure()

    def chflags(path, flags, follow_symlinks=True):  # pylint: disable=unused-argument
        raise PermissionError(1, 'Operation not permitted', p.strpath)
    monkeypatch.setattr('os.chflags', chflags)

    file_action = FileAction(flags=['hidden'])
    with pytest.raises(ActionError):
        assert file_action.set_file_attributes(p.strpath)


def test_file_action_remove_inexistent(tmpdir):
    p = tmpdir.join('test')

    file_action = FileAction()
    assert file_action.remove(p.strpath) is False


def test_file_action_remove_strange_file():
    file_action = FileAction()
    assert file_action.remove('/dev/null') is False


def test_file_action_remove_file(tmpdir):
    p = tmpdir.join('test').ensure()

    file_action = FileAction()
    assert file_action.remove(p.strpath) is True
    assert not p.exists()


def test_file_action_remove_file_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test').ensure()

    def remove(path):  # pylint: disable=unused-argument
        raise PermissionError(13, 'Permission denied', p.strpath)
    monkeypatch.setattr('os.remove', remove)

    file_action = FileAction()
    with pytest.raises(ActionError):
        file_action.remove(p.strpath)


def test_file_action_remove_symlink(tmpdir):
    p = tmpdir.join('testing.txt')
    p.mksymlinkto('something.txt')

    file_action = FileAction()
    assert file_action.remove(p.strpath) is True
    assert not p.exists()


def test_file_action_remove_symlink_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('testing.txt')
    p.mksymlinkto('something.txt')

    def remove(path):  # pylint: disable=unused-argument
        raise PermissionError(13, 'Permission denied', p.strpath)
    monkeypatch.setattr('os.remove', remove)

    file_action = FileAction()
    with pytest.raises(ActionError):
        file_action.remove(p.strpath)


def test_file_action_remove_directory(tmpdir):
    p = tmpdir.mkdir('test')
    p.join('file1.txt').ensure()
    p.join('file2.txt').ensure()

    file_action = FileAction()
    assert file_action.remove(p.strpath) is True
    assert not p.exists()


def test_file_action_remove_directory_not_writable(tmpdir, monkeypatch):
    p = tmpdir.mkdir('test')

    def rmtree(path):  # pylint: disable=unused-argument
        raise PermissionError(13, 'Permission denied', p.strpath)
    monkeypatch.setattr('shutil.rmtree', rmtree)

    file_action = FileAction()
    with pytest.raises(ActionError):
        file_action.remove(p.strpath)
