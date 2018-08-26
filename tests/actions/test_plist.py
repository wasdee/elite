import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.plist import Plist

from .helpers import build_open_with_permission_error


PLIST_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
)


def test_invalid_path_domain_empty_combination():
    with pytest.raises(ValueError):
        Plist(values={'python_lover': True})


def test_invalid_domain_empty_after_init():
    plist = Plist(values={'ShowOverlayStatusBar': True}, domain='com.apple.Safari')
    with pytest.raises(ValueError):
        plist.domain = None


def test_invalid_path_domain_both_combination():
    with pytest.raises(ValueError):
        Plist(
            values={'ShowOverlayStatusBar': True},
            domain='com.apple.Safari',
            path='~/Library/Preferences/com.apple.Safari.plist'
        )


def test_invalid_path_both_after_init():
    plist = Plist(values={'ShowOverlayStatusBar': True}, domain='com.apple.Safari')
    with pytest.raises(ValueError):
        plist.path = '~/Library/Preferences/com.apple.Safari.plist'


def test_invalid_domain_both_after_init():
    plist = Plist(
        values={'ShowOverlayStatusBar': True}, path='~/Library/Preferences/com.apple.Safari.plist'
    )
    with pytest.raises(ValueError):
        plist.domain = 'com.apple.Safari'


def test_invalid_container_domain_global_combination():
    with pytest.raises(ValueError):
        Plist(
            values={'AppleInterfaceStyle': 'Dark'},
            container='com.apple.iWork.Pages',
            domain='Apple Global Domain'
        )


def test_invalid_domain_global_after_init():
    plist = Plist(
        values={'NSNavLastRootDirectory': '~/Library/Mobile Documents/com~apple~Pages/Documents'},
        domain='com.apple.iWork.Pages',
        container='com.apple.iWork.Pages'
    )
    with pytest.raises(ValueError):
        plist.domain = 'Apple Global Domain'


def test_invalid_container_global_after_init():
    plist = Plist(
        values={'NSNavLastRootDirectory': '~/Library/Mobile Documents/com~apple~Pages/Documents'},
        domain='Apple Global Domain'
    )
    with pytest.raises(ValueError):
        plist.container = 'com.apple.iWork.Pages'


def test_invalid_container_missing_domain():
    with pytest.raises(ValueError):
        Plist(
            values={
                'NSNavLastRootDirectory': '~/Library/Mobile Documents/com~apple~Pages/Documents'
            },
            container='com.apple.iWork.Pages'
        )


def test_invalid_container_missing_domain_after_init():
    plist = Plist(
        values={'NSNavLastRootDirectory': '~/Library/Mobile Documents/com~apple~Pages/Documents'},
        path=(
            '~/Library/Containers/com.apple.iWork.Pages/Data/'
            'Library/Preferences/com.apple.iWork.Pages.plist'
        )
    )
    with pytest.raises(ValueError):
        plist.container = 'com.apple.iWork.Pages'


def test_invalid_fmt():
    with pytest.raises(ValueError):
        Plist(values={'ShowOverlayStatusBar': True}, domain='com.apple.Safari', fmt='boo')


def test_invalid_fmt_after_init():
    plist = Plist(values={'ShowOverlayStatusBar': True}, domain='com.apple.Safari')
    with pytest.raises(ValueError):
        plist.fmt = 'boo'


