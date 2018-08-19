import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.json import JSON


def test_json_same(tmpdir):
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


def test_json_different(tmpdir):
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


def test_json_inexistent_values(tmpdir):
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


def test_json_inexistent_path(tmpdir):
    p = tmpdir.join('test.json')

    json = JSON(path=p.strpath, values={'python_lover': False})
    assert json.process() == ActionResponse(changed=True, data={'path': p.strpath})
    assert p.read() == textwrap.dedent('''\
        {
          "python_lover": false
        }
    ''')


def test_json_invalid_file_parsing(tmpdir):
    p = tmpdir.join('test.json')
    p.write(textwrap.dedent('''\
        hmmmm
    '''))

    json = JSON(path=p.strpath, values={'name': 'Fots'})
    with pytest.raises(ActionError):
        json.process()


def test_json_not_writable():
    json = JSON(path='/', values={'name': 'Fots'})
    with pytest.raises(ActionError):
        json.process()
