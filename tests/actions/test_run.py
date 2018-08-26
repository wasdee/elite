from elite.actions import ActionResponse
from elite.actions.run import Run


def test_normal():
    run = Run(command=['echo', '-n', 'hi'])
    assert run.process() == ActionResponse(changed=True, data={
        'stdout': 'hi', 'stderr': '', 'return_code': 0
    })


def test_shell():
    run = Run(command='>&2 echo -n hi', shell='/bin/bash')
    assert run.process() == ActionResponse(changed=True, data={
        'stdout': '', 'stderr': 'hi', 'return_code': 0
    })


def test_creates_inexistent(tmpdir):
    p = tmpdir.join('test')

    run = Run(command=['echo', '-n', 'hi'], creates=p.strpath)
    assert run.process() == ActionResponse(changed=True, data={
        'stdout': 'hi', 'stderr': '', 'return_code': 0
    })


def test_creates_exists(tmpdir):
    p = tmpdir.join('test').ensure()

    run = Run(command=['echo', '-n', 'hi'], creates=p.strpath)
    assert run.process() == ActionResponse(changed=False)


def test_removes_inexistent(tmpdir):
    p = tmpdir.join('test')

    run = Run(command=['echo', '-n', 'hi'], removes=p.strpath)
    assert run.process() == ActionResponse(changed=False)


def test_removes_exists(tmpdir):
    p = tmpdir.join('test').ensure()

    run = Run(command=['echo', '-n', 'hi'], removes=p.strpath)
    assert run.process() == ActionResponse(changed=True, data={
        'stdout': 'hi', 'stderr': '', 'return_code': 0
    })


def test_unless_ok():
    run = Run(command=['echo', '-n', 'hi'], unless='true')
    assert run.process() == ActionResponse(changed=False)


def test_unless_failed():
    run = Run(command=['echo', '-n', 'hi'], unless='false')
    assert run.process() == ActionResponse(changed=True, data={
        'stdout': 'hi', 'stderr': '', 'return_code': 0
    })
