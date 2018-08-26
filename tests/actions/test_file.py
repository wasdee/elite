import os
import shutil

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.file import File

from .helpers import build_open_with_permission_error


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_argument_state_invalid():
    with pytest.raises(ValueError):
        File(path='boo.txt', state='hmmm')


def test_argument_source_absent_state_combination_invalid():
    with pytest.raises(ValueError):
        File(path='boo.txt', source='source.txt', state='absent')


def test_argument_source_absent_after_init_invalid():
    file = File(path='boo.txt', state='absent')
    with pytest.raises(ValueError):
        file.source = 'source.txt'


def test_argument_source_directory_state_combination_invalid():
    with pytest.raises(ValueError):
        File(path='boo.txt', source='source', state='directory')


def test_argument_source_directory_after_init_invalid():
    file = File(path='boo.txt', state='directory')
    with pytest.raises(ValueError):
        file.source = 'source'


def test_argument_source_directory_symlink_combination_invalid():
    with pytest.raises(ValueError):
        File(path='boo.txt', state='symlink')


def test_argument_source_symlink_after_init_invalid():
    file = File(path='boo.txt', source='source.txt', state='symlink')
    with pytest.raises(ValueError):
        file.source = None


def test_argument_state_absent_after_init_invalid():
    file = File(path='boo.txt', source='source.txt')
    with pytest.raises(ValueError):
        file.state = 'absent'


def test_argument_state_directory_after_init_invalid():
    file = File(path='boo.txt', source='source')
    with pytest.raises(ValueError):
        file.state = 'directory'


def test_argument_state_symlink_after_init_invalid():
    file = File(path='boo.txt')
    with pytest.raises(ValueError):
        file.state = 'symlink'


def test_file_empty_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('testing.txt')

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(p.strpath))

    file = File(path=p.strpath, state='file')
    with pytest.raises(ActionError):
        file.process()


def test_file_empty_directory(tmpdir):
    p = tmpdir.mkdir('directory')

    file = File(path=p.strpath, state='file')
    with pytest.raises(ActionError):
        file.process()


def test_file_empty_inexistent(tmpdir):
    p = tmpdir.join('testing.txt')

    file = File(path=p.strpath, state='file')
    assert file.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == ''


def test_file_empty_exists(tmpdir):
    p = tmpdir.join('testing.txt')
    p.write('Hello there')

    file = File(path=p.strpath, state='file')
    assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_file_source_not_readable(tmpdir, monkeypatch):
    dp = tmpdir.join('testing.txt').ensure()
    sp = tmpdir.join('source.txt').ensure()

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(sp.strpath))

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    with pytest.raises(ActionError):
        file.process()


def test_file_source_and_path_not_readable(tmpdir, monkeypatch):
    dp = tmpdir.join('testing.txt').ensure()
    sp = tmpdir.join('source.txt').ensure()

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(dp.strpath))

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    with pytest.raises(ActionError):
        file.process()


def test_file_source_and_path_not_writable(tmpdir, monkeypatch):
    dp = tmpdir.join('testing.txt').ensure()
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    builtins_open = open

    def open_(  # pylint: disable=unused-argument
        file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True,
        opener=None
    ):
        if file == dp.strpath and mode == 'wb':
            raise PermissionError(13, 'Permission denied', file)
        else:
            return builtins_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    monkeypatch.setattr('builtins.open', open_)

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    with pytest.raises(ActionError):
        file.process()


def test_file_source_directory(tmpdir):
    dp = tmpdir.join('testing.txt')
    sp = tmpdir.mkdir('directory')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    with pytest.raises(ActionError):
        file.process()


def test_file_source_destination_path_is_directory(tmpdir):
    dp = tmpdir.mkdir('directory')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(
        changed=True, data={'path': dp.join('source.txt').strpath}
    )
    assert dp.join('source.txt').read() == 'Hello there'


def test_file_source_inexistent(tmpdir):
    dp = tmpdir.join('testing.txt')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})
    assert dp.read() == 'Hello there'


def test_file_source_exists_different(tmpdir):
    dp = tmpdir.join('testing.txt')
    dp.write('Goodbye there')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})
    assert dp.read() == 'Hello there'


def test_file_source_exists_same(tmpdir):
    dp = tmpdir.join('testing.txt')
    dp.write('Hello there')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(changed=False, data={'path': dp.strpath})


