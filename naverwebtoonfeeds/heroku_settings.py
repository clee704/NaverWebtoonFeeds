import logging
import os
import re

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
    if key.endswith('_LEVEL'):
        locals()[key] = getattr(logging, os.environ[key].upper())
    else:
        locals()[key] = guess_type(os.environ[key])

if os.environ.get('GMAIL_USERNAME') and os.environ.get('GMAIL_PASSWORD'):
    MAIL_CREDENTIALS = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])

MAIL_HOST = ('smtp.gmail.com', 587)
MAIL_SECURE = ()
