from . import Action


class BrewUpdate(Action):
    def process(self):
        # Obtain information about the requested package
        brew_update_proc = self.run('brew update', stdout=True)

        # Determine if any changes were made
        if brew_update_proc.stdout.rstrip() == 'Already up-to-date.':
            self.ok()
        else:
            self.changed()


if __name__ == '__main__':
    brew_update = BrewUpdate()
    brew_update.invoke()
