from copy import deepcopy
from naverwebtoonfeeds.config.default import Config as Default

class Config(Default):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/test.db'
    LOGGING = deepcopy(Default.LOGGING)

    # Disable all loggers.
    for logger in LOGGING['loggers'].values():
        logger['handlers'] = ['null']
