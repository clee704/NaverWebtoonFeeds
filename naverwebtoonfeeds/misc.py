from functools import wraps
import logging
import urlparse
import re

from flask import request, redirect
import heroku
import lxml.html
import pytz
import requests

from naverwebtoonfeeds.objects import app
from naverwebtoonfeeds.constants import NAVER_TIMEZONE, URLS, MOBILE_URLS


__logger__ = logging.getLogger(__name__)


def naver_url(series_id, chapter_id=None, mobile=False):
    """Return appropriate webtoon URL for the given arguments."""
    key = 'series' if chapter_id is None else 'chapter'
    urls = URLS if not mobile else MOBILE_URLS
    return urls[key].format(series_id=series_id, chapter_id=chapter_id)


def as_naver_time_zone(datetime_obj):
    return pytz.utc.localize(datetime_obj).astimezone(NAVER_TIMEZONE)


def inner_html(element):
    u"""
    Return the string for this HtmlElement, without enclosing start and end
    tags, or an empty string if this is a self-enclosing tag.

    """
    outer = lxml.html.tostring(element, encoding='UTF-8').decode('UTF-8')
    i, j = outer.find('>'), outer.rfind('<')
    return outer[i + 1:j]


def get_public_ip():
    """Get the public IP of the server where this app is running."""
    data = requests.get('http://checkip.dyndns.com/').text
    return re.search(r'Address: (\d+\.\d+\.\d+\.\d+)', data).group(1)


def urlpath(url):
    parts = urlparse.urlsplit(url)
    path = parts.path
    if parts.query:
        path += '?' + parts.query
    if parts.fragment:
        path += '#' + parts.fragment
    return path


def heroku_scale(process_name, qty):
    # Currently it's not possible to scale processes between 0 and 1 using the
    # public API. Below is a quick-and-dirty workaround for that issue.
    # pylint: disable=W0212
    cloud = heroku.from_key(app.config['HEROKU_API_KEY'])
    cloud._http_resource(method='POST',
        resource=('apps', app.config['HEROKU_APP_NAME'], 'ps', 'scale'),
        data=dict(type=process_name, qty=qty))


def enqueue_job(func, args=None, kwargs=None):
    if app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
        heroku_scale('worker', 1)
    from naverwebtoonfeeds.objects import redis_queue
    redis_queue.enqueue_call(func=func,
            args=args,
            kwargs=kwargs,
            result_ttl=0,
            timeout=3600)


def redirect_to_canonical_url(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        path = request.environ['RAW_URI'] if 'RAW_URI' in request.environ else urlpath(request.url)
        canonical_url = app.config['URL_ROOT'] + path
        __logger__.debug('request.url=%s, canonical_url=%s', request.url, canonical_url)
        if app.config.get('FORCE_REDIRECT') and request.url != canonical_url:
            __logger__.info('Redirecting to the canonical URL')
            return redirect(canonical_url, 301)
        else:
            return f(*args, **kwargs)
    return decorated_function
