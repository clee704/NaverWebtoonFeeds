# Default settings file for NaverWebtoonFeeds.
#
# The only option you should override is URL_ROOT. Make a settings file and
# make NAVERWEBTOONFEEDS_SETTINGS environment variable point to it.
#
# Make sure this file is unreadable by others if you've decided to write down
# your Naver login information here.
import logging

# Root URL of the web server where the app is hosted. It should be served
# at the root, not below the root like http://example.com/myapp/.
URL_ROOT = 'http://example.com'

# If set, requests from different hosts other than URL_ROOT will be redirected
# to the corresponding canonical URL.
#FORCE_REDIRECT = True

# If set, DEBUG level logs will be printed.
DEBUG = False

LOG_LEVEL = logging.WARNING

# If set, email logs of the specified level to admins.
#SEND_EMAIL = not DEBUG
EMAIL_LEVEL = logging.ERROR
#MAIL_HOST = 'localhost'
#MAIL_FROMADDR = 'naverwebtoonfeeds-logger@localhost'
#MAIL_TOADDRS = ['admin@example.com']
MAIL_SUBJECT = '[NaverWebtoonFeeds] Logs'
MAIL_CREDENTIALS = None
MAIL_SECURE = None

# Use image proxy. Naver disallow access to thumbnails from other domains.
# If provided, all thumbnail URLs will be formatted as
# IMGPROXY_URL.format(url=thumbnail_url).
IMGPROXY_URL = 'http://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&url={url}'

# NaverWebtoonFeeds uses Flask-SQLAlchemy to persist data.
# See the Flask-SQLAlchemy documentation at
# http://packages.python.org/Flask-SQLAlchemy/config.html for more details.
#
# When using SQLite, make sure the database file, as well as the parent
# directory of the file, is readable and writable by the server process.
SQLALCHEMY_DATABASE_URI = 'sqlite:///db/naverwebtoonfeeds.db'

# Naver login information to access restricted contents.
#NAVER_USERNAME = ''
#NAVER_PASSWORD = ''

# Generated HTML and XML pages can be cached.
# See the Flask-Cache documentation at
# http://packages.python.org/Flask-Cache/ for configuration details.
#CACHE_TYPE = 'memcached'
#CACHE_KEY_PREFIX = 'naverwebtoonfeeds'
#CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']

# Enable Gzip compression
#GZIP = True
