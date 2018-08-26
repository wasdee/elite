import os

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.find import Find
from tests import helpers


def build_directory(p):
    fa1 = p.join('filea1.yaml').ensure()
    os.chflags(fa1.strpath, 0b1000000000000000)
    fa2 = p.join('filea2.json').ensure()
    fa2.chmod(0o600)
    p.join('filea3.txt').ensure()

    d1 = p.mkdir('test')
    d1.join('fileb1.txt').ensure()
    fb2 = d1.join('fileb2.json').ensure()
    fb2.chmod(0o600)
    os.chflags(fb2.strpath, 0b1000000000000000)
    d1.join('fileb3.txt').ensure()

    s1 = d1.join('symlinkb1.txt')
    s1.mksymlinkto('fileb1.txt')
    s2 = d1.join('symlinkb2.json')
    s2.mksymlinkto('fileb2.json')
    s3 = d1.join('symlinkb3.txt')
    s3.mksymlinkto('fileb3.txt')

    d2 = d1.mkdir('wow')
    d2.join('filec1.zip').ensure()
    d2.join('filec2.txt').ensure()
    d2.join('filec3.yaml').ensure()


os_stat = os.stat


def directory_stat(path, *, dir_fd=None, follow_symlinks=True):
    if path.endswith('filea3.txt'):
        return os.stat_result(
            (33188, 4254835, 16777220, 1, 502, 20, 0, 1533464722, 1533464722, 1533464722)
        )
    elif path.endswith('fileb1.txt'):
        return os.stat_result(
            (33188, 4254837, 16777220, 1, 501, 0, 0, 1533464722, 1533464722, 1533464722)
        )
    elif path.endswith('fileb3.txt'):
        return os.stat_result(
            (33188, 4254839, 16777220, 1, 502, 20, 0, 1533464722, 1533464722, 1533464722)
        )
    elif path.endswith('filec2.txt'):
        return os.stat_result(
            (33188, 4254845, 16777220, 1, 501, 0, 0, 1533464722, 1533464722, 1533464722)
        )
    else:
        return os_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)


def test_path_inexistent(tmpdir):
    p = tmpdir.join('test')
    find = Find(path=p.strpath)
    with pytest.raises(ActionError):
        find.process()


def test_all(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath)
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea1.yaml').strpath,
            tmpdir.join('filea2.json').strpath,
            tmpdir.join('filea3.txt').strpath,
            tmpdir.join('test').strpath,
            tmpdir.join('test/fileb1.txt').strpath,
            tmpdir.join('test/fileb2.json').strpath,
            tmpdir.join('test/fileb3.txt').strpath,
            tmpdir.join('test/symlinkb1.txt').strpath,
            tmpdir.join('test/symlinkb2.json').strpath,
            tmpdir.join('test/symlinkb3.txt').strpath,
            tmpdir.join('test/wow').strpath,
            tmpdir.join('test/wow/filec1.zip').strpath,
            tmpdir.join('test/wow/filec2.txt').strpath,
            tmpdir.join('test/wow/filec3.yaml').strpath
        ]
    })


def test_min_depth(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, min_depth=2)
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('test/fileb1.txt').strpath,
            tmpdir.join('test/fileb2.json').strpath,
            tmpdir.join('test/fileb3.txt').strpath,
            tmpdir.join('test/symlinkb1.txt').strpath,
            tmpdir.join('test/symlinkb2.json').strpath,
            tmpdir.join('test/symlinkb3.txt').strpath,
            tmpdir.join('test/wow').strpath,
            tmpdir.join('test/wow/filec1.zip').strpath,
            tmpdir.join('test/wow/filec2.txt').strpath,
            tmpdir.join('test/wow/filec3.yaml').strpath
        ]
    })


