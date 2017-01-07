from . import Argument, Action


class Fail(Action):
    def process(self, message):
        self.fail(message)


if __name__ == '__main__':
    fail = Fail(
        Argument('message')
    )
    fail.invoke()
