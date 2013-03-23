from copy import deepcopy

from ..config import DefaultConfig


class Config(DefaultConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # Use in-memory database.
    LOGGING = deepcopy(DefaultConfig.LOGGING)

    # Disable all loggers.
    for logger in LOGGING['loggers'].values():
        logger['handlers'] = ['null']
