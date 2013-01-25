from copy import deepcopy
from naverwebtoonfeeds.config.default import Config as Default

class Config(Default):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/development.db'
    GZIP = True
    LOGGING = deepcopy(Default.LOGGING)
    LOGGING['loggers']['naverwebtoonfeeds']['level'] = 'DEBUG'
