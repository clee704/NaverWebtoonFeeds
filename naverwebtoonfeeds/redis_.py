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
    response_error_max_retries = 10

    def __init__(self, *args, **kwargs):
        self._initialized = False
        if args or kwargs:
            super(Redis, self).__init__(*args, **kwargs)
            self._initialized = True

    def init_app(self, app):
        if not self._initialized:
            host, port, db, password = _parse_redis_url(
                app.config['REDIS_URL'])
            super(Redis, self).__init__(host=host, port=port, db=db,
                                        password=password)
            self._initialized = True
        else:
            raise RuntimeError('already initialized')

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
                    backoff *= 2
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
