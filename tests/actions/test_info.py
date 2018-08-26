from elite.actions import ActionResponse
from elite.actions.info import Info


def test_information():
    info = Info(message='some information')
    assert info.process() == ActionResponse(changed=False)
