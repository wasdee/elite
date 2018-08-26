import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.json import JSON

from .helpers import build_open_with_permission_error


def test_same(tmpdir):
    p = tmpdir.join('test.json')
    p.write(textwrap.dedent('''\
        {
            "name": "Fots",
            "python_lover": true,
            "interests": ["chickens", "coding", "music"]
        }
    '''))

    json = JSON(path=p.strpath, values={'python_lover': True})
    assert json.process() == ActionResponse(changed=False, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        {
            "name": "Fots",
            "python_lover": true,
            "interests": ["chickens", "coding", "music"]
        }
    ''')


def test_different(tmpdir):
    p = tmpdir.join('test.json')
    p.write(textwrap.dedent('''\
        {
            "name": "Fots",
            "python_lover": true,
            "interests": ["chickens", "coding", "music"]
        }
    '''))

    json = JSON(path=p.strpath, values={'python_lover': False})
    assert json.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        {
          "name": "Fots",
          "python_lover": false,
          "interests": [
            "chickens",
            "coding",
            "music"
          ]
        }
    ''')


def test_values_inexistent(tmpdir):
    p = tmpdir.join('test.json')
    p.write(textwrap.dedent('''\
        {
            "name": "Fots"
        }
    '''))

    json = JSON(path=p.strpath, values={'python_lover': False})
    assert json.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        {
          "name": "Fots",
          "python_lover": false
        }
    ''')


def test_path_inexistent(tmpdir):
    p = tmpdir.join('test.json')

    json = JSON(path=p.strpath, values={'python_lover': False})
    assert json.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        {
          "python_lover": false
        }
    ''')


def test_file_parsing_invalid(tmpdir):
    p = tmpdir.join('test.json')
    p.write(textwrap.dedent('''\
        hmmmm
    '''))

    json = JSON(path=p.strpath, values={'name': 'Fots'})
    with pytest.raises(ActionError):
        json.process()


def test_not_writable(tmpdir, monkeypatch):
    p = tmpdir.join('test.json')

    monkeypatch.setattr('builtins.open', build_open_with_permission_error(p.strpath))

    json = JSON(path=p.strpath, values={'name': 'Fots'})
    with pytest.raises(ActionError):
        json.process()
