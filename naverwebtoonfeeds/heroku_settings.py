import logging
import os
import re

if os.environ.get('LOG_LEVEL'):
    LOG_LEVEL = getattr(logging, os.environ['LOG_LEVEL'].upper())

if os.environ.get('EMAIL_LEVEL'):
    EMAIL_LEVEL = getattr(logging, os.environ['EMAIL_LEVEL'].upper())

MAIL_HOST = ('smtp.gmail.com', 587)

if os.environ.get('MAIL_TOADDRS'):
    MAIL_TOADDRS = re.split(r'\s*;\s*', os.environ['MAIL_TOADDRS'])

if os.environ.get('GMAIL_USERNAME') and os.environ.get('GMAIL_PASSWORD'):
    MAIL_CREDENTIALS = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])

MAIL_SECURE = ()

if os.environ.get('SEND_FILE_MAX_AGE_DEFAULT'):
    SEND_FILE_MAX_AGE_DEFAULT = int(os.environ['SEND_FILE_MAX_AGE_DEFAULT'])

if os.environ.get('CACHE_MEMCACHED_SERVERS'):
    CACHE_MEMCACHED_SERVERS = re.split(r'\s*,\s*', os.environ['CACHE_MEMCACHED_SERVERS'])

for key, value in os.environ.items():
    if key not in locals():
        locals()[key] = value
