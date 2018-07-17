from . import Action


class BrewUpdate(Action):
    """Updates all Homebrew package formulas to their latest versions."""

    __action_name__ = 'brew_update'

    def process(self):
        # Obtain information about the requested package
        brew_update_proc = self.run(['brew', 'update'], stdout=True)

        # Determine if any changes were made
        if brew_update_proc.stdout.rstrip() == 'Already up-to-date.':
            return self.ok()
        else:
            return self.changed()
