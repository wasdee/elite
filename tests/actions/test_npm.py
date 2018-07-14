import shutil

import pytest

from elite.actions import ActionResponse, ActionError
from elite.actions.npm import Npm

from .helpers import CommandMapping, build_run


def test_invalid_state():
    with pytest.raises(ValueError):
        Npm(name='express', state='hmmm', path='/Users/fots/project')


def test_invalid_version_state_combination():
    with pytest.raises(ValueError):
        Npm(name='express', state='latest', version='4.16.3', path='/Users/fots/project')


def test_invalid_version_after_init():
    npm = Npm(name='express', state='latest', path='/Users/fots/project')
    with pytest.raises(ValueError):
        npm.version = '4.16.3'


def test_invalid_state_after_init():
    npm = Npm(name='express', version='4.16.3', path='/Users/fots/project')
    with pytest.raises(ValueError):
        npm.state = 'latest'


def test_invalid_mode():
    with pytest.raises(ValueError):
        Npm(name='express', mode='hmmm', path='/Users/fots/project')


def test_invalid_mode_path_combination():
    with pytest.raises(ValueError):
        Npm(name='express', mode='local')


def test_invalid_mode_after_init():
    npm = Npm(name='express', mode='global')
    with pytest.raises(ValueError):
        npm.mode = 'local'


def test_invalid_path_after_init():
    npm = Npm(name='express', mode='local', path='/Users/fots/project')
    with pytest.raises(ValueError):
        npm.path = None


def test_invalid_list_command(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                returncode=2
            )
        ]
    ))

    npm = Npm(name='express', state='present', executable='npm', path='/Users/fots/project')
    with pytest.raises(ActionError):
        npm.process()


def test_invalid_list_output(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_invalid_output.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='present', executable='npm', path='/Users/fots/project')
    with pytest.raises(ActionError):
        npm.process()


def test_find_executable_found(monkeypatch):
    monkeypatch.setattr(
        shutil, 'which', lambda cmd: '/opt/nodejs/bin/npm' if cmd == 'npm' else None
    )
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    '/opt/nodejs/bin/npm', 'list', '--json', '--depth 0', '--prefix',
                    '/Users/fots/project', 'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='present', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=False)


def test_find_executable_not_found(monkeypatch):
    monkeypatch.setattr(shutil, 'which', lambda cmd: None)
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    '/opt/nodejs/bin/npm', 'list', '--json', '--depth 0', '--prefix',
                    '/Users/fots/project', 'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='present', path='/Users/fots/project')
    with pytest.raises(ActionError):
        npm.process()


def test_global_install(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=['npm', 'list', '--json', '--depth 0', '--global', 'express'],
                stdout_filename='npm_list_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='present', executable='npm', mode='global')
    assert npm.process() == ActionResponse(changed=False)


def test_supplied_path(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='present', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=False)


def test_present_installed(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='present', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=False)


def test_present_not_installed(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['npm', 'install', '--prefix', '/Users/fots/project', 'express']
            )
        ]
    ))

    npm = Npm(name='express', state='present', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=True)


def test_present_with_version_installed_same(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            )
        ]
    ))

    npm = Npm(
        name='express', version='4.16.3', state='present', executable='npm',
        path='/Users/fots/project'
    )
    assert npm.process() == ActionResponse(changed=False)


def test_present_with_version_installed_different(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            ),
            CommandMapping(
                command=['npm', 'install', '--prefix', '/Users/fots/project', 'express@4.15.5']
            )
        ]
    ))

    npm = Npm(
        name='express', version='4.15.5', state='present', executable='npm',
        path='/Users/fots/project'
    )
    assert npm.process() == ActionResponse(changed=True)


def test_present_with_version_not_installed(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['npm', 'install', '--prefix', '/Users/fots/project', 'express@4.16.3']
            )
        ]
    ))

    npm = Npm(
        name='express', version='4.16.3', state='present', executable='npm',
        path='/Users/fots/project'
    )
    assert npm.process() == ActionResponse(changed=True)


def test_latest_installed_and_up_to_date(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            ),
            CommandMapping(
                command=['npm', 'view', '--json', 'express'],
                stdout_filename='npm_view_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='latest', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=False)


def test_latest_installed_but_outdated(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command=['npm', 'view', '--json', 'express'],
                stdout_filename='npm_view_installed_but_outdated.stdout'
            ),
            CommandMapping(
                command=['npm', 'install', '--prefix', '/Users/fots/project', 'express']
            )
        ]
    ))

    npm = Npm(name='express', state='latest', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=True)


def test_latest_not_installed(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_not_installed.stdout'
            ),
            CommandMapping(
                command=['npm', 'install', '--prefix', '/Users/fots/project', 'express']
            )
        ]
    ))

    npm = Npm(name='express', state='latest', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=True)


def test_absent_not_installed(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_not_installed.stdout'
            )
        ]
    ))

    npm = Npm(name='express', state='absent', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=False)


def test_absent_installed(monkeypatch):
    monkeypatch.setattr(Npm, 'run', build_run(
        fixture_subpath='npm',
        command_mappings=[
            CommandMapping(
                command=[
                    'npm', 'list', '--json', '--depth 0', '--prefix', '/Users/fots/project',
                    'express'
                ],
                stdout_filename='npm_list_installed.stdout'
            ),
            CommandMapping(
                command=['npm', 'uninstall', '--prefix', '/Users/fots/project', 'express']
            )
        ]
    ))

    npm = Npm(name='express', state='absent', executable='npm', path='/Users/fots/project')
    assert npm.process() == ActionResponse(changed=True)
