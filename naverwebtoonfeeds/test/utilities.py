from mock import Mock
from naverwebtoonfeeds import app

def mock_obj(**kwargs):
    mock = Mock(app)
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock
