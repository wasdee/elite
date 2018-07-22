from . import Action, ActionError


class Fail(Action):
    """
    Causes the script to fail after displaying a suitable error message.

    :param message: the error message to display
    """

    def __init__(self, message, **kwargs):
        self.message = message
        super().__init__(**kwargs)

    def process(self):
        raise ActionError
