import logging
import re

from flask import current_app
try:
    import heroku
except ImportError:
    pass
import lxml.html
from netaddr import IPAddress
import pytz
import requests

from ..extensions import db
from .constants import URLS, MOBILE_URLS, NAVER_TIMEZONE
from .models import Config


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
    data = requests.get('http://checkip.dyndns.com/').text
    ip_str = re.search(r'Address: (\d+\.\d+\.\d+\.\d+)', data).group(1)
    return IPAddress(ip_str)


def heroku_scale(process_name, qty):
    key = 'heroku:{0}'.format(process_name)
    old_qty = Config.query.get(key)
    if old_qty is not None and old_qty.value == qty:
        return
    # Currently it's not possible to scale processes between 0 and 1 using the
    # public API. Below is a quick-and-dirty workaround for that issue.
    cloud = heroku.from_key(current_app.config['HEROKU_API_KEY'])
    # pylint: disable=W0212
    try:
        cloud._http_resource(method='POST',
            resource=('apps', current_app.config['HEROKU_APP_NAME'], 'ps', 'scale'),
            data=dict(type=process_name, qty=qty))
        if old_qty is None:
            db.session.add(Config(key=key, value=qty))
        else:
            old_qty.value = qty
        db.session.commit()
    except requests.HTTPError as e:
        __logger__.error('Could not scale heroku: %s', e.message)


def enqueue_job(func, args=None, kwargs=None):
    if current_app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
        heroku_scale('worker', 1)
    from ..extensions import redis_queue
    redis_queue.enqueue_call(func=func,
            args=args,
            kwargs=kwargs,
            result_ttl=0,
            timeout=3600)
