from naverwebtoonfeeds.config.default import Config as Default

class Config(Default):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/test.db'

    # Disable all loggers.
    for logger in Default.LOGGING['loggers'].values():
        logger['handlers'] = []