def test_plist_binary_fmt(tmpdir):
    p = tmpdir.join('test.plist')
    p.write(PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>interests</key>
            <array>
                <string>chickens</string>
                <string>coding</string>
                <string>music</string>
            </array>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <true/>
        </dict>
        </plist>
    '''))

    plist = Plist(path=p.strpath, values={'python_lover': False}, fmt='binary')
    assert plist.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read_binary().startswith(b'bplist00')


def test_plist_same(tmpdir):
    p = tmpdir.join('test.plist')
    p.write(PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>interests</key>
            <array>
                <string>chickens</string>
                <string>coding</string>
                <string>music</string>
            </array>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <true/>
        </dict>
        </plist>
    '''))

    plist = Plist(path=p.strpath, values={'python_lover': True})
    assert plist.process() == ActionResponse(changed=False, data={'path': p.strpath})
    assert p.read() == PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>interests</key>
            <array>
                <string>chickens</string>
                <string>coding</string>
                <string>music</string>
            </array>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <true/>
        </dict>
        </plist>
    ''')


def test_plist_different(tmpdir):
    p = tmpdir.join('test.plist')
    p.write(PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>interests</key>
            <array>
                <string>chickens</string>
                <string>coding</string>
                <string>music</string>
            </array>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <true/>
        </dict>
        </plist>
    '''))

    plist = Plist(path=p.strpath, values={'python_lover': False})
    assert plist.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>interests</key>
            <array>
                <string>chickens</string>
                <string>coding</string>
                <string>music</string>
            </array>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <false/>
        </dict>
        </plist>
    ''').replace(' ' * 4, '\t')


def test_plist_inexistent_values(tmpdir):
    p = tmpdir.join('test.plist')
    p.write(PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>name</key>
            <string>Fots</string>
        </dict>
        </plist>
    '''))

    plist = Plist(path=p.strpath, values={'python_lover': False})
    assert plist.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <false/>
        </dict>
        </plist>
    ''').replace(' ' * 4, '\t')


def test_plist_inexistent_path(tmpdir):
    p = tmpdir.join('test.plist')

    plist = Plist(path=p.strpath, values={'python_lover': False})
    assert plist.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>python_lover</key>
            <false/>
        </dict>
        </plist>
    ''').replace(' ' * 4, '\t')


def test_plist_invalid_file_parsing(tmpdir):
    p = tmpdir.join('test.plist')
    p.write('hmmmm')

    plist = Plist(path=p.strpath, values={'name': 'Fots'})
    with pytest.raises(ActionError):
        plist.process()


def test_plist_source(tmpdir):
    s = tmpdir.join('source.plist')
    s.write(PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>name</key>
            <string>Fots</string>
            <key>happy</key>
            <true/>
        </dict>
        </plist>
    '''))

    p = tmpdir.join('test.plist')
    p.write(PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>country</key>
            <string>Australia</string>
            <key>happy</key>
            <false/>
            <key>python_lover</key>
            <true/>
        </dict>
        </plist>
    '''))

    plist = Plist(path=p.strpath, source=s.strpath, values={'python_lover': False})
    assert plist.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <dict>
            <key>country</key>
            <string>Australia</string>
            <key>happy</key>
            <true/>
            <key>name</key>
            <string>Fots</string>
            <key>python_lover</key>
            <false/>
        </dict>
        </plist>
    ''').replace(' ' * 4, '\t')


def test_plist_source_inexistent(tmpdir):
    s = tmpdir.join('source.plist')
    p = tmpdir.join('test.plist')

    plist = Plist(path=p.strpath, source=s.strpath, values={'python_lover': False})
    with pytest.raises(ActionError):
        plist.process()


def test_plist_source_invalid(tmpdir):
    s = tmpdir.join('source.plist')
    s.write('hmmmm')
    p = tmpdir.join('test.plist')

    plist = Plist(path=p.strpath, source=s.strpath, values={'python_lover': False})
    with pytest.raises(ActionError):
        plist.process()


def test_plist_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.json')

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(p.strpath))

    plist = Plist(path=p.strpath, values={'name': 'Fots'})
    with pytest.raises(ActionError):
        plist.process()


def test_determine_plist_path_path():
    plist = Plist(
        values={'ShowOverlayStatusBar': True},
        path='~/Library/Preferences/com.apple.Safari.plist'
    )
    assert plist.determine_plist_path() == '~/Library/Preferences/com.apple.Safari.plist'


def test_determine_plist_path_domain():
    plist = Plist(
        values={'ShowOverlayStatusBar': True},
        domain='com.apple.Safari'
    )
    assert plist.determine_plist_path() == '~/Library/Preferences/com.apple.Safari.plist'


def test_determine_plist_path_domain_global():
    plist = Plist(
        values={'AppleInterfaceStyle': 'Dark'},
        domain='Apple Global Domain'
    )
    assert plist.determine_plist_path() == '~/Library/Preferences/.GlobalPreferences.plist'


def test_determine_plist_path_container():
    plist = Plist(
        values={'NSNavLastRootDirectory': '~/Library/Mobile Documents/com~apple~Pages/Documents'},
        domain='com.apple.iWork.Pages',
        container='com.apple.iWork.Pages'
    )
    assert plist.determine_plist_path() == (
        '~/Library/Containers/com.apple.iWork.Pages/Data/'
        'Library/Preferences/com.apple.iWork.Pages.plist'
    )
