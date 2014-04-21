"""
    naverwebtoonfeeds.feeds.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines endpoints for feeds.

"""
import logging

from flask import Blueprint, render_template, Response

from ..ext import cache
from .helpers import feed_cache_key, index_cache_key, naver_url
from .models import Series
from .signals import feed_requested, index_requested


feeds = Blueprint('feeds', __name__, template_folder='templates')

logger = logging.getLogger(__name__)


@feeds.route('/')
def index():
    """Returns a page that contains feeds."""
    index_requested.send(feeds)
    response = cache.get(index_cache_key())
    if response:
        logger.debug('Cache hit for /')
        return response
    return render_index()


@feeds.route('/feeds/<int:series_id>.xml')
def show(series_id):
    """Returns an Atom feed containing all episodes of the specified series."""
    feed_requested.send(feeds, series_id=series_id)
    response = cache.get(feed_cache_key(series_id))
    if response:
        logger.debug('Cache hit for /feeds/%d.xml', series_id)
        return response
    return render_feed(series_id)


@feeds.before_app_first_request
def remove_index_cache():
    # Without it, assets are not regenerated even if there are changes.
    cache.delete(index_cache_key())


@feeds.context_processor
def context():
    return dict(naver_url=naver_url)


def render_index():
    series_list = Series.query.order_by(Series.title).all()
    response = render_template('feeds/index.html', series_list=series_list)
    cache.set_permanently(index_cache_key(), response)
    return response


def render_feed(series_id):
    series = Series.query.get_or_404(series_id)
    xml = render_template('feeds/show.xml', series=series)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set_permanently(feed_cache_key(series.id), response)
    return response
