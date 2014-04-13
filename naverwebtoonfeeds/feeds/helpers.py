"""
    naverwebtoonfeeds.feeds.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements various helpers.

"""
import logging
import re

import lxml.html
import pytz
from flask import current_app
from netaddr import IPAddress

from .._compat import iteritems, URLError, urlopen


NAVER_TIMEZONE = pytz.timezone('Asia/Seoul')

_BASE_URL = 'http://comic.naver.com/webtoon'
_MOBILE_BASE_URL = 'http://m.comic.naver.com/webtoon'
_SUBPATHS = {
    'last_chapter': '/detail.nhn?titleId={series_id}',
    'chapter': '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'series': '/list.nhn?titleId={series_id}',
    'series_by_day': '/weekday.nhn',
    'completed_series': '/finish.nhn',
}

NAVER_URLS = dict((key, _BASE_URL + _SUBPATHS[key]) for key in _SUBPATHS)
MOBILE_NAVER_URLS = dict((key, _MOBILE_BASE_URL + _SUBPATHS[key]) for key
                         in _SUBPATHS)

logger = logging.getLogger(__name__)


def index_cache_key():
    return 'feeds:v:index'


def feed_cache_key(feed_id):
    return 'feeds:v:show:{id}'.format(id=feed_id)


def naver_url(series_id, chapter_id=None, mobile=False):
    """Returns a webtoon URL for the given arguments."""
    key = 'series' if chapter_id is None else 'chapter'
    urls = NAVER_URLS if not mobile else MOBILE_NAVER_URLS
    return urls[key].format(series_id=series_id, chapter_id=chapter_id)


def as_naver_time_zone(datetime_obj):
    return pytz.utc.localize(datetime_obj).astimezone(NAVER_TIMEZONE)


def get_public_ip():
    """Returns the public IP of the server where this app is running."""
    for url, pattern in iteritems(current_app.config['PUBLIC_IP_SERVERS']):
        logger.debug('Trying to get public IP using %s', url)
        data = None
        try:
            data = urlopen(url, timeout=60).read()
            ip_str = re.search(pattern, data).group(1)
            return IPAddress(ip_str)
        except (AttributeError, IndexError, TypeError):
            logger.debug('Unrecognizable data: %r', data, exc_info=True)
        except URLError as exc:
            logger.debug("Couln't get %s: %s", url, exc)


def inner_html(element):
    """Returns the string for this HtmlElement, without enclosing start and
    end tags, or an empty string if this is a self-enclosing tag.

    """
    outer_html = lxml.html.tostring(element, encoding='UTF-8').decode('UTF-8')

    # Since the output of lxml.html.tostring is well-formed, we can simply
    # use character matching.
    return outer_html[outer_html.find('>') + 1:outer_html.rfind('<')]
