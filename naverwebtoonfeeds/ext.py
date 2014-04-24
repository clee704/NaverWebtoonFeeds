"""
    naverwebtoonfeeds.ext
    ~~~~~~~~~~~~~~~~~~~~~

    Creates and configures Flask extension objects.

"""
from os.path import dirname, join

from flask import current_app
from flask_assets import Environment
from flask_sqlalchemy import SQLAlchemy

from .cache import Cache
from .gzip import Gzip


assets_env = Environment()
cache = Cache()
db = SQLAlchemy()
gzip = Gzip()


def get_queue():
    try:
        from flask import _app_ctx_stack as stack
    except ImportError:
        from flask import _request_ctx_stack as stack
    ctx = stack.top
    if ctx is not None:
        if not hasattr(ctx, 'queue'):
            import rq
            rq.connections.use_connection(
                current_app.extensions['cache'][cache]._client)
            ctx.queue = rq.Queue()
        return ctx.queue


assets_env.from_yaml(join(dirname(__file__), 'static/assets.yaml'))
