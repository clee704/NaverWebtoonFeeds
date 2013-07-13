# pylint: disable=E0603
__all__ = ['development', 'test', 'production']


# Default configurations for NaverWebtoonFeeds.
#
# You should override at least URL_ROOT and AUTHORITY_NAME.
# Edit this file or make a separate settings file and
# make NAVERWEBTOONFEEDS_SETTINGS environment variable point to it.
#
# Make sure this file is unreadable by others if you've decided to
# write down your Naver login information here.
#
# For more information, refer to:
# - http://flask.pocoo.org/docs/config/
# - http://packages.python.org/Flask-SQLAlchemy/config.html
# - http://packages.python.org/Flask-Cache/#configuring-flask-cache
# - http://elsdoerfer.name/docs/flask-assets/#configuration
#
class DefaultConfig(object):

    # Root URL of the web server where the app is hosted.
    # It should be served at the root, not below the root
    # like http://example.com/myapp/.
    URL_ROOT = 'http://example.com'

    # A domain name or an email address you own.
    # This is used to make unique Atom IDs for feed entries.
    # See http://www.taguri.org/ and http://www.faqs.org/rfcs/rfc4151.html
    # for more.
    AUTHORITY_NAME = 'yourdomain.com'
    # or
    #AUTHORITY_NAME = 'youremail@example.com'

    # NaverWebtoonFeeds uses Flask-SQLAlchemy to persist data.
    # See the Flask-SQLAlchemy documentation at
    # http://packages.python.org/Flask-SQLAlchemy/config.html
    # for more details.
    #
    # When using SQLite, make sure the database file, as well as
    # the parent directory of the file, is both readable and writable
    # by the server process.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///naverwebtoonfeeds.db'

    # If enabled, record SQL queries for debugging.
    # It should be disabled on the production environment.
    #SQLALCHEMY_RECORD_QUERIES = True

    # Enable or disable Flask debug mode. (Flask config)
    DEBUG = False

    # Enable gzip compression. If you are running your WSGI server
    # behind a proxy such as Nginx, you might want to disable it
    # and enable compression in the proxy.
    #GZIP = True

    # Default cache control max age to use with send_static_files()
    # and send_file(). (Flask config)
    SEND_FILE_MAX_AGE_DEFAULT = 31536000

    # Enable redirecting to the canonical URL if the request is from different
    # hosts other than URL_ROOT.
    #FORCE_REDIRECT = True

    # Cache is used to store rendered pages and to queue background
    # jobs. Both features are optional, although strongly recommended.
    CACHE_KEY_PREFIX = 'naverwebtoonfeeds:'
    CACHE_TYPE = 'simple'
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

    # Use Redis Queue to update the database by a background worker.
    # You must use Redis cache for this feature.
    #USE_REDIS_QUEUE = True

    # Enable on-demand starting and stopping of a background worker.
    # If disabled, the worker process must be running all the time.
    # Your Heroku API key and app name is needed.
    #REDIS_QUEUE_BURST_MODE_IN_HEROKU = True
    #HEROKU_API_KEY = ''
    #HEROKU_APP_NAME = ''

    # Enable data compression in Redis cache.
    # Recommended if you have a small cache (~ 5 MB).
    #ENABLE_CACHE_COMPRESSION = True

    # Naver account is needed to access adult-only works.
    #NAVER_USERNAME = ''
    #NAVER_PASSWORD = ''

    # Use proxy servers for embedded images.
    # Naver disallow access to thumbnails from other domains.
    # If provided, all thumbnail URLs will be formatted by
    # IMGPROXY_URL.format(url=thumbnail_url).
    # It may be overridden by IMGPROXY_URL_PATTERN.
    IMGPROXY_URL = 'http://images2-focus-opensocial.googleusercontent.com/' + \
            'gadgets/proxy?container=focus&url={url}'

    # You can use multiple hostnames to speed up page loading.
    # According to a research, too many hostnames actually have
    # negative impact on the performance; 2 to 4 should be good.
    # It overrides IMGPROXY_URL.
    IMGPROXY_URL_PATTERN = 'http://images{variable}-focus-opensocial.googleusercontent.com/' + \
            'gadgets/proxy?container=focus&url={url}'
    # Use 3 hostnames starting with images0, images1, and images2.
    IMGPROXY_URL_VARIABLE = staticmethod(lambda url: hash(url) % 3)

    # Configure logging.
    # See http://docs.python.org/2.7/library/logging.config.html#logging.config.dictConfig
    # for details.
    LOGGER_NAME = 'naverwebtoonfeeds'
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'default': {
                'format': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'raw': {
                'format': '%(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'console_raw': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'raw',
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
            'null': {
                'class': 'logging.NullHandler',
            },
        },
        'loggers': {
            'naverwebtoonfeeds': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'naverwebtoonfeeds.feeds.browser': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'sqlalchemy.engine': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'rq.worker': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'gunicorn.access': {
                'handlers': ['console_raw'],
                'level': 'INFO',
            },
        },
    }
