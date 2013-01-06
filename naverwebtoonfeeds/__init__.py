from flask import Flask
from flask.ext.cache import Cache
from flask.ext.gzip import Gzip

from naverwebtoonfeeds.models import db

app = Flask(__name__)
app.config.from_object('naverwebtoonfeeds.default_settings')
app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

db.init_app(app)
cache = Cache(app)
if app.config.get('GZIP'):
    gzip = Gzip(app)

import naverwebtoonfeeds.views
import naverwebtoonfeeds.helpers
