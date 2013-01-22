import logging
import urlparse

from flask import Response, render_template, request, redirect
import pytz
import heroku

from naverwebtoonfeeds import app, cache
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.naver import NAVER_TIMEZONE


# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10   # It works for Redis.
if app.config.get('CACHE_TYPE') == 'memcached':
    CACHE_PERMANENT = 0


__logger__ = logging.getLogger(__name__)


def redirect_to_canonical_url(view):
    def new_view(*args, **kwargs):
        path = request.environ['RAW_URI'] if 'RAW_URI' in request.environ else urlpath(request.url)
        canonical_url = app.config['URL_ROOT'] + path
        __logger__.debug('request.url=%s, canonical_url=%s', request.url, canonical_url)
        if app.config.get('FORCE_REDIRECT') and request.url != canonical_url:
            __logger__.info('Redirecting to the canonical URL')
            return redirect(canonical_url, 301)
        else:
            return view(*args, **kwargs)
    new_view.__name__ = view.__name__
    new_view.__doc__ = view.__doc__
    return new_view


def urlpath(url):
    parts = urlparse.urlsplit(url)
    path = parts.path
    if parts.query:
        path += '?' + parts.query
    if parts.fragment:
        path += '#' + parts.fragment
    return path


def render_and_cache_feed_index():
    series_list = Series.query.order_by(Series.title).all()
    response = render_template('feed_index.html', series_list=series_list)
    cache.set('feed_index', response, CACHE_PERMANENT)
    return response


def render_and_cache_feed_show(series):
    chapters = []
    for chapter in series.chapters:
        # pubdate_with_tz is used in templates to correct time zone
        pubdate_with_tz = pytz.utc.localize(chapter.pubdate).astimezone(NAVER_TIMEZONE)
        chapter.pubdate_with_tz = pubdate_with_tz
        chapters.append(chapter)
    xml = render_template('feed_show.xml', series=series, chapters=chapters)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set('feed_show_%d' % series.id, response, CACHE_PERMANENT)
    return response


def enqueue_job(func, args=None, kwargs=None):
    if app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
        heroku_scale('worker', 1)
    from naverwebtoonfeeds import redis_queue
    redis_queue.enqueue_call(func=func,
            args=args,
            kwargs=kwargs,
            result_ttl=0,
            timeout=3600)


def heroku_scale(process_name, qty):
    # Currently it's not possible to scale processes between 0 and 1 using the
    # public API. Below is a quick-and-dirty workaround for that issue.
    # pylint: disable=W0212
    cloud = heroku.from_key(app.config['HEROKU_API_KEY'])
    cloud._http_resource(method='POST',
        resource=('apps', app.config['HEROKU_APP_NAME'], 'ps', 'scale'),
        data=dict(type=process_name, qty=qty))
