from unittest import mock

import pytest
from CoreFoundation import NSURL  # pylint: disable=no-name-in-module
from elite.actions import ActionError, ActionResponse
from elite.actions.login_item import LoginItem


class MockLoginItem:
    def __init__(self, path, hidden):
        self._path = path
        self._hidden = hidden

    def path(self):
        return self._path

    def properties(self):
        return {'com.apple.loginitem.HideOnLaunch': self._hidden}


def mock_resolve_url(in_item, in_flags, out_error):  # pylint: disable=unused-argument
    url = NSURL.fileURLWithPath_(in_item.path())
    error = None
    return url, error


def test_argument_state_invalid():
    with pytest.raises(ValueError):
        LoginItem(path='/Applications/Dropbox.app', state='hmmm')


def test_path_inexistent(tmpdir):
    p = tmpdir.join('Dropbox.app')

    login_item = LoginItem(path=p.strpath, state='present')
    with pytest.raises(ActionError):
        login_item.process()


@mock.patch('elite.actions.login_item.LSSharedFileListInsertItemURL')
@mock.patch('elite.actions.login_item.LSSharedFileListItemCopyResolvedURL')
@mock.patch('elite.actions.login_item.LSSharedFileListCreate')
def test_present_installed_identical(ls_create_mock, ls_resolve_url_mock, ls_insert_mock, tmpdir):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = [
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem(p.strpath, hidden=True),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ]
    ls_create_mock().allItems.return_value = login_items
    ls_resolve_url_mock.side_effect = mock_resolve_url

    login_item = LoginItem(path=p.strpath, state='present', hidden=True)
    assert login_item.process() == ActionResponse(changed=False)
    assert not ls_insert_mock.called


@mock.patch('elite.actions.login_item.LSSharedFileListInsertItemURL')
@mock.patch('elite.actions.login_item.LSSharedFileListItemCopyResolvedURL')
@mock.patch('elite.actions.login_item.LSSharedFileListCreate')
def test_present_installed_hidden_different(
    ls_create_mock, ls_resolve_url_mock, ls_insert_mock, tmpdir
):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = [
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem(p.strpath, hidden=True),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ]
    ls_create_mock().allItems.return_value = login_items
    ls_resolve_url_mock.side_effect = mock_resolve_url

    login_item = LoginItem(path=p.strpath, state='present', hidden=False)
    assert login_item.process() == ActionResponse(changed=True)
    assert ls_insert_mock.called


@mock.patch('elite.actions.login_item.LSSharedFileListInsertItemURL')
@mock.patch('elite.actions.login_item.LSSharedFileListItemCopyResolvedURL')
@mock.patch('elite.actions.login_item.LSSharedFileListCreate')
def test_present_not_installed(
    ls_create_mock, ls_resolve_url_mock, ls_insert_mock, tmpdir
):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = [
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ]
    ls_create_mock().allItems.return_value = login_items
    ls_resolve_url_mock.side_effect = mock_resolve_url

    login_item = LoginItem(path=p.strpath, state='present', hidden=False)
    assert login_item.process() == ActionResponse(changed=True)
    assert ls_insert_mock.called


@mock.patch('elite.actions.login_item.LSSharedFileListItemRemove')
@mock.patch('elite.actions.login_item.LSSharedFileListItemCopyResolvedURL')
@mock.patch('elite.actions.login_item.LSSharedFileListCreate')
def test_absent_not_installed(ls_create_mock, ls_resolve_url_mock, ls_remove_mock, tmpdir):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = [
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ]
    ls_create_mock().allItems.return_value = login_items
    ls_resolve_url_mock.side_effect = mock_resolve_url

    login_item = LoginItem(path=p.strpath, state='absent')
    assert login_item.process() == ActionResponse(changed=False)
    assert not ls_remove_mock.called


@mock.patch('elite.actions.login_item.LSSharedFileListItemRemove')
@mock.patch('elite.actions.login_item.LSSharedFileListItemCopyResolvedURL')
@mock.patch('elite.actions.login_item.LSSharedFileListCreate')
def test_absent_installed(ls_create_mock, ls_resolve_url_mock, ls_remove_mock, tmpdir):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = [
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem(p.strpath, hidden=True),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ]
    ls_create_mock().allItems.return_value = login_items
    ls_resolve_url_mock.side_effect = mock_resolve_url

    login_item = LoginItem(path=p.strpath, state='absent')
    assert login_item.process() == ActionResponse(changed=True)
    assert ls_remove_mock.called
