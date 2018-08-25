from unittest import mock

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.login_item import LoginItem


class MockLoginItem:
    def __init__(self, path, hidden):
        self._path = path
        self._hidden = hidden
        self.deleted = False

    def __eq__(self, other):
        return (
            self.path() == other.path() and
            self.hidden() == other.hidden() and
            self.deleted == other.deleted
        )

    def path(self):
        return self._path

    def hidden(self):
        return self._hidden

    def setHidden_(self, hidden):  # noqa: N802, pylint: disable=invalid-name
        self._hidden = hidden

    def delete(self):
        self.deleted = True


class MockLoginItemsList(list):
    def addObject_(self, item):  # noqa: N802, pylint: disable=invalid-name
        self.append(item)


def test_invalid_state():
    with pytest.raises(ValueError):
        LoginItem(path='/Applications/Dropbox.app', state='hmmm')


def test_inexistent_path(tmpdir):
    p = tmpdir.join('Dropbox.app')

    login_item = LoginItem(path=p.strpath, state='present')
    with pytest.raises(ActionError):
        login_item.process()


@mock.patch('elite.actions.login_item.SystemEventsLoginItem')
@mock.patch('elite.actions.login_item.system_events')
def test_present_installed_identical(  # pylint: disable=unused-argument
    system_events_mock, system_events_login_item_mock, tmpdir
):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = MockLoginItemsList([
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem(p.strpath, hidden=True),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ])
    system_events_mock.loginItems.return_value = login_items

    login_item = LoginItem(path=p.strpath, state='present', hidden=True)
    assert login_item.process() == ActionResponse(changed=False)


@mock.patch('elite.actions.login_item.SystemEventsLoginItem')
@mock.patch('elite.actions.login_item.system_events')
def test_present_installed_hidden_different(  # pylint: disable=unused-argument
    system_events_mock, system_events_login_item_mock, tmpdir
):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = MockLoginItemsList([
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem(p.strpath, hidden=True),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ])
    system_events_mock.loginItems.return_value = login_items

    login_item = LoginItem(path=p.strpath, state='present', hidden=False)
    assert login_item.process() == ActionResponse(changed=True)
    assert login_items[1] == MockLoginItem(p.strpath, hidden=False)


@mock.patch('elite.actions.login_item.SystemEventsLoginItem')
@mock.patch('elite.actions.login_item.system_events')
def test_present_not_installed(system_events_mock, system_events_login_item_mock, tmpdir):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = MockLoginItemsList([
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ])
    system_events_mock.loginItems.return_value = login_items
    system_events_login_item_mock.alloc().initWithProperties_.return_value = MockLoginItem(
        p.strpath, hidden=False
    )

    login_item = LoginItem(path=p.strpath, state='present', hidden=False)
    assert login_item.process() == ActionResponse(changed=True)
    assert system_events_login_item_mock.alloc().initWithProperties_.call_args == mock.call({
        'path': p.strpath,
        'hidden': False
    })
    assert login_items[4] == MockLoginItem(p.strpath, hidden=False)


@mock.patch('elite.actions.login_item.system_events')
def test_absent_not_installed(system_events_mock, tmpdir):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = MockLoginItemsList([
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ])
    system_events_mock.loginItems.return_value = login_items

    login_item = LoginItem(path=p.strpath, state='absent')
    assert login_item.process() == ActionResponse(changed=False)


@mock.patch('elite.actions.login_item.system_events')
def test_absent_installed(system_events_mock, tmpdir):
    p = tmpdir.mkdir('Dropbox.app')
    login_items = MockLoginItemsList([
        MockLoginItem('/Applications/Gmail Notifier.app', hidden=False),
        MockLoginItem(p.strpath, hidden=True),
        MockLoginItem('/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app', hidden=False),
        MockLoginItem('/Applications/BetterSnapTool.app', hidden=False),
        MockLoginItem('/Applications/Flux.app', hidden=False)
    ])
    system_events_mock.loginItems.return_value = login_items

    login_item = LoginItem(path=p.strpath, state='absent')
    assert login_item.process() == ActionResponse(changed=True)
    assert login_items[1].deleted is True
