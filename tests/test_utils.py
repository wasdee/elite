import pytest
from elite.utils import ReversibleDict, batch, deep_equal, deep_merge, generate_uuid


def test_reversible_dict_lookup():
    data = ReversibleDict({
        'value1': 1,
        'value2': 2,
        'value3': 3
    })

    assert data['value1'] == 1
    assert data['value2'] == 2
    assert data['value3'] == 3
    assert data.lookup(1) == 'value1'
    assert data.lookup(2) == 'value2'
    assert data.lookup(3) == 'value3'


def test_reversible_dict_duplicate_values():
    with pytest.raises(ValueError):
        ReversibleDict({
            'value1': 1,
            'value2': 2,
            'value3': 1
        })


def test_reversible_dict_delete_item():
    data = ReversibleDict({
        'value1': 1,
        'value2': 2,
        'value3': 3
    })
    del data['value2']

    assert data['value1'] == 1
    assert 'value2' not in data
    assert data['value3'] == 3
    assert data.lookup(1) == 'value1'
    with pytest.raises(KeyError):
        data.lookup(2)
    assert data.lookup(3) == 'value3'


def test_reversible_dict_set_item():
    data = ReversibleDict({
        'value1': 1,
        'value2': 2,
        'value3': 3
    })
    data['value4'] = 4

    assert data['value1'] == 1
    assert data['value2'] == 2
    assert data['value3'] == 3
    assert data.lookup(1) == 'value1'
    assert data.lookup(2) == 'value2'
    assert data.lookup(3) == 'value3'
    assert data.lookup(4) == 'value4'


def test_deep_equal_same():
    source = {
        'name': 'fots',
        'things': {'a': 'b'},
        'deeper': {
            'and_deeper': {'key': 'value'}
        }
    }
    destination = {
        'name': 'fots',
        'age': 3,
        'happy': True,
        'things': {'a': 'b'},
        'deeper': {
            'and_deeper': {'key': 'value'}
        }
    }

    assert deep_equal(source, destination)


def test_deep_equal_different():
    source = {
        'name': 'fots',
        'things': {'a': 'b'},
        'deeper': {
            'and_deeper': {'key': 'hmmm'}
        }
    }
    destination = {
        'name': 'fots',
        'age': 3,
        'happy': True,
        'things': {'a': 'b'},
        'deeper': {
            'and_deeper': {'key': 'value'}
        }
    }

    assert not deep_equal(source, destination)


def test_deep_merge():
    source = {
        'name': 'fots',
        'things': {'a': 'b'},
        'deeper': {
            'and_deeper': {'key': 'value'}
        }
    }
    destination = {
        'age': 20,
        'things': {'b': 'c'},
        'deeper': {
            'and_deeper': {'bleh': 'blah'}
        }
    }
    deep_merge(source, destination)

    assert destination == {
        'name': 'fots',
        'age': 20,
        'things': {'a': 'b', 'b': 'c'},
        'deeper': {
            'and_deeper': {'key': 'value', 'bleh': 'blah'}
        }
    }


def test_batch_exact_split():
    assert list(batch(items=[1, 2, 3, 4], batch_size=2)) == [[1, 2], [3, 4]]


def test_batch_split_with_remainder():
    assert list(batch(items=[1, 2, 3, 4, 5], batch_size=3)) == [[1, 2, 3], [4, 5]]


def test_generate_uuid(monkeypatch):
    def check_output(args, encoding=None):
        if args == '/usr/bin/uuidgen' and encoding == 'utf-8':
            return 'A217CF9E-07D2-4DE0-8864-CD1988305656\n'

        raise Exception(f'unexpected args {args} encountered')

    monkeypatch.setattr('subprocess.check_output', check_output)
    assert generate_uuid() == 'A217CF9E-07D2-4DE0-8864-CD1988305656'
