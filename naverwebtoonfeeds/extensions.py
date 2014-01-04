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


try:
    from redismod import Redis
    from rq import Queue

    redis_connection = Redis()
    redis_queue = Queue(connection=redis_connection)
except ImportError:
    redis_connection = None
    redis_queue = None
