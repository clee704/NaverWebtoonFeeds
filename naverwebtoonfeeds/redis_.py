"""
    naverwebtoonfeeds.redis_
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Implements customized versions of :class:`redis.Redis`.

"""
import logging
import random
import time

from ._compat import urlparse


logger = logging.getLogger(__name__)


try:
    from redis import Redis as RedisBase
    from redis.exceptions import ResponseError
except ImportError:
    RedisBase = object


class Redis(RedisBase):
    response_error_max_retries = 20
    shared_connection_pool = None

    def __init__(self, host='localhost', port=6379,
                 db=0, password=None, socket_timeout=None,
                 connection_pool=None, charset='utf-8',
                 errors='strict', decode_responses=False,
                 unix_socket_path=None):
        if connection_pool is None:
            connection_pool = self.__class__.shared_connection_pool
        super(Redis, self).__init__(host=host, port=port, db=db,
                                    password=password,
                                    socket_timeout=socket_timeout,
                                    connection_pool=connection_pool,
                                    charset=charset, errors=errors,
                                    decode_responses=decode_responses,
                                    unix_socket_path=unix_socket_path)
        if self.__class__.shared_connection_pool is None:
            self.__class__.shared_connection_pool = self.connection_pool

    def execute_command(self, *args, **kwargs):
        retry = self.response_error_max_retries
        backoff = 1
        while retry > 0:
            retry -= 1
            try:
                return super(Redis, self).execute_command(*args, **kwargs)
            except ResponseError as exc:
                logger.debug('Redis server appears to be busy: %s', exc)
                if retry > 0:
                    delay = random.random() * backoff
                    logger.debug('Waiting %.1f seconds before retrying', delay)
                    time.sleep(delay)
                    backoff += 2
                else:
                    logger.exception('Maximum number of retries reached')
                    raise


def from_url(url, db=None, **kwargs):
    host, port, db_, password = _parse_redis_url(url)
    if db is None:
        db = db_
    return Redis(host=host, port=port, db=db, password=password, **kwargs)


def _parse_redis_url(url):
    urlparts = urlparse(url)
    assert urlparts.scheme == 'redis' or not urlparts.scheme
    host = urlparts.hostname
    port = int(urlparts.port or 6379)
    try:
        db = int(urlparts.path.replace('/', ''))
    except (AttributeError, ValueError):
        db = 0
    password = urlparts.password
    return host, port, db, password
