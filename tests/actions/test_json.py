import os
import tempfile
import textwrap

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.json import JSON


def test_json_same(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            {
                "name": "Fots",
                "python_lover": true,
                "interests": ["chickens", "coding", "music"]
            }
        '''))

    try:
        json = JSON(path=fp.name, values={'python_lover': True})
        assert json.process() == ActionResponse(changed=False, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                {
                    "name": "Fots",
                    "python_lover": true,
                    "interests": ["chickens", "coding", "music"]
                }
            ''')
    finally:
        os.remove(fp.name)


def test_json_different(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            {
                "name": "Fots",
                "python_lover": true,
                "interests": ["chickens", "coding", "music"]
            }
        '''))

    try:
        json = JSON(path=fp.name, values={'python_lover': False})
        assert json.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
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
    finally:
        os.remove(fp.name)


def test_json_inexistent_values(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            {
                "name": "Fots"
            }
        '''))

    try:
        json = JSON(path=fp.name, values={'python_lover': False})
        assert json.process() == ActionResponse(changed=True, data={'path': fp.name})

        with open(fp.name, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                {
                  "name": "Fots",
                  "python_lover": false
                }
            ''')
    finally:
        os.remove(fp.name)


def test_json_inexistent_path(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, 'temp.json')

        json = JSON(path=path, values={'python_lover': False})
        assert json.process() == ActionResponse(changed=True, data={'path': path})

        with open(path, 'r') as fp:
            assert fp.read() == textwrap.dedent('''\
                {
                  "python_lover": false
                }
            ''')


def test_json_invalid_file_parsing(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as fp:
        fp.write(textwrap.dedent('''\
            hmmmm
        '''))

    try:
        json = JSON(path=fp.name, values={'name': 'Fots'})
        with pytest.raises(ActionError):
            json.process()
    finally:
        os.remove(fp.name)


def test_prefs_not_writable(monkeypatch):
    json = JSON(path='/', values={'name': 'Fots'})
    with pytest.raises(ActionError):
        json.process()
