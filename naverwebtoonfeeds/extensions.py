# pylint: disable=E0611,F0401,C0103,W0231

from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()


from flask.ext.cache import Cache
cache = Cache()


from flask.ext.assets import Environment, Bundle
assets = Environment()
assets.register('js_all',
    'jquery.min.js',
    'bootstrap/js/bootstrap.min.js',
    'jquery.lazyload.min.js',
    Bundle('jquery.delayedlast.js.coffee',
        'app.js.coffee',
        filters='coffeescript,yui_js'),
    output='gen/packed.%(version)s.js'
)
assets.register('css_all',
    Bundle('bootstrap/css/bootstrap.min.css',
        'bootstrap/css/bootstrap-responsive.min.css',
        filters='cssrewrite'),
    Bundle('app.css.scss', filters='scss,yui_css'),
    output='gen/packed.%(version)s.css'
)


from flask.ext.gzip import Gzip
class MyGzip(Gzip):
    def __init__(self):
        pass
    def init_app(self, app):
        Gzip.__init__(self, app)
gzip = MyGzip()


try:
    from redis import Redis
    from rq import Queue

    # pylint: disable=R0904,R0924
    class MyRedis(Redis):
        def __init__(self):
            pass
        def init_app(self, *args, **kwargs):
            Redis.__init__(self, *args, **kwargs)

    redis_connection = MyRedis()
    redis_queue = Queue(connection=redis_connection)
except ImportError:
    redis_connection = None
    redis_queue = None
