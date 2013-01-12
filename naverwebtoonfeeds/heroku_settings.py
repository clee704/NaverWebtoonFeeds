import logging
import os
import re

if os.environ.get('GMAIL_USERNAME') and os.environ.get('GMAIL_PASSWORD'):
    MAIL_CREDENTIALS = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])

MAIL_HOST = ('smtp.gmail.com', 587)
MAIL_SECURE = ()

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

for key, value in os.environ.items():
    if key not in locals():
        if key.endswith('_LEVEL'):
            val = getattr(logging, value.upper())
        else:
            val = guess_type(value)
        locals()[key] = val
