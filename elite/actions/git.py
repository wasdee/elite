import os

from . import Action


class Git(Action):
    __action_name__ = 'git'

    def __init__(self, repo, path, branch='master', **kwargs):
        self.repo = repo
        self.path = path
        self.branch = branch
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Check if the repository already exists in the destination path
        if os.path.exists(os.path.join(path, '.git', 'config')):
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
                    ['git', 'checkout', self.branch], cwd=path,
                    fail_error='unable to checkout requested branch'
                )
                return self.changed()

        # Build the clone command
        git_command = ['git', 'clone', '--quiet']
        if self.branch:
            git_command.extend(['-b', self.branch])
        git_command.extend([self.repo, path])

        # Run the command and check for failures
        self.run(git_command, fail_error='unable to clone git repository')

        # Clone was successful
        return self.changed()
