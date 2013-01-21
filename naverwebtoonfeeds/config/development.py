from naverwebtoonfeeds.config.default import Config as Default

class Config(Default):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/development.db'
    GZIP = True
    Default.LOGGING['handlers']['console']['level'] = 'DEBUG'
    Default.LOGGING['loggers']['naverwebtoonfeeds']['handlers'].remove('mail_admins')
