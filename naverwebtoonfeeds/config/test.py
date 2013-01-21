from naverwebtoonfeeds.config.default import Config as Default

class Config(Default):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/test.db'
    Default.LOGGING['loggers']['naverwebtoonfeeds']['handlers'].remove('mail_admins')
