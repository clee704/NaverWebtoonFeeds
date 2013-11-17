# pylint: disable=import-error,no-name-in-module
import os


__dir__ = os.path.dirname(__file__)


from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()


from flask.ext.cache import Cache
cache = Cache()


from flask.ext.assets import Environment
assets_env = Environment()
assets_env.from_yaml(os.path.join(__dir__, 'static/webassets.yaml'))


from flask.ext.gzip import Gzip

class MyGzip(Gzip):
    def __init__(self):
        pass

    def init_app(self, app):
        Gzip.__init__(self, app)

    def after_request(self, response):
        # Fix https://github.com/elasticsales/Flask-gzip/issues/7
        response.direct_passthrough = False
        return Gzip.after_request(self, response)

gzip = MyGzip()


import zlib
from werkzeug.contrib.cache import RedisCache

class CompressedRedisCache(RedisCache):

    def dump_object(self, value):
        serialized_str = RedisCache.dump_object(self, value)
        try:
            return zlib.compress(serialized_str)
        except zlib.error:
            return serialized_str

    def load_object(self, value):
        try:
            serialized_str = zlib.decompress(value)
        except (zlib.error, TypeError):
            serialized_str = value
        return RedisCache.load_object(self, serialized_str)


try:
    from redis import Redis
    from rq import Queue

    # Redis implements __getitem__ but not __len__
    # Redis has too many public methods (142 methods)
    # pylint: disable=incomplete-protocol,too-many-public-methods
    class MyRedis(Redis):
        def __init__(self):
            # pylint: disable=super-init-not-called
            pass
        def init_app(self, *args, **kwargs):
            Redis.__init__(self, *args, **kwargs)

    redis_connection = MyRedis()
    redis_queue = Queue(connection=redis_connection)
except ImportError:
    redis_connection = None
    redis_queue = None
