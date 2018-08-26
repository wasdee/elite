import os
import shutil

from elite.actions import ActionResponse
from elite.actions.file_info import FileInfo


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_inexistent(tmpdir):
    p = tmpdir.join('test.txt')

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': False,
        'file_type': None,
        'source': None,
        'mount': None,
        'flags': None
    })


def test_directory(tmpdir):
    p = tmpdir.mkdir('directory')

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'directory',
        'source': None,
        'mount': False,
        'flags': []
    })


def test_file_with_aliases(tmpdir):
    p = tmpdir.join('test.txt').ensure()

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'file',
        'source': None,
        'mount': False,
        'flags': []
    })


def test_file_without_aliases(tmpdir):
    p = tmpdir.join('test.txt').ensure()

    file_info = FileInfo(path=p.strpath, aliases=False)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'file',
        'source': None,
        'mount': False,
        'flags': []
    })


def test_alias_inexistent(tmpdir):
    p = tmpdir.join('test.alias')
    shutil.copy(os.path.join(FIXTURE_PATH, 'file', 'test.alias'), p.strpath)

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'alias',
        'source': None,
        'mount': False,
        'flags': []
    })


def test_alias_exists(tmpdir):
    p = tmpdir.join('test.alias')
    shutil.copy(os.path.join(FIXTURE_PATH, 'file', 'test.alias'), p.strpath)

    try:
        # Create a file at the source path as it must exist for the alias to work
        with open('/private/var/tmp/test.txt', 'w'):
            pass

        file_info = FileInfo(path=p.strpath)
        assert file_info.process() == ActionResponse(changed=False, data={
            'exists': True,
            'file_type': 'alias',
            'source': '/private/var/tmp/test.txt',
            'mount': False,
            'flags': []
        })
    finally:
        os.remove('/private/var/tmp/test.txt')


def test_file_flags(tmpdir):
    p = tmpdir.join('test.txt').ensure()
    os.chflags(p.strpath, 0b1000000000000000)

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'file',
        'source': None,
        'mount': False,
        'flags': ['hidden']
    })


def test_symlink_inexistent(tmpdir):
    p = tmpdir.join('testing.txt')
    p.mksymlinkto('something.txt')

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': False,
        'file_type': 'symlink',
        'source': 'something.txt',
        'mount': False,
        'flags': []
    })


def test_symlink_exists(tmpdir):
    p = tmpdir.join('testing.txt')
    p.mksymlinkto('something.txt')
    tmpdir.join('something.txt').ensure()

    file_info = FileInfo(path=p.strpath)
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'symlink',
        'source': 'something.txt',
        'mount': False,
        'flags': []
    })


def test_mount():
    file_info = FileInfo(path='/')
    assert file_info.process() == ActionResponse(changed=False, data={
        'exists': True,
        'file_type': 'directory',
        'source': None,
        'mount': True,
        'flags': []
    })
