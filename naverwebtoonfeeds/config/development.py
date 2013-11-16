from copy import deepcopy
import os

from ..config import DefaultConfig


class Config(DefaultConfig):
    URL_ROOT = 'http://localhost:5000'
    FORCE_REDIRECT = False
    DEBUG = True
    ASSETS_DEBUG = True
    EXPRESS_MODE = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////{0}/development.db'.format(os.getcwd())
    LOGGING = deepcopy(DefaultConfig.LOGGING)
    LOGGING['loggers']['naverwebtoonfeeds']['level'] = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOGGING['loggers']['sqlalchemy.engine']['level'] = os.environ.get('SQL_LOG_LEVEL', 'WARNING')


Config.from_envvars()
