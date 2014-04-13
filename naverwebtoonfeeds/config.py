"""
    naverwebtoonfeeds.config
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The default configuration values.

"""
import os
from datetime import timedelta
from os.path import dirname, join

from ._compat import string_types, iteritems


cwd = os.path.abspath(os.getcwd())
instance_path = join(cwd, 'instance')


class DefaultConfig(object):
    """Default configurations for NaverWebtoonFeeds.

    You must change at least :attr:`.SERVER_NAME` and :attr:`.AUTHORITY_NAME`.
    :attr:`.NAVER_USERNAME` and :attr:`.NAVER_PASSWORD` is required for
    adult-only works.

    If a value contains ``{INSTANCE_PATH}``, it will be converted to the
    absolute path of :attr:`instance_path` which is by default the ``instance``
    folder under the current working directiry.

    For more information, follow the below links.

    - `Flask Configuration Handling`__
    - `Flask-SQLAlchemy Configuration`__
    - `Configuring Flask-Cache`__
    - `Flask-Assets Configuration`__

    __ http://flask.pocoo.org/docs/config/
    __ http://pythonhosted.org/Flask-SQLAlchemy/config.html
    __ http://pythonhosted.org/Flask-Cache/#configuring-flask-cache
    __ http://flask-assets.readthedocs.org/en/latest/#configuration

    """

    #: (Required) The name and port number of the server. Used to redirect
    #: requests to non-canonical URLs to the canonical ones.
    SERVER_NAME = 'localhost:5000'

    #: The URL scheme that should be used when generating canonical URLs.
    PREFERRED_URL_SCHEME = 'http'

    #: (Required) A domain name or an email address you own. This is used to
    #: make unique Atom IDs for feed entries. See `Tag URI`__ and
    #: `RFC 4151 - The 'tag' URI Scheme`__ for more information.
    #:
    #: __ http://www.taguri.org/
    #: __ http://www.faqs.org/rfcs/rfc4151.html
    #:
    AUTHORITY_NAME = SERVER_NAME
    # or
    # AUTHORITY_NAME = 'youremail@example.com'

    #: If *True*, redirects requests from non-canonical URL to the canonical
    #: URL. Canonical URLs start with :attr:`.SERVER_NAME`.
    REDIRECT_TO_CANONICAL_URL = False

    #: Enable or disable fetching adult-only data. It requires
    #: :attr:`.NAVER_USERNAME` and :attr:`.NAVER_PASSWORD` be set correctly.
    FETCH_ADULT_ONLY = False

    #: Naver username.
    NAVER_USERNAME = ''

    #: Naver password.
    NAVER_PASSWORD = ''

    #: (Flask config) Enable or disable Flask debug mode.
    DEBUG = True

    #: (Flask config) Enable or disable Flask testing mode.
    TESTING = False

    #: Enable or disable gzip compression. If you are running your WSGI server
    #: behind a proxy such as Nginx, you might want to disable it and enable
    #: compression on the proxy.
    GZIP = False

    #: (Flask config) Default cache control max age to use with
    #: send_static_files() and send_file().
    SEND_FILE_MAX_AGE_DEFAULT = 31536000

    #: NaverWebtoonFeeds uses Flask-SQLAlchemy to persist data.
    #: See the `Flask-SQLAlchemy documentation`__ for more information.
    #:
    #: When using SQLite, make sure the database file, as well as
    #: the parent directory of the file, is both readable and writable
    #: by the server process.
    #:
    #: __ http://packages.python.org/Flask-SQLAlchemy/config.html
    #:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{INSTANCE_PATH}/development.db'

    #: If enabled, record SQL queries for debugging.
    #: It should be disabled on the production environment.
    SQLALCHEMY_RECORD_QUERIES = False

    #: Specify the cache type. See `Configuring Flask-Cache`__ for more
    #: information. In addition to the types provided by Flask-Cache, you can
    #: also use ``naverwebtoonfeeds.cache.redis`` and
    #: ``naverwebtoonfeeds.cache.compressedredis``. They both support retrying
    #: failed requests when the Redis server is busy and the latter one saves
    #: and loads values with compression to reduce the space usage.
    #:
    #: __ http://pythonhosted.org/Flask-Cache/#configuring-flask-cache
    #:
    CACHE_TYPE = 'filesystem'

    CACHE_DIR = '{INSTANCE_PATH}/cache'
    CACHE_DEFAULT_TIMEOUT = timedelta(hours=3)
    CACHE_KEY_PREFIX = 'naverwebtoonfeeds:'

    # Memcached
    # CACHE_TYPE = 'memcached'
    # CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']

    # Redis
    # CACHE_TYPE = 'naverwebtoonfeeds.cache.compressedredis'
    # CACHE_REDIS_URL = 'redis://localhost:6379/'

    #: If *True*, use RQ (Redis Queue) to update the database by a background
    #: worker. :attr:`.CACHE_TYPE` must be ``redis``,
    #: ``naverwebtoonfeeds.cache.redis``, or
    #: ``naverwebtoonfeeds.cache.compressedredis`` to use this feature.
    USE_REDIS_QUEUE = False

    #: Enable or disable on-demand starting of a background worker. If
    #: disabled, you must run the worker process manually.
    START_HEROKU_WORKER_ON_REQUEST = False

    #: Heroku API key. Used in conjunction with
    #: :attr:`.START_HEROKU_WORKER_ON_REQUEST`.
    HEROKU_API_KEY = ''

    #: Heroku app name. Used in conjunction with
    #: :attr:`.START_HEROKU_WORKER_ON_REQUEST`.
    HEROKU_APP_NAME = ''

    #: Use proxy servers for embedded images, as Naver disallow access to
    #: thumbnail images from other domains.  If provided, all thumbnail URLs
    #: will be formatted as ``IMGPROXY_URL.format(url=thumbnail_url)``.
    #: It may be overridden by :attr:`.IMGPROXY_URL_PATTERN`.
    IMGPROXY_URL = ('http://images2-focus-opensocial.googleusercontent.com/'
                    'gadgets/proxy?container=focus&url={url}')

    #: Use multiple hostnames to speed up page loading.
    #: According to a research, too many hostnames actually have
    #: negative impact on the performance; 2 to 4 hostnames should be fine.
    #: It overrides :attr:`.IMGPROXY_URL`.
    IMGPROXY_URL_PATTERN = ('http://images{v}-focus-opensocial.'
                            'googleusercontent.com/gadgets/proxy?'
                            'container=focus&url={url}')

    #: Function that takes an image URL and returns a value to interpolate
    #: *v* in :attr:`.IMGPROXY_URL_PATTERN`. The default function returns a
    #: number between 0 and 2 based on the hash value of the URL.
    IMGPROXY_URL_VARIABLE = staticmethod(lambda url: hash(url) % 3)

    PUBLIC_IP_SERVERS = {
        'http://ipecho.net/plain': r'(\d{1,3}(\.\d{1,3}){3})',
        'http://httpbin.org/ip': r'"origin": "(\d{1,3}(\.\d{1,3}){3})"',
        'http://checkip.dyndns.com/': r'Address: (\d{1,3}(\.\d{1,3}){3})',
    }

    # Config values that need not be changed by the user.
    ASSETS_DEBUG = True
    ASSETS_LOAD_PATH = [join(dirname(__file__), 'static')]
    ASSETS_DIRECTORY = '{INSTANCE_PATH}/assets'
    ASSETS_URL = '/static/generated'
    ASSETS_URL_MAPPING = {join(dirname(__file__), 'static'): '/static'}
    LESS_BIN = join(cwd, 'node_modules/.bin/lessc')


def resolve_instance_path(cls):
    class ResolvedConfig(cls):
        pass
    changes = {}
    for key in dir(ResolvedConfig):
        if not key.isupper():
            continue
        value = getattr(ResolvedConfig, key)
        new_value = _deep_replace_instance_path(value)
        if new_value != value:
            changes[key] = new_value
    for key, value in iteritems(changes):
        setattr(ResolvedConfig, key, value)
    return ResolvedConfig


def _deep_replace_instance_path(value):
    if isinstance(value, string_types):
        return value.replace('{INSTANCE_PATH}', instance_path)
    if isinstance(value, (tuple, list, set)):
        return type(value)(_deep_replace_instance_path(x) for x in value)
    if isinstance(value, dict):
        new_d = {}
        for k, v in iteritems(value):
            new_k = _deep_replace_instance_path(k)
            new_v = _deep_replace_instance_path(v)
            new_d[new_k] = new_v
        return new_d
    else:
        return value
