import os

import pytest
import vcr
from elite.actions import ActionError, ActionResponse
from elite.actions.download import Download

from .helpers import build_open_with_permission_error


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_path_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('data.dmg')

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(p.strpath))

    download = Download(url='https://www.eventideaudio.com/downloader/1165', path=p.strpath)
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'eventide.yaml')):
        with pytest.raises(ActionError):
            download.process()


def test_path_existing_with_valid_url(tmpdir):
    p = tmpdir.join('data.dmg').ensure()

    download = Download(url='https://www.eventideaudio.com/downloader/1165', path=p.strpath)
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'eventide.yaml')):
        assert download.process() == ActionResponse(changed=False, data={'path': p.strpath})


def test_url_inexistent(tmpdir):
    p = tmpdir.mkdir('directory')

    download = Download(
        url='https://google.com/wow',
        path=p.strpath
    )
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'inexistent.yaml')):
        with pytest.raises(ActionError):
            download.process()


def test_filename_provided(tmpdir):
    p = tmpdir.join('data.dmg')

    download = Download(url='https://www.eventideaudio.com/downloader/1165', path=p.strpath)
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'eventide.yaml')):
        assert download.process() == ActionResponse(changed=True, data={'path': p.strpath})


def test_filename_from_disposition(tmpdir):
    p = tmpdir.mkdir('directory')

    download = Download(url='https://www.eventideaudio.com/downloader/1165', path=p.strpath)
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'eventide.yaml')):
        assert download.process() == ActionResponse(changed=True, data={
            'path': os.path.join(p.strpath, '2016-Stereo-Room-3.1.3-osx-installer.dmg')
        })


def test_filename_from_url(tmpdir):
    p = tmpdir.mkdir('directory')

    download = Download(
        url='https://uhedownloads-heckmannaudiogmb.netdna-ssl.com/releases/Zebra2_28_7422_Mac.zip',
        path=p.strpath
    )
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'u-he.yaml')):
        assert download.process() == ActionResponse(changed=True, data={
            'path': os.path.join(p.strpath, 'Zebra2_28_7422_Mac.zip')
        })


def test_filename_from_url_inexistent(tmpdir):
    p = tmpdir.mkdir('directory')

    download = Download(
        url='https://google.com/',
        path=p.strpath
    )
    with vcr.use_cassette(os.path.join(FIXTURE_PATH, 'download', 'google.yaml')):
        with pytest.raises(ActionError):
            download.process()
