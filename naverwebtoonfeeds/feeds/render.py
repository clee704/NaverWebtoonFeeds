import logging

from flask import Response, render_template, current_app

from ..extensions import cache
from .models import Series


__logger__ = logging.getLogger(__name__)


def permanent_cache():
    """Returns a expiry time for permanent cache."""
    seconds = 86400 * 365 * 10   # for Redis
    if current_app.config.get('CACHE_TYPE') == 'memcached':
        seconds = 0  # 0 means infinity in memcached
    return seconds


def render_feed_index():
    series_list = Series.query.order_by(Series.title).all()
    response = render_template('index.html', series_list=series_list)
    cache.set('feed_index', response, permanent_cache())
    return response


def render_feed_show(series):
    xml = render_template('show.xml', series=series)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set('feed_show_%d' % series.id, response, permanent_cache())
    return response
