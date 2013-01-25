from copy import deepcopy
import os
import re
from naverwebtoonfeeds.config.default import Config as Default

class Config(Default):

    LOGGING = deepcopy(Default.LOGGING)
    LOGGING['loggers']['naverwebtoonfeeds']['level'] = os.environ.get('LOG_LEVEL', 'WARNING')
    LOGGING['loggers']['sqlalchemy.engine']['level'] = os.environ.get('LOG_LEVEL', 'WARNING')
    LOGGING['loggers']['rq.worker']['level'] = os.environ.get('LOG_LEVEL', 'WARNING')

    @classmethod
    def setup_smtp(cls):
        keys = ['MAIL_TOADDRS', 'GMAIL_USERNAME', 'GMAIL_PASSWORD']
        if not all(os.environ.get(x) for x in keys):
            return
        smtp_handler = cls.LOGGING['handlers']['mail_admins']
        smtp_handler['toaddrs'] = os.environ['MAIL_TOADDRS']
        smtp_handler['mailhost'] = ('smtp.gmail.com', 587)
        smtp_handler['credentials'] = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])
        smtp_handler['secure'] = ()
        cls.LOGGING['loggers']['naverwebtoonfeeds'].append('mail_admins')

    @classmethod
    def from_envvars(cls):
        for key in os.environ:
            if validkey(key):
                setattr(cls, key, autocast(os.environ[key]))

def validkey(key):
    return re.match(r'^[A-Z_]+$', key)

def autocast(value):
    if re.match(r'^\d+$', value):
        return int(value)
    elif re.match(r'^\d+\.\d+$', value):
        return float(value)
    elif value == 'True':
        return True
    elif value == 'False':
        return False
    elif re.match(r'^\[.*\]$', value):
        return re.split(r'\s*,\s*', value[1:-1])
    else:
        return value

Config.from_envvars()
