from . import Action


class Info(Action):
    """
    Causes the script to displaying a suitable info message.

    :param message: the info message to display
    """
    __action_name__ = 'info'

    def __init__(self, message):
        self.message = message

    def process(self):
        return self.ok()
