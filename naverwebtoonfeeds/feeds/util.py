import logging
import re

import lxml.html
from netaddr import IPAddress
import pytz
import requests

from .constants import URLS, MOBILE_URLS, NAVER_TIMEZONE


__logger__ = logging.getLogger(__name__)


def naver_url(series_id, chapter_id=None, mobile=False):
    """Returns a webtoon URL for the given arguments."""
    key = 'series' if chapter_id is None else 'chapter'
    urls = URLS if not mobile else MOBILE_URLS
    return urls[key].format(series_id=series_id, chapter_id=chapter_id)


def as_naver_time_zone(datetime_obj):
    return pytz.utc.localize(datetime_obj).astimezone(NAVER_TIMEZONE)


def inner_html(element):
    """
    Returns the string for this HtmlElement, without enclosing start and end
    tags, or an empty string if this is a self-enclosing tag.

    """
    outer = lxml.html.tostring(element, encoding='UTF-8').decode('UTF-8')
    i, j = outer.find('>'), outer.rfind('<')
    return outer[i + 1:j]


def get_public_ip():
    """Returns the public IP of the server where this app is running."""
    url_patterns = {
        'http://checkip.dyndns.com/': r'Address: (\d+\.\d+\.\d+\.\d+)',
        'http://ipecho.net/plain': r'(\d+\.\d+\.\d+\.\d+)',
    }
    for url, pattern in url_patterns.items():
        __logger__.debug('Trying to get public IP using %s', url)
        data = None
        try:
            data = requests.get(url, timeout=60).text
            ip_str = re.search(pattern, data).group(1)
            return IPAddress(ip_str)
        except (AttributeError, IndexError, TypeError):
            __logger__.debug('Unrecognizable data: %s', repr(data), exc_info=True)
        except (requests.ConnectionError, requests.Timeout) as e:
            __logger__.debug("Couln't get %s: %s", url, e)
