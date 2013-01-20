# Default settings file for NaverWebtoonFeeds.
#
# You should override at least URL_ROOT and AUTHORITY_NAME.
# Edit this file or make a separate settings file and set
# NAVERWEBTOONFEEDS_SETTINGS environment variable to point to it.
#
# Make sure this file is unreadable by others if you've decided to write down
# your Naver login information here.

# Root URL of the web server where the app is hosted. It should be served
# at the root, not below the root like http://example.com/myapp/.
URL_ROOT = 'http://example.com'

# A domain name or an email address you own.
# This is used to make unique Atom IDs for feed entries.
# See http://www.taguri.org/ and http://www.faqs.org/rfcs/rfc4151.html for more.
AUTHORITY_NAME = 'yourdomain.com'
# or
#AUTHORITY_NAME = 'youremail@example.com'

# If set, requests from different hosts other than URL_ROOT will be redirected
# to the corresponding canonical URL.
#FORCE_REDIRECT = True

# Enable or disable Flask debug mode.
DEBUG = False

# NaverWebtoonFeeds uses Flask-SQLAlchemy to persist data.
# See the Flask-SQLAlchemy documentation at
# http://packages.python.org/Flask-SQLAlchemy/config.html for more details.
#
# When using SQLite, make sure the database file, as well as the parent
# directory of the file, is readable and writable by the server process.
SQLALCHEMY_DATABASE_URI = 'sqlite:///db/naverwebtoonfeeds.db'

# Record SQL queries for debugging. It should be disabled on the production
# environment.
#SQLALCHEMY_RECORD_QUERIES = True

# Additional configurations for Flask-SQLAlchemy can be found at
# http://packages.python.org/Flask-SQLAlchemy/config.html

# Generated HTML and XML pages can be cached.
# See the Flask-Cache documentation at
# http://packages.python.org/Flask-Cache/ for configuration details.
CACHE_TYPE = 'simple'
#CACHE_KEY_PREFIX = 'naverwebtoonfeeds'
#
# Memcached
#
#CACHE_TYPE = 'memcached'
#CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']
#
# Redis
#
#CACHE_TYPE = 'redis'
#CACHE_REDIS_HOST = 'localhost'
#CACHE_REDIS_PORT = 6379
#CACHE_REDIS_PASSWORD = ''

# Use Redis Queue to update the database by background workers.
# You must use Redis as a cache (see above).
#USE_REDIS_QUEUE = True

# While deploying in Heroku, run the worker process only when needed.
# Useful if you are on a budget.
#REDIS_QUEUE_BURST_MODE_IN_HEROKU = True
#HEROKU_API_KEY = ''
#HEROKU_APP_NAME = ''

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
IMGPROXY_URL_VARIABLE = lambda url: hash(url) % 3

# Enable Gzip compression
#GZIP = True

# Logging settings.
# See http://docs.python.org/2.7/library/logging.config.html#logging.config.dictConfig
# for details.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'mail_admins': {
            'level': 'ERROR',
            'formatter': 'default',
            'class': 'logging.handlers.SMTPHandler',
            'toaddrs': ['admin@example.com'],
            'fromaddr': 'naverwebtoonfeeds-logger@localhost',
            'subject': '[NaverWebtoonFeeds] Logs',
            'mailhost': 'localhost',
        },
    },
    'loggers': {
        'naverwebtoonfeeds': {
            # Add 'mail_admins' to email error level logs to admins.
            #'handlers': ['console', 'mail_admins'],
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'sqlalchemy.engine': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'rq.worker': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Additional Flask configurations can be found at
# http://flask.pocoo.org/docs/config/
