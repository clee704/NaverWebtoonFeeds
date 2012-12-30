from flask import Flask
from flask.ext.cache import Cache
from flask.ext.gzip import Gzip
import pytz

from naverwebtoonfeeds.models import db

app = Flask(__name__)
app.config.from_object('naverwebtoonfeeds.default_settings')
app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

db.init_app(app)
cache = Cache(app)
gzip = Gzip(app)   # for Heroku deployment; maybe redundant for others

tz = pytz.timezone('Asia/Seoul')   # Naver's time zone

import naverwebtoonfeeds.views
import naverwebtoonfeeds.helpers
