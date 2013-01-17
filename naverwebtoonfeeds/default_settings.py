# Default settings file for NaverWebtoonFeeds.
#
# The only option you should override is URL_ROOT. Make a settings file and
# set NAVERWEBTOONFEEDS_SETTINGS environment variable to point to it.
#
# Make sure this file is unreadable by others if you've decided to write down
# your Naver login information here.
import logging

# Enable or disable Flask debug mode.
DEBUG = False

# Root URL of the web server where the app is hosted. It should be served
# at the root, not below the root like http://example.com/myapp/.
URL_ROOT = 'http://example.com'

# The app listens to the port 5000 by default.
# Uncomment to change the port to 80.
#PORT = 80

# If set, requests from different hosts other than URL_ROOT will be redirected
# to the corresponding canonical URL.
#FORCE_REDIRECT = True

LOG_LEVEL = logging.WARNING

# If set, send emails to admins on the specified level of logs.
#SEND_EMAIL = not DEBUG
EMAIL_LEVEL = logging.ERROR

# Arguments to logging.handlers.SMTPHandler
# See http://docs.python.org/2/library/logging.handlers.html#smtphandler
# for details.
#MAIL_HOST = 'localhost'
#MAIL_FROMADDR = 'naverwebtoonfeeds-logger@localhost'
#MAIL_TOADDRS = ['admin@example.com']
MAIL_SUBJECT = '[NaverWebtoonFeeds] Logs'
MAIL_CREDENTIALS = None
MAIL_SECURE = None

# NaverWebtoonFeeds uses Flask-SQLAlchemy to persist data.
# See the Flask-SQLAlchemy documentation at
# http://packages.python.org/Flask-SQLAlchemy/config.html for more details.
#
# When using SQLite, make sure the database file, as well as the parent
# directory of the file, is readable and writable by the server process.
SQLALCHEMY_DATABASE_URI = 'sqlite:///db/naverwebtoonfeeds.db'

# Record SQL queries for debugging. It should be unset on the production
# environment.
#SQLALCHEMY_RECORD_QUERIES = True

# Additional configurations for Flask-SQLAlchemy can be found at
# http://packages.python.org/Flask-SQLAlchemy/config.html

# Generated HTML and XML pages can be cached.
# See the Flask-Cache documentation at
# http://packages.python.org/Flask-Cache/ for configuration details.
#CACHE_TYPE = 'memcached'
#CACHE_KEY_PREFIX = 'naverwebtoonfeeds'
#CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']

# Naver login information is needed to access some adult-only series.
#NAVER_USERNAME = ''
#NAVER_PASSWORD = ''

# Use image proxy. Naver disallow access to thumbnails from other domains.
# If provided, all thumbnail URLs will be formatted as
# IMGPROXY_URL.format(url=thumbnail_url).
IMGPROXY_URL = 'http://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&url={url}'

# You can use multiple hostnames to speed up page loading.
IMGPROXY_URL_PATTERN = 'http://images{variable}-focus-opensocial.googleusercontent.com/' + \
        'gadgets/proxy?container=focus&url={url}'
IMGPROXY_URL_VARIABLE = lambda url: hash(url) % 20

# Enable Gzip compression
#GZIP = True

# Additional Flask configurations can be found at
# http://flask.pocoo.org/docs/config/
