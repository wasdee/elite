from elite.actions import ActionResponse
from elite.actions.rsync import Rsync


def test_archive_same(tmpdir):
    dp = tmpdir.mkdir('destination')
    sp = tmpdir.mkdir('source')

    rsync = Rsync(dp.strpath, sp.strpath + sp.sep)
    assert rsync.process() == ActionResponse(changed=False)


def test_archive_different(tmpdir):
    dp = tmpdir.mkdir('destination')
    dp.join('file1.txt').ensure()
    sp = tmpdir.mkdir('source')
    sp.join('file2.txt').ensure()
    sp.join('file3.txt').ensure()

    rsync = Rsync(dp.strpath, sp.strpath + sp.sep)
    assert rsync.process() == ActionResponse(changed=True, data={'changes': [
        ('send', 'file2.txt'),
        ('send', 'file3.txt')
    ]})


def test_archive_different_options(tmpdir):
    dp = tmpdir.mkdir('destination')
    dp.join('file1.txt').ensure()
    sp = tmpdir.mkdir('source')
    sp.join('file2.txt').ensure()
    sp.join('file3.txt').ensure()

    rsync = Rsync(dp.strpath, sp.strpath + sp.sep, options=['--delete'])
    assert rsync.process() == ActionResponse(changed=True, data={'changes': [
        ('del.', 'file1.txt'),
        ('send', 'file2.txt'),
        ('send', 'file3.txt')
    ]})
