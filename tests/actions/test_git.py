import textwrap

from elite.actions import ActionResponse
from elite.actions.git import Git

from .helpers import CommandMapping, build_run


def test_path_inexistent(tmpdir, monkeypatch):
    p = tmpdir.join('painter')

    repo = 'https://github.com/fgimian/painter.git'
    path = p.strpath

    monkeypatch.setattr(Git, 'run', build_run(
        fixture_subpath='git',
        command_mappings=[
            CommandMapping(
                command=['git', 'clone', '--quiet', '-b', 'master', repo, path]
            )
        ]
    ))

    git = Git(repo=repo, path=path)
    assert git.process() == ActionResponse(changed=True)


def test_different_remote_existing(tmpdir, monkeypatch):
    p = tmpdir.mkdir('painter')
    p.join('.git/config').ensure()

    repo = 'https://github.com/fgimian/painter.git'
    path = p.strpath

    monkeypatch.setattr(Git, 'run', build_run(
        fixture_subpath='git',
        command_mappings=[
            CommandMapping(
                stdout=textwrap.dedent('''\
                    https://github.com/fgimian/paramiko-expect.git
                '''),
                command=['git', 'remote', 'get-url', 'github']
            ),
            CommandMapping(
                command=['git', 'clone', '--quiet', '-b', 'master', repo, path]
            )
        ]
    ))

    git = Git(repo=repo, path=path, remote='github')
    assert git.process() == ActionResponse(changed=True)
    # The action should have deleted the original directory and cloned the new repo, but since
    # we're mocking the clone command, the directory should no longer exist.
    assert not p.exists()


def test_different_branch_existing(tmpdir, monkeypatch):
    p = tmpdir.mkdir('painter')
    p.join('.git/config').ensure()

    repo = 'https://github.com/fgimian/painter.git'
    path = p.strpath

    monkeypatch.setattr(Git, 'run', build_run(
        fixture_subpath='git',
        command_mappings=[
            CommandMapping(
                stdout=textwrap.dedent('''\
                    https://github.com/fgimian/painter.git
                '''),
                command=['git', 'remote', 'get-url', 'origin']
            ),
            CommandMapping(
                stdout=textwrap.dedent('''\
                    master
                '''),
                command=['git', 'symbolic-ref', '--short', 'HEAD']
            ),
            CommandMapping(
                command=['git', 'checkout', '--quiet', 'some-feature-branch']
            )
        ]
    ))

    git = Git(repo=repo, path=path, branch='some-feature-branch')
    assert git.process() == ActionResponse(changed=True)


def test_same_existing(tmpdir, monkeypatch):
    p = tmpdir.join('painter')
    p.join('.git/config').ensure()

    repo = 'https://github.com/fgimian/painter.git'
    path = p.strpath

    monkeypatch.setattr(Git, 'run', build_run(
        fixture_subpath='git',
        command_mappings=[
            CommandMapping(
                stdout=textwrap.dedent('''\
                    https://github.com/fgimian/painter.git
                '''),
                command=['git', 'remote', 'get-url', 'origin']
            ),
            CommandMapping(
                stdout=textwrap.dedent('''\
                    master
                '''),
                command=['git', 'symbolic-ref', '--short', 'HEAD']
            )
        ]
    ))

    git = Git(repo=repo, path=path)
    assert git.process() == ActionResponse(changed=False)
