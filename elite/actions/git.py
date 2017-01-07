import os

from . import Argument, Action


class Git(Action):
    def process(self, repo, destination, branch):
        # Check if the repository already exists in the destination
        if os.path.exists(os.path.join(destination, '.git', 'config')):
            # Verify that the existing repo is on the correct branch
            git_branch_proc = self.run(
                'git symbolic-ref --short HEAD', cwd=destination, stdout=True,
                fail_error='unable to check existing repository branch'
            )

            # Currently checked out repo is on the correct branch
            if git_branch_proc.stdout.strip() == branch:
                self.ok()
            # Checked out repo is on the wrong branch and must be switched
            else:
                self.run(
                    ['git', 'checkout', branch], cwd=destination,
                    fail_error='unable to checkout requested branch'
                )
                self.changed('existing repo found and switched to requested branch')

        # Build the clone command
        git_command = ['git', 'clone', '--quiet']
        if branch:
            git_command.extend(['-b', branch])
        git_command.extend([repo, destination])

        # Run the command and check for failures
        self.run(git_command, fail_error='unable to clone git repository')

        # Clone was successful
        self.changed('repository cloned successfully')


if __name__ == '__main__':
    git = Git(
        Argument('repo'),
        Argument('destination'),
        Argument('branch', default='master')
    )
    git.invoke()
