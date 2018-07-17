from . import Action, ActionError


class Fail(Action):
    """
    Causes the script to fail after displaying a suitable error message.

    :param message: the error message to display
    """

    __action_name__ = 'fail'

    def __init__(self, message):
        self.message = message

    def process(self):
        raise ActionError
