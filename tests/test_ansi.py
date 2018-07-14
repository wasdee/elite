import elite.ansi


def test_move_up():
    assert elite.ansi.move_up(5) == '\033[5A'


def test_move_up_none():
    assert elite.ansi.move_up(0) == ''


def test_move_down():
    assert elite.ansi.move_down(5) == '\033[5B'


def test_move_down_none():
    assert elite.ansi.move_down(0) == ''


def test_move_forward():
    assert elite.ansi.move_forward(5) == '\033[5C'


def test_move_forward_none():
    assert elite.ansi.move_forward(0) == ''


def test_move_backward():
    assert elite.ansi.move_backward(5) == '\033[5D'


def test_move_backward_none():
    assert elite.ansi.move_backward(0) == ''
