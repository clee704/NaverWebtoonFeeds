import logging
import os

from flask import Flask
from flask.ext.cache import Cache
from flask.ext.gzip import Gzip
from flask.ext.assets import Environment, Bundle

from naverwebtoonfeeds.models import db

app = Flask(__name__)
app.config.from_object('naverwebtoonfeeds.default_settings')
if os.environ.get('NAVERWEBTOONFEEDS_SETTINGS'):
    app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

db.init_app(app)
cache = Cache(app)
if app.config.get('GZIP'):
    gzip = Gzip(app)

assets = Environment(app)
assets.register('js_all',
    'bootstrap/js/bootstrap.min.js',
    Bundle('application.js', filters='yui_js'),
    output='gen/packed.js'
)
assets.register('css_all',
    Bundle('bootstrap/css/bootstrap.min.css',
        'bootstrap/css/bootstrap-responsive.min.css',
        filters='cssrewrite'),
    Bundle('application.css', filters='yui_css'),
    output='gen/packed.css'
)

# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10   # It works for Redis.
if app.config.get('CACHE_TYPE') == 'memcached':
    CACHE_PERMANENT = 0

# Logging settings
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

import naverwebtoonfeeds.views
import naverwebtoonfeeds.helpers
