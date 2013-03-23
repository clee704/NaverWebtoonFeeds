from copy import deepcopy

from ..config import DefaultConfig


class Config(DefaultConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///development.db'
    GZIP = True
    LOGGING = deepcopy(DefaultConfig.LOGGING)
    LOGGING['loggers']['naverwebtoonfeeds']['level'] = 'DEBUG'