def test_max_depth(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, max_depth=2)
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea1.yaml').strpath,
            tmpdir.join('filea2.json').strpath,
            tmpdir.join('filea3.txt').strpath,
            tmpdir.join('test').strpath,
            tmpdir.join('test/fileb1.txt').strpath,
            tmpdir.join('test/fileb2.json').strpath,
            tmpdir.join('test/fileb3.txt').strpath,
            tmpdir.join('test/symlinkb1.txt').strpath,
            tmpdir.join('test/symlinkb2.json').strpath,
            tmpdir.join('test/symlinkb3.txt').strpath,
            tmpdir.join('test/wow').strpath
        ]
    })


def test_types_directory(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, types=['directory'])
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('test').strpath,
            tmpdir.join('test/wow').strpath
        ]
    })


def test_types_file_with_aliases(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, types=['file'])
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea1.yaml').strpath,
            tmpdir.join('filea2.json').strpath,
            tmpdir.join('filea3.txt').strpath,
            tmpdir.join('test/fileb1.txt').strpath,
            tmpdir.join('test/fileb2.json').strpath,
            tmpdir.join('test/fileb3.txt').strpath,
            tmpdir.join('test/wow/filec1.zip').strpath,
            tmpdir.join('test/wow/filec2.txt').strpath,
            tmpdir.join('test/wow/filec3.yaml').strpath
        ]
    })


def test_types_file_without_aliases(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, types=['file'], aliases=False)
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea1.yaml').strpath,
            tmpdir.join('filea2.json').strpath,
            tmpdir.join('filea3.txt').strpath,
            tmpdir.join('test/fileb1.txt').strpath,
            tmpdir.join('test/fileb2.json').strpath,
            tmpdir.join('test/fileb3.txt').strpath,
            tmpdir.join('test/wow/filec1.zip').strpath,
            tmpdir.join('test/wow/filec2.txt').strpath,
            tmpdir.join('test/wow/filec3.yaml').strpath
        ]
    })


def test_types_symlink(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, types=['symlink'])
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('test/symlinkb1.txt').strpath,
            tmpdir.join('test/symlinkb2.json').strpath,
            tmpdir.join('test/symlinkb3.txt').strpath
        ]
    })


def test_mode(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, mode='0600')
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea2.json').strpath,
            tmpdir.join('test/fileb2.json').strpath
        ]
    })


def test_owner_inexistent(tmpdir, monkeypatch):
    build_directory(tmpdir)
    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)
    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)
    monkeypatch.setattr('os.stat', directory_stat)

    find = Find(path=tmpdir.strpath, owner='wow')
    with pytest.raises(ActionError):
        find.process()


def test_owner(tmpdir, monkeypatch):
    build_directory(tmpdir)
    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)
    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)
    monkeypatch.setattr('os.stat', directory_stat)

    find = Find(path=tmpdir.strpath, owner='happy')
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea3.txt').strpath,
            tmpdir.join('test/fileb3.txt').strpath
        ]
    })


def test_group_inexistent(tmpdir, monkeypatch):
    build_directory(tmpdir)
    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)
    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)
    monkeypatch.setattr('os.stat', directory_stat)

    find = Find(path=tmpdir.strpath, group='wow')
    with pytest.raises(ActionError):
        find.process()


def test_group(tmpdir, monkeypatch):
    build_directory(tmpdir)
    monkeypatch.setattr('pwd.getpwnam', helpers.getpwnam)
    monkeypatch.setattr('grp.getgrnam', helpers.getgrnam)
    monkeypatch.setattr('os.stat', directory_stat)

    find = Find(path=tmpdir.strpath, group='wheel')
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('test/fileb1.txt').strpath,
            tmpdir.join('test/wow/filec2.txt').strpath
        ]
    })


def test_flags_invalid(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, flags=['hmmm'])
    with pytest.raises(ActionError):
        find.process()


def test_flags(tmpdir):
    build_directory(tmpdir)
    find = Find(path=tmpdir.strpath, flags=['hidden'])
    assert find.process() == ActionResponse(changed=False, data={
        'paths': [
            tmpdir.join('filea1.yaml').strpath,
            tmpdir.join('test/fileb2.json').strpath
        ]
    })
