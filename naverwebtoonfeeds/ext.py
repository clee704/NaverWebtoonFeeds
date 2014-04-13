"""
    naverwebtoonfeeds.ext
    ~~~~~~~~~~~~~~~~~~~~~

    Creates and configures Flask extension objects.

"""
from os.path import dirname, join

from flask_assets import Environment
from flask_sqlalchemy import SQLAlchemy

from .cache import Cache
from .gzip import Gzip


assets_env = Environment()
cache = Cache()
db = SQLAlchemy()
gzip = Gzip()


assets_env.from_yaml(join(dirname(__file__), 'static/assets.yaml'))


try:
    from rq import Queue
    from .redis_ import Redis
    redis = Redis()
    queue = Queue(connection=redis)
except ImportError:
    redis = None
    queue = None
