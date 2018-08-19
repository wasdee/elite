import os

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.archive import Archive


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_extract_invalid_archive_type(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.boo')
    )
    with pytest.raises(ActionError):
        archive.process()


def test_extract_rar_invalid_archive_contents(tmpdir):
    sp = tmpdir.join('archive.rar').ensure()
    dp = tmpdir.mkdir('directory')

    archive = Archive(
        path=dp.strpath,
        source=sp.strpath
    )
    with pytest.raises(ActionError):
        archive.process()


def test_extract_rar_invalid_archive_volume(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.part2.rar')
    )
    with pytest.raises(ActionError):
        archive.process()


def test_extract_zip_preserve(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.zip'),
        preserve_mode=True
    )
    assert archive.process() == ActionResponse(changed=True)

    assert p.join('hello.txt').isfile()
    assert oct(p.join('hello.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory1').isdir()
    assert oct(p.join('directory1').stat().mode)[-4:] == '0755'
    assert p.join('directory1/file1.txt').isfile()
    assert oct(p.join('directory1/file1.txt').stat().mode)[-4:] == '0600'
    assert p.join('directory1/file2.txt').isfile()
    assert oct(p.join('directory1/file2.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory2').isdir()
    assert oct(p.join('directory2').stat().mode)[-4:] == '0755'
    assert p.join('directory2/file3.json').isfile()
    assert oct(p.join('directory2/file3.json').stat().mode)[-4:] == '0644'
    assert p.join('directory2/file4.txt').isfile()
    assert oct(p.join('directory2/file4.txt').stat().mode)[-4:] == '0666'


def test_extract_zip_no_preserve(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.zip'),
        preserve_mode=False
    )
    assert archive.process() == ActionResponse(changed=True)

    assert p.join('hello.txt').isfile()
    assert oct(p.join('hello.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory1').isdir()
    assert oct(p.join('directory1').stat().mode)[-4:] == '0755'
    assert p.join('directory1/file1.txt').isfile()
    assert oct(p.join('directory1/file1.txt').stat().mode)[-4:] == '0644'
    assert p.join('directory1/file2.txt').isfile()
    assert oct(p.join('directory1/file2.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory2').isdir()
    assert oct(p.join('directory2').stat().mode)[-4:] == '0755'
    assert p.join('directory2/file3.json').isfile()
    assert oct(p.join('directory2/file3.json').stat().mode)[-4:] == '0644'
    assert p.join('directory2/file4.txt').isfile()
    assert oct(p.join('directory2/file4.txt').stat().mode)[-4:] == '0644'


def test_extract_zip_no_dirs(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive_no_dirs.zip')
    )
    assert archive.process() == ActionResponse(changed=True)

    assert p.join('hello.txt').isfile()

    assert p.join('directory1').isdir()
    assert p.join('directory1/file1.txt').isfile()
    assert p.join('directory1/file2.txt').isfile()

    assert p.join('directory2').isdir()
    assert p.join('directory2/file3.json').isfile()
    assert p.join('directory2/file4.txt').isfile()


def test_extract_zip_existing(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.zip'),
        preserve_mode=True
    )
    assert archive.process() == ActionResponse(changed=True)
    assert archive.process() == ActionResponse(changed=False)


def test_extract_rar_preserve(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.rar'),
        preserve_mode=True
    )
    assert archive.process() == ActionResponse(changed=True)

    assert p.join('hello.txt').isfile()
    assert oct(p.join('hello.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory1').isdir()
    assert oct(p.join('directory1').stat().mode)[-4:] == '0755'
    assert p.join('directory1/file1.txt').isfile()
    assert oct(p.join('directory1/file1.txt').stat().mode)[-4:] == '0600'
    assert p.join('directory1/file2.txt').isfile()
    assert oct(p.join('directory1/file2.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory2').isdir()
    assert oct(p.join('directory2').stat().mode)[-4:] == '0755'
    assert p.join('directory2/file3.json').isfile()
    assert oct(p.join('directory2/file3.json').stat().mode)[-4:] == '0644'
    assert p.join('directory2/file4.txt').isfile()
    assert oct(p.join('directory2/file4.txt').stat().mode)[-4:] == '0666'


def test_extract_rar_no_preserve(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.rar'),
        preserve_mode=False
    )
    assert archive.process() == ActionResponse(changed=True)

    assert p.join('hello.txt').isfile()
    assert oct(p.join('hello.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory1').isdir()
    assert oct(p.join('directory1').stat().mode)[-4:] == '0755'
    assert p.join('directory1/file1.txt').isfile()
    assert oct(p.join('directory1/file1.txt').stat().mode)[-4:] == '0644'
    assert p.join('directory1/file2.txt').isfile()
    assert oct(p.join('directory1/file2.txt').stat().mode)[-4:] == '0644'

    assert p.join('directory2').isdir()
    assert oct(p.join('directory2').stat().mode)[-4:] == '0755'
    assert p.join('directory2/file3.json').isfile()
    assert oct(p.join('directory2/file3.json').stat().mode)[-4:] == '0644'
    assert p.join('directory2/file4.txt').isfile()
    assert oct(p.join('directory2/file4.txt').stat().mode)[-4:] == '0644'


def test_extract_rar_no_dirs(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive_no_dirs.rar')
    )
    assert archive.process() == ActionResponse(changed=True)

    assert p.join('hello.txt').isfile()

    assert p.join('directory1').isdir()
    assert p.join('directory1/file1.txt').isfile()
    assert p.join('directory1/file2.txt').isfile()

    assert p.join('directory2').isdir()
    assert p.join('directory2/file3.json').isfile()
    assert p.join('directory2/file4.txt').isfile()


def test_extract_rar_existing(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.rar'),
        preserve_mode=True
    )
    assert archive.process() == ActionResponse(changed=True)
    assert archive.process() == ActionResponse(changed=False)


def test_extract_zip_invalid_archive_contents(tmpdir):
    sp = tmpdir.join('archive.zip').ensure()
    dp = tmpdir.mkdir('directory')

    archive = Archive(
        path=dp.strpath,
        source=sp.strpath
    )
    with pytest.raises(ActionError):
        archive.process()


def test_extract_ignore(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.zip'),
        ignore_files=['file2.txt', 'directory2']
    )
    assert archive.process() == ActionResponse(changed=True)
    assert p.join('hello.txt').isfile()
    assert p.join('directory1').isdir()
    assert p.join('directory1/file1.txt').isfile()
    assert not p.join('directory1/file2.txt').isfile()
    assert not p.join('directory2').isdir()
    assert not p.join('directory2/file3.json').isfile()
    assert not p.join('directory2/file4.txt').isfile()


def test_extract_base_dir(tmpdir):
    p = tmpdir.mkdir('directory')

    archive = Archive(
        path=p.strpath,
        source=os.path.join(FIXTURE_PATH, 'archive', 'archive.zip'),
        base_dir='directory1'
    )
    assert archive.process() == ActionResponse(changed=True)
    assert not p.join('hello.txt').isfile()
    assert p.join('file1.txt').isfile()
    assert p.join('file2.txt').isfile()
