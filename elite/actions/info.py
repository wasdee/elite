from . import Action


class Info(Action):
    """
    Causes the script to displaying a suitable info message.

    :param message: the info message to display
    """

    def __init__(self, message, **kwargs):
        self.message = message
        super().__init__(**kwargs)

    def process(self):
        return self.ok()
