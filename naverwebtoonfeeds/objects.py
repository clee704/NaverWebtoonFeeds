# pylint: disable=E0611,F0401,C0103
import logging
import logging.config
import os
import sys

from flask import Flask
from flask.ext.cache import Cache
from flask.ext.assets import Environment, Bundle

from naverwebtoonfeeds.models import db


__logger__ = logging.getLogger(__name__)


app = Flask(__name__)


# Configuration handling
mode = os.environ.get('NWF_MODE')
try:
    app.config.from_object('naverwebtoonfeeds.config.{0}.Config'.format(mode))
except ImportError:
    import naverwebtoonfeeds.config
    modes = ', '.join(naverwebtoonfeeds.config.__all__)
    print >> sys.stderr, 'Invalid NWF_MODE:', mode
    print >> sys.stderr, 'Valid modes:', modes
    sys.exit(1)


# Make sure the logger is created.
# pylint: disable=W0104
app.logger
logging.config.dictConfig(app.config['LOGGING'])


db.init_app(app)


cache = Cache(app)
if app.config.get('ENABLE_CACHE_COMPRESSION') and app.config.get('CACHE_TYPE') == 'redis':
    from naverwebtoonfeeds.cache import CompressedRedisCache
    cache.cache.__class__ = CompressedRedisCache


if app.config.get('GZIP'):
    from flask.ext.gzip import Gzip
    gzip = Gzip(app)


if app.config.get('USE_REDIS_QUEUE'):
    from redis import Redis
    from rq import Queue
    redis_connection = Redis(host=app.config['CACHE_REDIS_HOST'],
            port=app.config['CACHE_REDIS_PORT'],
            password=app.config['CACHE_REDIS_PASSWORD'])
    redis_queue = Queue(connection=redis_connection)


assets = Environment(app)
assets.register('js_all',
    'jquery.min.js',
    'bootstrap/js/bootstrap.min.js',
    'jquery.lazyload.min.js',
    Bundle('jquery.delayedlast.js.coffee',
        'application.js.coffee',
        filters='coffeescript,yui_js'),
    output='gen/packed.%(version)s.js'
)
assets.register('css_all',
    Bundle('bootstrap/css/bootstrap.min.css',
        'bootstrap/css/bootstrap-responsive.min.css',
        filters='cssrewrite'),
    Bundle('application.css.scss', filters='scss,yui_css'),
    output='gen/packed.%(version)s.css'
)


import naverwebtoonfeeds.views
import naverwebtoonfeeds.template


# Log the current IP address
# since Naver blocks requests from some IP address ranges.
try:
    from naverwebtoonfeeds.misc import get_public_ip
    __logger__.info('Current IP: %s', get_public_ip())
except:
    __logger__.info('Failed to get the public IP')
