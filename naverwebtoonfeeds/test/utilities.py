from flask import Flask
from mock import Mock


def mock_obj(**kwargs):
    mock = Mock(Flask('mock'))
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock
