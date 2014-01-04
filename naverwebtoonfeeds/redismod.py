import logging
import random
import time
import zlib

from redis import Redis as RedisBase
from werkzeug.contrib.cache import RedisCache as RedisCacheBase


__logger__ = logging.getLogger(__name__)


# Redis implements __getitem__ but not __len__
# Redis has too many public methods (142 methods)
# pylint: disable=incomplete-protocol,too-many-public-methods
class Redis(RedisBase):

    def __init__(self, *args, **kwargs):
        self._init_done = False
        if args or kwargs:
            RedisBase.__init__(self, *args, **kwargs)
            self._init_done = True

    def init(self, *args, **kwargs):
        if not self._init_done:
            RedisBase.__init__(self, *args, **kwargs)
            self._init_done = True
        else:
            raise RuntimeError('already initialized')

    def execute_command(self, *args, **kwargs):
        retry = 10
        backoff = 1
        while retry > 0:
            retry -= 1
            try:
                return RedisBase.execute_command(self, *args, **kwargs)
            except redis.exceptions.ResponseError:
                __logger__.debug('Redis server appears to be busy')
                if retry != 0:
                    delay = random.random() * backoff
                    __logger__.debug('Waiting %.1f seconds before retrying...', delay)
                    time.sleep(delay)
                    backoff *= 2
                else:
                    __logger__.exception('Maximum number of retries reached')


class RedisCache(RedisCacheBase):

    def __init__(self, host='localhost', port=6379, password=None,
                 db=0, default_timeout=300, key_prefix=None):
        client = Redis(host=host, port=port, password=password, db=db)
        RedisCacheBase.__init__(self, client, port, password, db, default_timeout, key_prefix)


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
