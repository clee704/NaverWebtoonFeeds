import os
import re


__all__ = ['development', 'test', 'production']
__package_dir__ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_p = lambda relpath: os.path.join(__package_dir__, relpath)


class DefaultConfig(object):
    """
    Default configurations for NaverWebtoonFeeds.

    You should set *URL_ROOT* and *AUTHORITY_NAME*.
    *NAVER_USERNAME* and *NAVER_PASSWORD* is required for adult-only works.

    Edit this file or make a separate settings file and
    set *NWF_SETTINGS* environment variable to the path of the file.

    For more information, follow the below links.

    - http://flask.pocoo.org/docs/config/
    - http://packages.python.org/Flask-SQLAlchemy/config.html
    - http://packages.python.org/Flask-Cache/#configuring-flask-cache
    - http://elsdoerfer.name/docs/flask-assets/#configuration

    """

    #: (Required) Root URL of the web server where the app is hosted.
    #: It should be served at the root, not below like http://example.com/myapp/.
    URL_ROOT = 'http://example.com'

    #: (Required) A domain name or an email address you own.
    #: This is used to make unique Atom IDs for feed entries.
    #: See http://www.taguri.org/ and http://www.faqs.org/rfcs/rfc4151.html
    #: for more.
    AUTHORITY_NAME = 'yourdomain.com'
    # or
    # AUTHORITY_NAME = 'youremail@example.com'

    #: Enable or disable redirecting to the canonical URL
    #: if the request is from different hosts other than *URL_ROOT*.
    FORCE_REDIRECT = True

    #: Naver username.
    NAVER_USERNAME = ''

    #: Naver password.
    NAVER_PASSWORD = ''

    #: (Flask config) Enable or disable Flask debug mode.
    DEBUG = False

    #: (Flask config) Enable or disable Flask testing mode.
    TESTING = False

    #: Enable or disable gzip compression. If you are running your WSGI server
    #: behind a proxy such as Nginx, you might want to disable it
    #: and enable compression in the proxy.
    GZIP = True

    #: (Flask config) Default cache control max age to use with
    #: send_static_files() and send_file().
    SEND_FILE_MAX_AGE_DEFAULT = 31536000

    ASSETS_DEBUG = False
    ASSETS_DIRECTORY = _p('static/webassets')
    ASSETS_URL = '/static/webassets'
    ASSETS_LOAD_PATH = [_p('static')]
    ASSETS_URL_MAPPING = {_p('static'): '/static'}

    #: NaverWebtoonFeeds uses Flask-SQLAlchemy to persist data.
    #: See the `Flask-SQLAlchemy documentation <http://packages.python.org/Flask-SQLAlchemy/config.html>`
    #: for more information.
    #:
    #: When using SQLite, make sure the database file, as well as
    #: the parent directory of the file, is both readable and writable
    #: by the server process.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///naverwebtoonfeeds.db'

    #: If enabled, record SQL queries for debugging.
    #: It should be disabled on the production environment.
    SQLALCHEMY_RECORD_QUERIES = False

    #: Cache is used to store rendered pages and to queue background
    #: jobs. Both features are optional, although strongly recommended.
    CACHE_KEY_PREFIX = 'naverwebtoonfeeds:'

    #: Cache type. simple is the default, which uses python dict in webserver
    #: memory.
    #: Memcached
    #: CACHE_TYPE = 'memcached'
    #: CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']
    #: Redis
    #: CACHE_TYPE = 'redis'
    #: CACHE_REDIS_HOST = 'localhost'
    #: CACHE_REDIS_PORT = 6379
    #: CACHE_REDIS_PASSWORD = ''
    CACHE_TYPE = 'simple'

    #: Enable or disable using Redis Queue to update the database by a
    #: background worker. You must use Redis cache for this feature.
    USE_REDIS_QUEUE = False

    #: Enable or disable on-demand starting and stopping of a background worker.
    #: If disabled, the worker process must be running all the time.
    REDIS_QUEUE_BURST_MODE_IN_HEROKU = False

    #: Heroku API key. Used in conjunction with *REDIS_QUEUE_BURST_MODE_IN_HEROKU*.
    HEROKU_API_KEY = ''

    #: Heroku app name. Used in conjunction with *REDIS_QUEUE_BURST_MODE_IN_HEROKU*.
    HEROKU_APP_NAME = ''

    #: Enable or disable data compression for Redis cache.
    #: Recommended if you have a small cache (~ 5 MB).
    ENABLE_CACHE_COMPRESSION = False

    #: Use proxy servers for embedded images, as Naver disallow access to
    #: thumbnail images from other domains.  If provided, all thumbnail URLs
    #: will be formatted as ``IMGPROXY_URL.format(url=thumbnail_url)``.
    #: It may be overridden by *IMGPROXY_URL_PATTERN*.
    IMGPROXY_URL = 'http://images2-focus-opensocial.googleusercontent.com/' + \
            'gadgets/proxy?container=focus&url={url}'

    #: Use multiple hostnames to speed up page loading.
    #: According to a research, too many hostnames actually have
    #: negative impact on the performance; 2 to 4 hostnames should be fine.
    #: It overrides *IMGPROXY_URL*.
    IMGPROXY_URL_PATTERN = 'http://images{variable}-focus-opensocial.googleusercontent.com/' + \
            'gadgets/proxy?container=focus&url={url}'

    #: Function that takes an image URL and returns a value to interpolate
    #: *variable* in *IMGPROXY_URL_PATTERN*. The default function returns
    #: a number between 0 and 2 based on the hash value of the URL.
    IMGPROXY_URL_VARIABLE = staticmethod(lambda url: hash(url) % 3)

    #: Configurations for :py:mod:`logging`.
    #: See :py:func:`logging.config.dictConfig()` for more.
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'default': {
                'format': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'raw': {
                'format': '%(message)s',
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
            'sqlalchemy.engine': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'rq.worker': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'scss': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'gunicorn.access': {
                'handlers': ['console_raw'],
                'level': 'INFO',
            },
        },
    }

    PYSCSS_STATIC_ROOT = 'static'
    PYSCSS_STATIC_URL = 'static'

    @classmethod
    def from_envvars(cls):
        """
        Imports configuration values from environment variables.

        """
        if os.environ.get('SPHINX_RUNNING'):
            # Do not get values from environment if we are making docs.
            return
        for key in os.environ:
            if validkey(key):
                setattr(cls, key, autocast(os.environ[key]))


def validkey(key):
    return re.match(r'^[A-Z_]+$', key)


def autocast(value):
    """
    Converts the given string to a Python value.

    """
    if re.match(r'^\d+$', value):
        return int(value)
    elif re.match(r'^\d+\.\d+$', value):
        return float(value)
    elif value == 'True':
        return True
    elif value == 'False':
        return False
    elif value == 'None':
        return None
    elif re.match(r'^\[.*\]$', value):
        # Example: "[a, b, c]" => ['a', 'b', 'c']
        return re.split(r'\s*,\s*', value[1:-1])
    else:
        # If all others fail, just use the plain string.
        return value


DefaultConfig.from_envvars()