def test_directory_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('directory')

    os_mkdir = os.mkdir

    def mkdir(path, *args, **kwargs):
        if path == p.strpath:
            raise PermissionError(13, 'Permission denied', file)
        else:
            return os_mkdir(path, *args, **kwargs)

    monkeypatch.setattr('os.mkdir', mkdir)

    file = File(path=p.strpath, state='directory')
    with pytest.raises(ActionError):
        file.process()


def test_directory_inexistent(tmpdir):
    p = tmpdir.join('directory')

    file = File(path=p.strpath, state='directory')
    assert file.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.isdir()


def test_directory_exists(tmpdir):
    p = tmpdir.mkdir('directory')

    file = File(path=p.strpath, state='directory')
    assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_symlink_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('testing.txt')

    os_symlink = os.symlink

    def symlink(src, dst, *args, **kwargs):
        if dst == p.strpath:
            raise PermissionError(13, 'Permission denied', file)
        else:
            return os_symlink(src, dst, *args, **kwargs)

    monkeypatch.setattr('os.symlink', symlink)

    file = File(path=p.strpath, source='source.txt', state='symlink')
    with pytest.raises(ActionError):
        file.process()


def test_symlink_destination_path_is_directory(tmpdir):
    p = tmpdir.mkdir('directory')

    file = File(path=p.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(
        changed=True, data={'path': p.join('source.txt').strpath}
    )
    assert p.join('source.txt').islink()
    assert p.join('source.txt').readlink() == 'source.txt'


def test_symlink_inexistent(tmpdir):
    p = tmpdir.join('testing.txt')

    file = File(path=p.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.islink()
    assert p.readlink() == 'source.txt'


def test_symlink_exists_different(tmpdir):
    p = tmpdir.join('testing.txt')
    p.mksymlinkto('something.txt')

    file = File(path=p.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.islink()
    assert p.readlink() == 'source.txt'


def test_symlink_exists_same(tmpdir):
    p = tmpdir.join('testing.txt')
    p.mksymlinkto('source.txt')

    file = File(path=p.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_alias_not_writable(tmpdir):
    sp = tmpdir.join('source.txt').ensure()

    # TODO: Determine a suitable way to mock the appropriate PyObjC methods to do this better
    file = File(path='/alias', source=sp.strpath, state='alias')
    with pytest.raises(ActionError):
        file.process()


def test_alias_destination_path_is_directory(tmpdir):
    dp = tmpdir.mkdir('directory')
    sp = tmpdir.join('source.txt').ensure()

    file = File(path=dp.strpath, source=sp.strpath, state='alias')
    assert file.process() == ActionResponse(
        changed=True, data={'path': dp.join('source.txt').strpath}
    )
    assert dp.join('source.txt').isfile()
    alias_data = dp.join('source.txt').read_binary()
    assert alias_data.startswith(b'book')
    assert b'source.txt' in alias_data


def test_alias_source_inexistent(tmpdir):
    p = tmpdir.join('testing.txt')

    file = File(path=p.strpath, source='source.txt', state='alias')
    with pytest.raises(ActionError):
        file.process()


def test_alias_path_inexistent(tmpdir):
    dp = tmpdir.join('testing.txt')
    sp = tmpdir.join('source.txt').ensure()

    file = File(path=dp.strpath, source=sp.strpath, state='alias')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})
    assert dp.isfile()
    alias_data = dp.read_binary()
    assert alias_data.startswith(b'book')
    assert b'source.txt' in alias_data


def test_alias_exists_different(tmpdir):
    dp = tmpdir.join('test.alias')
    shutil.copy(os.path.join(FIXTURE_PATH, 'file', 'test.alias'), dp.strpath)
    sp = tmpdir.join('source.txt').ensure()

    file = File(path=dp.strpath, source=sp.strpath, state='alias')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})
    alias_data = dp.read_binary()
    assert alias_data.startswith(b'book')
    assert b'source.txt' in alias_data


def test_alias_exists_same(tmpdir):
    p = tmpdir.join('test.alias')
    shutil.copy(os.path.join(FIXTURE_PATH, 'file', 'test.alias'), p.strpath)

    try:
        # Create a file at the source path as it must exist for the alias to work
        with open('/private/var/tmp/test.txt', 'w'):
            pass

        file = File(path=p.strpath, source='/private/var/tmp/test.txt', state='alias')
        assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})
    finally:
        os.remove('/private/var/tmp/test.txt')


def test_absent_inexistent(tmpdir):
    p = tmpdir.join('testing.txt')

    file = File(path=p.strpath, state='absent')
    assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_absent_exists(tmpdir):
    p = tmpdir.join('testing.txt').ensure()

    file = File(path=p.strpath, state='absent')
    assert file.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert not p.exists()
