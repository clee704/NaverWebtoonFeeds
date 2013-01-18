import logging
import os

from flask import Flask
from flask.ext.cache import Cache
from flask.ext.assets import Environment, Bundle

from naverwebtoonfeeds.models import db

app = Flask(__name__)
app.config.from_object('naverwebtoonfeeds.default_settings')
if os.environ.get('NAVERWEBTOONFEEDS_SETTINGS'):
    app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

def setup_loggers():
    loggers = [app.logger, logging.getLogger('sqlalchemy.engine')]
    formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    for logger in loggers:
        logger.setLevel(app.config['LOG_LEVEL'])
        logger.addHandler(stream_handler)
    if app.config.get('SEND_EMAIL'):
        from logging.handlers import SMTPHandler
        mail_options = 'HOST FROMADDR TOADDRS SUBJECT CREDENTIALS SECURE'
        mail_config = (app.config['MAIL_' + x] for x in mail_options.split())
        smtp_handler = SMTPHandler(*mail_config)
        smtp_handler.setLevel(app.config['EMAIL_LEVEL'])
        smtp_handler.setFormatter(formatter)
        for logger in loggers:
            logger.addHandler(smtp_handler)
setup_loggers()

db.init_app(app)

cache = Cache(app)

if app.config.get('GZIP'):
    from flask.ext.gzip import Gzip
    gzip = Gzip(app)

if app.config.get('USE_REDIS_QUEUE'):
    from redis import Redis
    from rq import Queue
    connection = Redis(host=app.config['CACHE_REDIS_HOST'],
            port=app.config['CACHE_REDIS_PORT'],
            password=app.config['CACHE_REDIS_PASSWORD'])
    queue = Queue(connection=connection)

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

# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10   # It works for Redis.
if app.config.get('CACHE_TYPE') == 'memcached':
    CACHE_PERMANENT = 0

import naverwebtoonfeeds.views
import naverwebtoonfeeds.helpers
