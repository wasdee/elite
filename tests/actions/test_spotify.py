import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.spotify import Spotify

from .helpers import build_open_with_permission_error


def test_determine_pref_path():
    spotify = Spotify(values={'ui.show_friend_feed': False})
    assert spotify.determine_pref_path() == (
        '~/Library/Application Support/Spotify/prefs'
    )


def test_determine_pref_path_username():
    spotify = Spotify(values={'ui.show_friend_feed': False}, username='fots')
    assert spotify.determine_pref_path() == (
        '~/Library/Application Support/Spotify/Users/fots-user/prefs'
    )


def test_pref_boolean_same(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        audio.sync_bitrate_enumeration=3
        audio.play_bitrate_enumeration=0
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'ui.show_friend_feed': False})
    assert spotify.process() == ActionResponse(changed=False, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        audio.sync_bitrate_enumeration=3
        audio.play_bitrate_enumeration=0
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    ''')


def test_pref_invalid_supplied_value(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        audio.sync_bitrate_enumeration=3
        audio.play_bitrate_enumeration=0
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=true
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'wow': 5.5})
    with pytest.raises(ActionError):
        spotify.process()


def test_pref_boolean_different(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        audio.sync_bitrate_enumeration=3
        audio.play_bitrate_enumeration=0
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=true
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'ui.show_friend_feed': False})
    assert spotify.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        audio.sync_bitrate_enumeration=3
        audio.play_bitrate_enumeration=0
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    ''')


def test_pref_boolean_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('prefs').ensure()

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'ui.show_friend_feed': False})
    assert spotify.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        ui.show_friend_feed=false
    ''')


def test_pref_integer_same(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        audio.sync_bitrate_enumeration=4
        audio.play_bitrate_enumeration=4
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'audio.sync_bitrate_enumeration': 4}, username='fots')
    assert spotify.process() == ActionResponse(changed=False, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        audio.sync_bitrate_enumeration=4
        audio.play_bitrate_enumeration=4
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    ''')


def test_pref_integer_different(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        audio.sync_bitrate_enumeration=3
        audio.play_bitrate_enumeration=0
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(
        values={
            'audio.sync_bitrate_enumeration': 4,
            'audio.play_bitrate_enumeration': 4
        },
        username='fots'
    )
    assert spotify.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        audio.sync_bitrate_enumeration=4
        audio.play_bitrate_enumeration=4
        ui.hide_hpto=true
        audio.normalize_v2=false
        app.player.autoplay=false
        ui.show_friend_feed=false
    ''')


def test_pref_integer_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('prefs').ensure()

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'audio.sync_bitrate_enumeration': 4}, username='fots')
    assert spotify.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        audio.sync_bitrate_enumeration=4
    ''')


def test_pref_string_same(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        autologin.canonical_username="fots"
        autologin.username="fots"
        app.autostart-mode="off"
        app.autostart-banner-seen=true
        core.clock_delta=-1
        app.autostart-configured=true
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(
        values={
            'autologin.canonical_username': 'fots',
            'autologin.username': 'fots'
        }
    )
    assert spotify.process() == ActionResponse(changed=False, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        autologin.canonical_username="fots"
        autologin.username="fots"
        app.autostart-mode="off"
        app.autostart-banner-seen=true
        core.clock_delta=-1
        app.autostart-configured=true
    ''')


def test_pref_string_different(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        autologin.canonical_username="pablo"
        autologin.username="pablo"
        app.autostart-mode="off"
        app.autostart-banner-seen=true
        core.clock_delta=-1
        app.autostart-configured=true
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(
        values={
            'autologin.canonical_username': 'fots',
            'autologin.username': 'fots'
        }
    )
    assert spotify.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        autologin.canonical_username="fots"
        autologin.username="fots"
        app.autostart-mode="off"
        app.autostart-banner-seen=true
        core.clock_delta=-1
        app.autostart-configured=true
    ''')


def test_pref_string_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('prefs').ensure()

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'autologin.username': 'fots'})
    assert spotify.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        autologin.username="fots"
    ''')


def test_prefs_invalid_file_parsing(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        hmmmm
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'autologin.username': 'fots'})
    with pytest.raises(ActionError):
        spotify.process()


def test_pref_invalid_file_value(tmpdir, monkeypatch):
    p = tmpdir.join('prefs')
    p.write(textwrap.dedent('''\
        autologin.canonical_username="pablo"
        autologin.username="pablo"
        wow=[]
        app.autostart-configured=true
    '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={
        'autologin.canonical_username': 'fots',
        'autologin.username': 'fots'
    })
    with pytest.raises(ActionError):
        spotify.process()


def test_prefs_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.json')

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(p.strpath))
    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: p.strpath)

    spotify = Spotify(values={'autologin.username': 'fots'})
    with pytest.raises(ActionError):
        spotify.process()
