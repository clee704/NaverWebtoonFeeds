import os

from mock import Mock
import yaml


def mock_obj(**kwargs):
    mock = Mock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock


def read_fixture(name):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', name)) as f:
        text = f.read()
        if name.endswith('yml'):
            return yaml.load(text)
        else:
            return text
