"""
    naverwebtoonfeeds.redis_
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Implements customized versions of :class:`redis.Redis`.

"""
import logging
import random
import time

from redis import Redis as RedisBase
from redis.exceptions import ResponseError


logger = logging.getLogger(__name__)


class Redis(RedisBase):

    response_error_max_retries = 10

    def __init__(self, *args, **kwargs):
        self._initialized = False
        if args or kwargs:
            super(Redis, self).__init__(*args, **kwargs)
            self._initialized = True

    def init(self, *args, **kwargs):
        if not self._initialized:
            super(Redis, self).__init__(*args, **kwargs)
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
            except ResponseError:
                logger.debug('Redis server appears to be busy')
                if retry > 0:
                    delay = random.random() * backoff
                    logger.debug('Waiting %.1f seconds before retrying', delay)
                    time.sleep(delay)
                    backoff *= 2
                else:
                    logger.exception('Maximum number of retries reached')
                    raise
