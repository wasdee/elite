import os
import plistlib
import re
import shutil

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.notifications import Notifications, get_ncprefs_plist_path


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_argument_alert_style_invalid():
    with pytest.raises(ValueError):
        Notifications(path='/Applications/Dropbox.app', alert_style='hmmm')


def test_get_ncprefs_plist_path():
    assert re.match(
        '/Users/.*/Library/Preferences/com.apple.ncprefs.plist', get_ncprefs_plist_path()
    )


def test_path_invalid(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Boo.app', alert_style='Alerts')
    with pytest.raises(ActionError):
        notifications.process()


def test_ncprefs_plist_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', alert_style='Alerts')
    with pytest.raises(ActionError):
        notifications.process()


def test_ncprefs_plist_parsing_invalid(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    p.write('hmmmm')

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', alert_style='Alerts')
    with pytest.raises(ActionError):
        notifications.process()


def test_alert_style_same_default(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', alert_style='Alerts')
    assert notifications.process() == ActionResponse(changed=False)


def test_alert_style_same_modified(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', alert_style='None')
    assert notifications.process() == ActionResponse(changed=False)


def test_alert_style_different_none(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', alert_style='None')
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][6]['path'] == '/Applications/Dropbox.app'
    # 0b1xxxxxx: Permanent bit indicating that alert style has been changed
    # 0bx000xxx: Set the alert style to 'None'
    assert ncprefs_plist['apps'][6]['flags'] == 0b1000110


def test_alert_style_different_banners(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', alert_style='Banners')
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][6]['path'] == '/Applications/Dropbox.app'
    # 0b1xxxxxx: Permanent bit indicating that alert style has been changed
    # 0bx001xxx: Set the alert style to 'Banners'
    assert ncprefs_plist['apps'][6]['flags'] == 0b1001110


def test_alert_style_different_alerts(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', alert_style='Alerts')
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][13]['path'] == '/Applications/Cog.app'
    # 0b1xxxxxx: Permanent bit indicating that alert style has been changed
    # 0bx010xxx: Set the alert style to 'Alerts'
    assert ncprefs_plist['apps'][13]['flags'] == 0b1000101010001


def test_lock_screen_same(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', lock_screen=True)
    assert notifications.process() == ActionResponse(changed=False)


def test_lock_screen_different_on(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', lock_screen=True)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][13]['path'] == '/Applications/Cog.app'
    # 0b0xxxxxxxxxxxx: Enable lock screen notifications
    assert ncprefs_plist['apps'][13]['flags'] == 0b0000101000001


def test_lock_screen_different_off(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', lock_screen=False)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][6]['path'] == '/Applications/Dropbox.app'
    # 0b1xxxxxxxxxxxx: Disable lock screen notifications
    assert ncprefs_plist['apps'][6]['flags'] == 0b1000000010110


def test_notification_center_same_default(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', notification_center=True)
    assert notifications.process() == ActionResponse(changed=False)


def test_notification_center_same_modified(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', notification_center=False)
    assert notifications.process() == ActionResponse(changed=False)


def test_notification_center_different_on(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', notification_center=True)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][13]['path'] == '/Applications/Cog.app'
    # 0b1xxxxxxxx: Permanent bit indicating that notification center settings have been changed
    # 0b0: Enable notification center notifications
    assert ncprefs_plist['apps'][13]['flags'] == 0b1000101000000


def test_notification_center_different_off(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', notification_center=False)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][6]['path'] == '/Applications/Dropbox.app'
    # 0b1xxxxxxxx: Permanent bit indicating that notification center settings have been changed
    # 0b1: Disable notification center notifications
    assert ncprefs_plist['apps'][6]['flags'] == 0b100010111


def test_badge_app_icon_same(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', badge_app_icon=True)
    assert notifications.process() == ActionResponse(changed=False)


def test_badge_app_icon_different_on(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', badge_app_icon=True)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][13]['path'] == '/Applications/Cog.app'
    # 0b1x: Enable badge app icon for notifications
    assert ncprefs_plist['apps'][13]['flags'] == 0b1000101000011


def test_badge_app_icon_different_off(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', badge_app_icon=False)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][6]['path'] == '/Applications/Dropbox.app'
    # 0b0x: Disable badge app icon for notifications
    assert ncprefs_plist['apps'][6]['flags'] == 0b10100


def test_sound_same(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', sound=True)
    assert notifications.process() == ActionResponse(changed=False)


def test_sound_different_on(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Cog.app', sound=True)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][13]['path'] == '/Applications/Cog.app'
    # 0b1xx: Enable sound for notifications
    assert ncprefs_plist['apps'][13]['flags'] == 0b1000101000101


def test_sound_different_off(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)

    notifications = Notifications(path='/Applications/Dropbox.app', sound=False)
    assert notifications.process() == ActionResponse(changed=True)

    with open(p.strpath, 'rb') as fp:
        ncprefs_plist = plistlib.load(fp)

    assert ncprefs_plist['apps'][6]['path'] == '/Applications/Dropbox.app'
    # 0b0xx: Disable sound for notifications
    assert ncprefs_plist['apps'][6]['flags'] == 0b10010


def test_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('com.apple.ncprefs.plist')
    shutil.copy(os.path.join(FIXTURE_PATH, 'notifications', 'com.apple.ncprefs.plist'), p.strpath)

    builtins_open = open

    def open_(  # pylint: disable=unused-argument
        file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True,
        opener=None
    ):
        if file == p.strpath and mode == 'wb':
            raise PermissionError(13, 'Permission denied', file)
        else:
            return builtins_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    monkeypatch.setattr('elite.actions.notifications.get_ncprefs_plist_path', lambda: p.strpath)
    monkeypatch.setattr('builtins.open', open_)

    notifications = Notifications(path='/Applications/Dropbox.app', sound=False)
    with pytest.raises(ActionError):
        notifications.process()
