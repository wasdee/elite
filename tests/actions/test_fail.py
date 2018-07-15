import pytest
from elite.actions import ActionError
from elite.actions.fail import Fail


def test_failure():
    fail = Fail(message='something went wrong')
    with pytest.raises(ActionError):
        fail.process()
