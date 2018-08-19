import os
import shutil
import tempfile
import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.package import Package

from .helpers import CommandMapping, build_run


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')
PLIST_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
)


def test_package_inexistent(tmpdir):
    p = tmpdir.join('something.pkg')

    package = Package(path=p.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_insufficient_permissions(tmpdir):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()

    package = Package(path=kp.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_no_pkg_refs(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.mkdir('package')
    pp.join('Distribution').write(textwrap.dedent('''\
        <?xml version="1.0" encoding="utf-8" standalone="no"?>
        <pkg-info>
        </pkg-info>
    '''))

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)

    package = Package(path=kp.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_no_package_info_identifier(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.join('package')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'package', 'pkg'), pp.strpath)
    pp.join('West Africa Factory Content.pkg/PackageInfo').write(textwrap.dedent('''\
        <?xml version="1.0" encoding="utf-8" standalone="no"?>
        <pkg-info>
        </pkg-info>
    '''))

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)

    package = Package(path=kp.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_missing_disribution(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.join('package')

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)

    package = Package(path=kp.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_invalid_disribution(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.mkdir('package')
    pp.join('Distribution').write('boo')

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)

    package = Package(path=kp.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_invalid_pkginfo(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.join('package')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'package', 'pkg'), pp.strpath)
    pp.join('West Africa Factory Content.pkg/PackageInfo').write('boo')

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)

    package = Package(path=kp.strpath)
    with pytest.raises(ActionError):
        package.process()


def test_package_not_installed(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.join('package')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'package', 'pkg'), pp.strpath)
    rp = tmpdir.mkdir('receipts')

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            ),
            CommandMapping(
                command=[
                    'installer',
                    '-package', kp.strpath,
                    '-target', '/'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)
    Package.receipts_dirs = [rp.strpath]

    package = Package(path=kp.strpath)
    assert package.process() == ActionResponse(changed=True)


def test_package_installed(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.join('package')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'package', 'pkg'), pp.strpath)
    rp = tmpdir.join('receipts')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'package', 'receipts'), rp.strpath)

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            ),
            CommandMapping(
                command=[
                    'installer',
                    '-package', kp.strpath,
                    '-target', '/'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)
    Package.receipts_dirs = [rp.strpath]

    package = Package(path=kp.strpath)
    assert package.process() == ActionResponse(changed=False)


def test_package_choices(tmpdir, monkeypatch):
    kp = tmpdir.join('West Africa 1.3.0 Installer Mac.pkg').ensure()
    pp = tmpdir.join('package')
    shutil.copytree(os.path.join(FIXTURE_PATH, 'package', 'pkg'), pp.strpath)
    rp = tmpdir.mkdir('receipts')
    cp = tmpdir.join('choices')

    monkeypatch.setattr(Package, 'run', build_run(
        fixture_subpath='cask',
        command_mappings=[
            CommandMapping(
                command=[
                    'xar', '-xf', kp.strpath,
                    '-C', pp.strpath,
                    '^Distribution$', '^PackageInfo$', '/PackageInfo$'
                ],
                returncode=0
            ),
            CommandMapping(
                command=[
                    'installer',
                    '-applyChoiceChangesXML', cp.strpath,
                    '-package', kp.strpath,
                    '-target', '/'
                ],
                returncode=0
            )
        ]
    ))
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: pp.strpath)
    monkeypatch.setattr(tempfile, 'mkstemp', lambda: (11, cp.strpath))
    monkeypatch.setattr(os, 'geteuid', lambda: 0)
    monkeypatch.setattr(os, 'remove', lambda path, *, dir_fd=None: None)
    Package.receipts_dirs = [rp.strpath]

    package = Package(
        path=kp.strpath,
        choices=[
            {
                'choiceIdentifier': 'WestAfrica_Library',
                'choiceAttribute': 'customLocation',
                'attributeSetting': '/Volumes/Sample Libraries/Kontakt/Native Instruments'
            }
        ]
    )
    assert package.process() == ActionResponse(changed=True)
    assert cp.read() == PLIST_HEADER + textwrap.dedent('''\
        <plist version="1.0">
        <array>
            <dict>
                <key>attributeSetting</key>
                <string>/Volumes/Sample Libraries/Kontakt/Native Instruments</string>
                <key>choiceAttribute</key>
                <string>customLocation</string>
                <key>choiceIdentifier</key>
                <string>WestAfrica_Library</string>
            </dict>
        </array>
        </plist>
    '''.replace(' ' * 4, '\t'))
