import os

from . import Action, Argument


class Git(Action):
    def process(self, repo, path, branch):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)

        # Check if the repository already exists in the destination path
        if os.path.exists(os.path.join(path, '.git', 'config')):
            # Verify that the existing repo is on the correct branch
            git_branch_proc = self.run(
                'git symbolic-ref --short HEAD', cwd=path, stdout=True,
                fail_error='unable to check existing repository branch'
            )

            # Currently checked out repo is on the correct branch
            if git_branch_proc.stdout.rstrip() == branch:
                self.ok()
            # Checked out repo is on the wrong branch and must be switched
            else:
                self.run(
                    ['git', 'checkout', branch], cwd=path,
                    fail_error='unable to checkout requested branch'
                )
                self.changed()

        # Build the clone command
        git_command = ['git', 'clone', '--quiet']
        if branch:
            git_command.extend(['-b', branch])
        git_command.extend([repo, path])

        # Run the command and check for failures
        self.run(git_command, fail_error='unable to clone git repository')

        # Clone was successful
        self.changed()


if __name__ == '__main__':
    git = Git(
        Argument('repo'),
        Argument('path'),
        Argument('branch', default='master')
    )
    git.invoke()
