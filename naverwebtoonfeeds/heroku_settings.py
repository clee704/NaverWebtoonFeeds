import logging
import os
import re

LOG_LEVEL = getattr(logging, os.environ['LOG_LEVEL'])
EMAIL_LEVEL = getattr(logging, os.environ['EMAIL_LEVEL'])
MAIL_HOST = ('smtp.gmail.com', 587)
MAIL_TOADDRS = re.split(r'\s*;\s*', os.environ['MAIL_TOADDRS'])
MAIL_CREDENTIALS = (os.environ['GMAIL_USERNAME'], os.environ['GMAIL_PASSWORD'])
MAIL_SECURE = ()
SEND_FILE_MAX_AGE_DEFAULT = int(os.environ['SEND_FILE_MAX_AGE_DEFAULT'])

for key, value in os.environ.items():
    if key not in locals():
        locals()[key] = value
