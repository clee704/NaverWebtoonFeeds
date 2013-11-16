from copy import deepcopy
import os

from ..config import DefaultConfig, autocast


class Config(DefaultConfig):
    LOGGING = deepcopy(DefaultConfig.LOGGING)
    LOGGING['loggers']['naverwebtoonfeeds']['level'] = os.environ.get('LOG_LEVEL', 'WARNING')
    LOGGING['loggers']['sqlalchemy.engine']['level'] = os.environ.get('SQL_LOG_LEVEL', 'WARNING')

    @classmethod
    def setup_smtp(cls):
        keys = ['MAIL_TOADDRS', 'GMAIL_USERNAME', 'GMAIL_PASSWORD']
        if not all(os.environ.get(x) for x in keys):
            return
        smtp_handler = cls.LOGGING['handlers']['mail_admins']
        smtp_handler['toaddrs'] = autocast(os.environ['MAIL_TOADDRS'])
        smtp_handler['mailhost'] = ('smtp.gmail.com', 587)
        smtp_handler['credentials'] = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])
        smtp_handler['secure'] = ()
        cls.LOGGING['loggers']['naverwebtoonfeeds']['handlers'].append('mail_admins')


Config.from_envvars()
Config.setup_smtp()
