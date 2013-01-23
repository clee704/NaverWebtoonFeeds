import logging

from flask import Response, render_template

from naverwebtoonfeeds import app, cache
from naverwebtoonfeeds.models import Series


# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10   # It works for Redis.
if app.config.get('CACHE_TYPE') == 'memcached':
    CACHE_PERMANENT = 0


__logger__ = logging.getLogger(__name__)


def render_feed_index():
    series_list = Series.query.order_by(Series.title).all()
    response = render_template('feed_index.html', series_list=series_list)
    cache.set('feed_index', response, CACHE_PERMANENT)
    return response


def render_feed_show(series):
    xml = render_template('feed_show.xml', series=series)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set('feed_show_%d' % series.id, response, CACHE_PERMANENT)
    return response
