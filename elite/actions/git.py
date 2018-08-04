import os

from . import FileAction


class Git(FileAction):
    def __init__(self, repo, path, branch='master', remote='origin', **kwargs):
        self.repo = repo
        self.path = path
        self.branch = branch
        self.remote = remote
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Check if the repository already exists in the destination path
        if os.path.exists(os.path.join(path, '.git', 'config')):
            # Verify that the existing repo originates from the same remote
            git_remote_proc = self.run(
                ['git', 'remote', 'get-url', self.remote],
                fail_error='unable to check existing remote'
            )

            if git_remote_proc.stdout.rstrip() == self.repo:
                # Verify that the existing repo is on the correct branch
                git_branch_proc = self.run(
                    ['git', 'symbolic-ref', '--short', 'HEAD'], cwd=path, stdout=True,
                    fail_error='unable to check existing repository branch'
                )

                # Currently checked out repo is on the correct branch
                if git_branch_proc.stdout.rstrip() == self.branch:
                    return self.ok()
                # Checked out repo is on the wrong branch and must be switched
                else:
                    self.run(
                        ['git', 'checkout', '--quiet', self.branch], cwd=path,
                        fail_error='unable to checkout requested branch'
                    )
                    return self.changed()
            else:
                # The remote differs so we clean up the destination before cloning the repo
                self.remove(path)

        # Clone the requested repository and branch
        self.run(
            ['git', 'clone', '--quiet', '-b', self.branch, self.repo, path],
            fail_error='unable to clone git repository'
        )

        # Clone was successful
        return self.changed()
