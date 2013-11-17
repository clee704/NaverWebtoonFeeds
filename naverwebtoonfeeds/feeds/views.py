from functools import wraps
import logging
import urlparse

from flask import Blueprint, current_app, request, redirect

from ..extensions import cache
from .models import Series
from .render import render_feed_index, render_feed_show
from .update import series_list_needs_fetching, update_series_list, update_series
from .util import naver_url
from .worker import enqueue_update_series_list, enqueue_update_series


__logger__ = logging.getLogger(__name__)


#: Blueprint for feeds.
feeds = Blueprint('feeds', __name__, template_folder='templates')


def redirect_to_canonical_url(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        path = request.environ['RAW_URI'] if 'RAW_URI' in request.environ else urlpath(request.url)
        canonical_url = current_app.config['URL_ROOT'] + path
        if current_app.config.get('FORCE_REDIRECT') and request.url != canonical_url:
            __logger__.debug('request.url=%s != canonical_url=%s', request.url, canonical_url)
            __logger__.info('Redirecting to the canonical URL')
            return redirect(canonical_url, 301)
        else:
            return f(*args, **kwargs)
    return wrapper


@feeds.route('/')
@redirect_to_canonical_url
def index():
    """Returns a cached index page containing feeds."""
    invalidate_cache = False
    if series_list_needs_fetching():
        if current_app.config.get('USE_REDIS_QUEUE'):
            enqueue_update_series_list()
        else:
            invalidate_cache = update_series_list()[0]
    if not invalidate_cache:
        response = cache.get('feed_index')
        if response:
            __logger__.debug('Cache hit for /')
            return response
    return render_feed_index()


@feeds.route('/feeds/<int:series_id>.xml')
@redirect_to_canonical_url
def show(series_id):
    """
    Returns a cached Atom feed containing all episodes of the given series.

    """
    series = None
    invalidate_cache = False
    if series_list_needs_fetching():
        if current_app.config.get('USE_REDIS_QUEUE'):
            enqueue_update_series_list()
        elif update_series_list()[0]:
            cache.delete('feed_index')
    series = Series.query.get_or_404(series_id)
    if series.new_chapters_available:
        if current_app.config.get('USE_REDIS_QUEUE'):
            enqueue_update_series(series_id)
        else:
            invalidate_cache = any(update_series(series))
    if not invalidate_cache:
        response = cache.get('feed_show_%d' % series_id)
        if response:
            __logger__.debug('Cache hit for /feeds/%d.xml', series_id)
            return response
    return render_feed_show(series)


@feeds.context_processor
def context():
    return dict(naver_url=naver_url)


def urlpath(url):
    parts = urlparse.urlsplit(url)
    path = parts.path
    if parts.query:
        path += '?' + parts.query
    if parts.fragment:
        path += '#' + parts.fragment
    return path
