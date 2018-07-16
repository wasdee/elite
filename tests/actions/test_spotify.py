import os
import tempfile
import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.spotify import Spotify


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


def test_pref_boolean_same(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            audio.sync_bitrate_enumeration=3
            audio.play_bitrate_enumeration=0
            ui.hide_hpto=true
            audio.normalize_v2=false
            app.player.autoplay=false
            ui.show_friend_feed=false
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'ui.show_friend_feed': False})
        assert spotify.process() == ActionResponse(changed=False, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                audio.sync_bitrate_enumeration=3
                audio.play_bitrate_enumeration=0
                ui.hide_hpto=true
                audio.normalize_v2=false
                app.player.autoplay=false
                ui.show_friend_feed=false
            ''')
    finally:
        os.remove(fp.name)


def test_pref_invalid_supplied_value(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            audio.sync_bitrate_enumeration=3
            audio.play_bitrate_enumeration=0
            ui.hide_hpto=true
            audio.normalize_v2=false
            app.player.autoplay=false
            ui.show_friend_feed=true
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'wow': 5.5})
        with pytest.raises(ActionError):
            spotify.process()
    finally:
        os.remove(fp.name)


def test_pref_boolean_different(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            audio.sync_bitrate_enumeration=3
            audio.play_bitrate_enumeration=0
            ui.hide_hpto=true
            audio.normalize_v2=false
            app.player.autoplay=false
            ui.show_friend_feed=true
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'ui.show_friend_feed': False})
        assert spotify.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                audio.sync_bitrate_enumeration=3
                audio.play_bitrate_enumeration=0
                ui.hide_hpto=true
                audio.normalize_v2=false
                app.player.autoplay=false
                ui.show_friend_feed=false
            ''')
    finally:
        os.remove(fp.name)


def test_pref_boolean_inexistent(monkeypatch):
    fp = tempfile.NamedTemporaryFile('w', delete=False)

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'ui.show_friend_feed': False})
        assert spotify.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                ui.show_friend_feed=false
            ''')
    finally:
        os.remove(fp.name)


def test_pref_integer_same(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            audio.sync_bitrate_enumeration=4
            audio.play_bitrate_enumeration=4
            ui.hide_hpto=true
            audio.normalize_v2=false
            app.player.autoplay=false
            ui.show_friend_feed=false
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'audio.sync_bitrate_enumeration': 4}, username='fots')
        assert spotify.process() == ActionResponse(changed=False, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                audio.sync_bitrate_enumeration=4
                audio.play_bitrate_enumeration=4
                ui.hide_hpto=true
                audio.normalize_v2=false
                app.player.autoplay=false
                ui.show_friend_feed=false
            ''')
    finally:
        os.remove(fp.name)


def test_pref_integer_different(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            audio.sync_bitrate_enumeration=3
            audio.play_bitrate_enumeration=0
            ui.hide_hpto=true
            audio.normalize_v2=false
            app.player.autoplay=false
            ui.show_friend_feed=false
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(
            values={
                'audio.sync_bitrate_enumeration': 4,
                'audio.play_bitrate_enumeration': 4
            },
            username='fots'
        )
        assert spotify.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                audio.sync_bitrate_enumeration=4
                audio.play_bitrate_enumeration=4
                ui.hide_hpto=true
                audio.normalize_v2=false
                app.player.autoplay=false
                ui.show_friend_feed=false
            ''')
    finally:
        os.remove(fp.name)


def test_pref_integer_inexistent(monkeypatch):
    fp = tempfile.NamedTemporaryFile('w', delete=False)

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'audio.sync_bitrate_enumeration': 4}, username='fots')
        assert spotify.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                audio.sync_bitrate_enumeration=4
            ''')
    finally:
        os.remove(fp.name)


def test_pref_string_same(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            autologin.canonical_username="fots"
            autologin.username="fots"
            app.autostart-mode="off"
            app.autostart-banner-seen=true
            core.clock_delta=-1
            app.autostart-configured=true
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(
            values={
                'autologin.canonical_username': 'fots',
                'autologin.username': 'fots'
            }
        )
        assert spotify.process() == ActionResponse(changed=False, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                autologin.canonical_username="fots"
                autologin.username="fots"
                app.autostart-mode="off"
                app.autostart-banner-seen=true
                core.clock_delta=-1
                app.autostart-configured=true
            ''')
    finally:
        os.remove(fp.name)


def test_pref_string_different(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            autologin.canonical_username="pablo"
            autologin.username="pablo"
            app.autostart-mode="off"
            app.autostart-banner-seen=true
            core.clock_delta=-1
            app.autostart-configured=true
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(
            values={
                'autologin.canonical_username': 'fots',
                'autologin.username': 'fots'
            }
        )
        assert spotify.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                autologin.canonical_username="fots"
                autologin.username="fots"
                app.autostart-mode="off"
                app.autostart-banner-seen=true
                core.clock_delta=-1
                app.autostart-configured=true
            ''')
    finally:
        os.remove(fp.name)


def test_pref_string_inexistent(monkeypatch):
    fp = tempfile.NamedTemporaryFile('w', delete=False)

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'autologin.username': 'fots'})
        assert spotify.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                autologin.username="fots"
            ''')
    finally:
        os.remove(fp.name)


def test_prefs_invalid_file_parsing(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            hmmmm
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={'autologin.username': 'fots'})
        with pytest.raises(ActionError):
            spotify.process()
    finally:
        os.remove(fp.name)


def test_pref_invalid_file_value(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            autologin.canonical_username="pablo"
            autologin.username="pablo"
            wow=[]
            app.autostart-configured=true
        '''))

    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: fp.name)

    try:
        spotify = Spotify(values={
                'autologin.canonical_username': 'fots',
                'autologin.username': 'fots'
            }
        )
        with pytest.raises(ActionError):
            spotify.process()
    finally:
        os.remove(fp.name)


def test_prefs_not_writable(monkeypatch):
    monkeypatch.setattr(Spotify, 'determine_pref_path', lambda self: '/')

    spotify = Spotify(values={'autologin.username': 'fots'})
    with pytest.raises(ActionError):
        spotify.process()
