import os

from flask import Flask
from flask.ext.cache import Cache
from flask.ext.gzip import Gzip

from naverwebtoonfeeds.models import db

app = Flask(__name__)
app.config.from_object('naverwebtoonfeeds.default_settings')
if os.environ.get('NAVERWEBTOONFEEDS_SETTINGS'):
    app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

db.init_app(app)
cache = Cache(app)
if app.config.get('GZIP'):
    gzip = Gzip(app)

# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10   # It works for Redis.
if app.config.get('CACHE_TYPE') == 'memcached':
    CACHE_PERMANENT = 0

import naverwebtoonfeeds.views
import naverwebtoonfeeds.helpers
