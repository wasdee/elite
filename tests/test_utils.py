import os

import elite.utils


def test_dict_to_namedtuple():
    nt = elite.utils.dict_to_namedtuple('Thing', {
        'name': 'Bobo',
        'age': 10,
        'cool': False
    })
    assert repr(nt) == "Thing(name='Bobo', age=10, cool=False)"
    assert nt.name == 'Bobo'
    assert nt.age == 10
    assert nt.cool is False


def test_build_absolute_path():
    path = os.path.abspath(os.path.join('.', 'fruits.txt'))
    elite.utils.build_absolute_path('fruits.txt') == path


def test_deep_merge():
    source = {
        'name': 'fots',
        'things': {
            'a': 'b'
        },
        'deeper': {
            'and_deeper': {
                'key': 'value'
            }
        }
    }
    destination = {
        'age': 20,
        'things': {
            'b': 'c'
        },
        'deeper': {
            'and_deeper': {
                'bleh': 'blah'
            }
        }
    }
    elite.utils.deep_merge(source, destination)
    assert destination == {
        'name': 'fots',
        'age': 20,
        'things': {
            'a': 'b',
            'b': 'c'
        },
        'deeper': {
            'and_deeper': {
                'key': 'value',
                'bleh': 'blah'
            }
        }
    }
