"""
    naverwebtoonfeeds.cache
    ~~~~~~~~~~~~~~~~~~~~~~~

    Implements a customized version of :class:`flask_cache.Cache` and
    customized versions of :class:`werkzeug.contrib.cache.RedisCache`.

"""
import zlib
from datetime import timedelta

from flask_cache import Cache as CacheBase
from redis import from_url
from werkzeug.contrib.cache import RedisCache as RedisCacheBase

from .redis_ import Redis


LONG_LONG_TIME = timedelta(days=365).total_seconds()


class Cache(CacheBase):

    def set_permanently(self, *args, **kwargs):
        """Sets the value almost permanently (a year by default)."""
        kwargs['timeout'] = LONG_LONG_TIME
        return self.set(*args, **kwargs)


class RedisCache(RedisCacheBase):

    def __init__(self, host='localhost', port=6379, password=None,
                 db=0, default_timeout=300, key_prefix=None):
        client = Redis(host=host, port=port, password=password, db=db)
        super(RedisCache, self).__init__(client, port, password, db,
                                         default_timeout, key_prefix)


class CompressedRedisCache(RedisCache):

    def dump_object(self, value):
        serialized_str = super(CompressedRedisCache, self).dump_object(value)
        try:
            return zlib.compress(serialized_str)
        except zlib.error:
            return serialized_str

    def load_object(self, value):
        try:
            serialized_str = zlib.decompress(value)
        except (zlib.error, TypeError):
            serialized_str = value
        return super(CompressedRedisCache, self).load_object(serialized_str)


def redis(app, config, args, kwargs):
    """Returns a :class:`RedisCache`. Compatible with Flask-Cache.
    """
    return _redis_backend(app, config, args, kwargs, RedisCache)


def compressedredis(app, config, args, kwargs):
    """Returns a :class:`CompressedRedisCache`. Compatible with Flask-Cache.
    """
    return _redis_backend(app, config, args, kwargs, CompressedRedisCache)


def _redis_backend(app, config, args, kwargs, cache_class):
    kwargs.update(dict(
        host=config.get('CACHE_REDIS_HOST', 'localhost'),
        port=config.get('CACHE_REDIS_PORT', 6379),
    ))
    password = config.get('CACHE_REDIS_PASSWORD')
    if password:
        kwargs['password'] = password

    key_prefix = config.get('CACHE_KEY_PREFIX')
    if key_prefix:
        kwargs['key_prefix'] = key_prefix

    db_number = config.get('CACHE_REDIS_DB')
    if db_number:
        kwargs['db'] = db_number

    redis_url = config.get('CACHE_REDIS_URL')
    if redis_url:
        kwargs['host'] = from_url(redis_url, db=kwargs.pop('db', None))

    return cache_class(*args, **kwargs)
