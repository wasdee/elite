from . import Argument, Action


class Info(Action):
    def process(self, message):
        self.ok()


if __name__ == '__main__':
    info = Info(
        Argument('message')
    )
    info.invoke()
