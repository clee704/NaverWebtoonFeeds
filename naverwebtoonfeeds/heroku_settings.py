import os
import re
from naverwebtoonfeeds.default_settings import LOGGING

def guess_type(value):
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

for key in os.environ:
    locals()[key] = guess_type(os.environ[key])

if os.environ.get('LOG_LEVEL'):
    LOGGING['loggers']['naverwebtoonfeeds']['level'] = os.environ['LOG_LEVEL']

if os.environ.get('WORKER_LOG_LEVEL'):
    LOGGING['loggers']['rq.worker']['level'] = os.environ['WORKER_LOG_LEVEL']

if all(os.environ.get(x) for x in ['GMAIL_USERNAME', 'GMAIL_PASSWORD', 'MAIL_TOADDRS']):
    smtp_handler = LOGGING['handlers']['mail_admins']
    smtp_handler['toaddrs'] = MAIL_TOADDRS
    smtp_handler['mailhost'] = ('smtp.gmail.com', 587)
    smtp_handler['credentials'] = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])
    smtp_handler['secure'] = ()
    logger = LOGGING['loggers']['naverwebtoonfeeds']
    if 'mail_admins' not in logger['handlers']:
        logger['handlers'].append('mail_admins')
