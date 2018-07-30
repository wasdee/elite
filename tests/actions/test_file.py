import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.file import File


def test_invalid_state():
    with pytest.raises(ValueError):
        File(path='boo.txt', state='hmmm')


def test_invalid_source_absent_state_combination():
    with pytest.raises(ValueError):
        File(path='boo.txt', source='source.txt', state='absent')


def test_invalid_source_absent_after_init():
    file = File(path='boo.txt', state='absent')
    with pytest.raises(ValueError):
        file.source = 'source.txt'


def test_invalid_source_directory_state_combination():
    with pytest.raises(ValueError):
        File(path='boo.txt', source='source', state='directory')


def test_invalid_source_directory_after_init():
    file = File(path='boo.txt', state='directory')
    with pytest.raises(ValueError):
        file.source = 'source'


def test_invalid_source_directory_symlink_combination():
    with pytest.raises(ValueError):
        File(path='boo.txt', state='symlink')


def test_invalid_source_symlink_after_init():
    file = File(path='boo.txt', source='source.txt', state='symlink')
    with pytest.raises(ValueError):
        file.source = None


def test_invalid_state_absent_after_init():
    file = File(path='boo.txt', source='source.txt')
    with pytest.raises(ValueError):
        file.state = 'absent'


def test_invalid_state_directory_after_init():
    file = File(path='boo.txt', source='source')
    with pytest.raises(ValueError):
        file.state = 'directory'


def test_invalid_state_symlink_after_init():
    file = File(path='boo.txt')
    with pytest.raises(ValueError):
        file.state = 'symlink'


def test_file_empty_not_writable():
    file = File(path='/file', state='file')
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


def test_file_empty_exists(tmpdir):
    p = tmpdir.join('testing.txt')
    p.write('Hello there')

    file = File(path=p.strpath, state='file')
    assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_file_source_not_writable(tmpdir):
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path='/file', source=sp.strpath, state='file')
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


def test_file_source_inexistent(tmpdir):
    dp = tmpdir.join('testing.txt')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})


def test_file_source_exists_different(tmpdir):
    dp = tmpdir.join('testing.txt')
    dp.write('Goodbye there')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})


def test_file_source_exists_same(tmpdir):
    dp = tmpdir.join('testing.txt')
    dp.write('Hello there')
    sp = tmpdir.join('source.txt')
    sp.write('Hello there')

    file = File(path=dp.strpath, source=sp.strpath, state='file')
    assert file.process() == ActionResponse(changed=False, data={'path': dp.strpath})


def test_directory_not_writable():
    file = File(path='/directory', state='directory')
    with pytest.raises(ActionError):
        file.process()


def test_directory_inexistent(tmpdir):
    p = tmpdir.join('directory')

    file = File(path=p.strpath, state='directory')
    assert file.process() == ActionResponse(changed=True, data={'path': p.strpath})


def test_directory_exists(tmpdir):
    p = tmpdir.mkdir('directory')

    file = File(path=p.strpath, state='directory')
    assert file.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_symlink_not_writable():
    file = File(path='/symlink', source='source.txt', state='symlink')
    with pytest.raises(ActionError):
        file.process()


def test_symlink_destination_path_is_directory(tmpdir):
    dp = tmpdir.join('testing.txt')

    file = File(path=dp.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})


def test_symlink_inexistent(tmpdir):
    dp = tmpdir.mkdir('directory')

    file = File(path=dp.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(
        changed=True, data={'path': dp.join('source.txt').strpath}
    )


def test_symlink_exists_different(tmpdir):
    dp = tmpdir.join('testing.txt')
    dp.mksymlinkto('something.txt')

    file = File(path=dp.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})


def test_symlink_exists_same(tmpdir):
    dp = tmpdir.join('testing.txt')
    dp.mksymlinkto('source.txt')

    file = File(path=dp.strpath, source='source.txt', state='symlink')
    assert file.process() == ActionResponse(changed=False, data={'path': dp.strpath})


def test_absent_inexistent(tmpdir):
    dp = tmpdir.join('testing.txt')

    file = File(path=dp.strpath, state='absent')
    assert file.process() == ActionResponse(changed=False, data={'path': dp.strpath})


def test_absent_exists(tmpdir):
    dp = tmpdir.join('testing.txt').ensure()

    file = File(path=dp.strpath, state='absent')
    assert file.process() == ActionResponse(changed=True, data={'path': dp.strpath})
