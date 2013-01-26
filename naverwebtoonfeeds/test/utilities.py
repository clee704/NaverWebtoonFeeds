from mock import Mock


def mock_obj(**kwargs):
    mock = Mock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock
