# -*- coding: UTF-8 -*-
from datetime import datetime
import logging
import re
import time
import urllib2

import lxml.html
import lxml.html.soupparser
import pytz
import requests

BASE_URL = 'http://comic.naver.com/webtoon'
MOBILE_BASE_URL = 'http://m.comic.naver.com/webtoon'
URL = {
    'last_chapter': BASE_URL + '/detail.nhn?titleId={series_id}',
    'chapter': BASE_URL + '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'mobile': MOBILE_BASE_URL + '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'series': BASE_URL + '/list.nhn?titleId={series_id}',
    'series_by_day': BASE_URL + '/weekday.nhn',
    'completed_series': BASE_URL + '/finish.nhn',
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; ko; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate',
    'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
}
NAVER_TIMEZONE = pytz.timezone('Asia/Seoul')


__logger__ = logging.getLogger(__name__)


class NaverBrowser(object):

    def __init__(self, app, max_retry=3):
        self.app = app
        self.cookies = None
        self.headers = HEADERS.copy()
        self.max_retry = max_retry

    def get(self, url):
        errors = 0
        delay = 1
        while True:
            try:
                # Requests to Naver should be carefully monitored.
                __logger__.warning('Requesting GET %s', url)
                response = requests.get(url, cookies=self.cookies, headers=self.headers)
                self.cookies = response.cookies
                if self.login_required(response):
                    self.login()
                    continue
                if response.status_code == 403:
                    __logger__.warning('Forbidden IP: %s', get_public_ip())
                    raise urllib2.HTTPError(url, 403, 'Forbidden', response.headers, None)
                return response
            except urllib2.URLError:
                __logger__.info('A URLError occurred', exc_info=True)
                errors += 1
                if errors > self.max_retry:
                    raise
                __logger__.info('Waiting for %d seconds before reconnecting', delay)
                time.sleep(delay)
                delay += 0.5

    def login_required(self, response):
        __logger__.info('Checking the URL: %s', response.url)
        return 'login' in response.url

    def login(self):
        if not self.app.config.get('NAVER_USERNAME'):
            return
        url = 'https://nid.naver.com/nidlogin.login'
        headers = dict(Referer='http://static.nid.naver.com/login.nhn')
        headers.update(self.headers)
        data = {
            'enctp': '2',
            'id': self.app.config['NAVER_USERNAME'],
            'pw': self.app.config['NAVER_PASSWORD'],
        }
        self.get('http://www.naver.com')   # Get cookies
        response = requests.post(url, data=data, cookies=self.cookies, headers=headers)
        self.cookies = response.cookies
        if 'location.replace' not in response.text[:100]:
            raise RuntimeError("Cannot log in to naver.com")
        __logger__.info('Logged in')

    def _parse(self, response, method, *args):
        parsers = [lxml.html.soupparser, lxml.html]
        # lxml.html.soupparser.fromstring is generally more tolerant than
        # lxml.html.fromstring, so it can parse HTML with unescaped brackets
        # (<, >) which appear often. But there are some cases where
        # lxml.html.soupparser.fromstring misbehaves while lxml.html.fromstring
        # works.
        for parser in parsers:
            try:
                doc = parser.fromstring(response.text)
                return getattr(self, method)(doc, *args)
            except:
                __logger__.warning('An error occurred while parsing data for %s',
                        response.url, exc_info=True)
        raise self.ResponseUnparsable(response.url)

    def get_issues(self):
        response = self.get(URL['series_by_day'])
        return self._parse(response, '_parse_issues')

    def _parse_issues(self, doc):
        __logger__.debug('Parsing the current series list')
        retval = []
        for a_elem in doc.xpath('//*[@class="list_area daily_all"]//li/*[@class="thumb"]/a'):
            url = a_elem.attrib['href']
            match = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
            series_id, day = int(match.group('id')), match.group('day')
            uploaded = len(a_elem.xpath('em[@class="ico_updt"]')) > 0
            retval.append(dict(id=series_id, day=day, days_uploaded=day if uploaded else False))
        return retval

    def get_completed_series(self):
        response = self.get(URL['completed_series'])
        return self._parse(response, '_parse_completed_series')

    def _parse_completed_series(self, doc):
        __logger__.debug('Parsing the completed series list')
        retval = []
        for a_elem in doc.xpath('//*[@class="list_area"]//li/*[@class="thumb"]/a'):
            url = a_elem.attrib['href']
            match = re.search(r'titleId=(?P<id>\d+)', url)
            series_id = int(match.group('id'))
            retval.append(dict(id=series_id))
        return retval

    def get_series_data(self, series_id):
        url = URL['last_chapter'].format(series_id=series_id)
        response = self.get(url)
        if response.url != url:
            return dict(removed=True)
        return self._parse(response, '_parse_series_data', series_id)

    def _parse_series_data(self, doc, series_id): 
        __logger__.debug('Parsing data for series #%d', series_id)
        comicinfo_dsc = doc.xpath('//*[@class="comicinfo"]/*[@class="dsc"]')[0]
        permalink = doc.xpath('//meta[@property="og:url"]/@content')[0]
        status = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em/text()')[0].strip()
        return {
            'title': comicinfo_dsc.xpath('h2/text()')[0].strip(),
            'author': comicinfo_dsc.xpath('h2/em')[0].text_content().strip(),
            'description': inner_html(comicinfo_dsc.xpath('p[@class="txt"]')[0]),
            'last_chapter': int(re.search(r'no=(\d+)', permalink).group(1)),
            'is_completed': status == u'완결웹툰',
            'thumbnail_url': doc.xpath('//meta[@property="og:image"]/@content')[0],
        }

    def get_chapter_data(self, series_id, chapter_id):
        url = URL['chapter'].format(series_id=series_id, chapter_id=chapter_id)
        response = self.get(url)
        return self._parse(response, '_parse_chapter_data', series_id, chapter_id, url)

    def _parse_chapter_data(self, doc, series_id, chapter_id, url):
        __logger__.debug('Parsing data for chapter #%d of series #%d', chapter_id, series_id)
        if url != doc.xpath('//meta[@property="og:url"]/@content')[0]:
            return dict(not_found=True)
        date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]/@value')[0]
        naive_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        data = {
            'title': doc.xpath('//meta[@property="og:description"]/@content')[0],
            'pubdate': NAVER_TIMEZONE.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None),
            'thumbnail_url': doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/@src')[0],
        }
        if '{0}/{1}'.format(series_id, chapter_id) not in data['thumbnail_url']:
            __logger__.error('Thumbnail URL looks strange: thumbnail_url=%s, series_id=%d, chapter_id=%d',
                    data['thumbnail_url'], series_id, chapter_id)
        return data

    class ResponseUnparsable(Exception):
        pass


def inner_html(element):
    u"""
    Return the string for this HtmlElement, without enclosing start and end
    tags, or an empty string if this is a self-enclosing tag.

    >>> inner_html(lxml.html.fromstring('<p>hello,<br>world!</p>'))
    u'hello,<br>world!'
    >>> inner_html(lxml.html.fromstring('<div class="foo"><span>bar <span>bar</span></span> bar</div>'))
    u'<span>bar <span>bar</span></span> bar'
    >>> inner_html(lxml.html.fromstring('<img src="http://nowhere.com/nothing.jpg" />'))
    u''
    >>> inner_html(lxml.html.fromstring(u'<p>\ub17c\uc544\uc2a4\ud0a4</p>'))
    u'\ub17c\uc544\uc2a4\ud0a4'

    """
    outer = lxml.html.tostring(element, encoding='UTF-8').decode('UTF-8')
    i, j = outer.find('>'), outer.rfind('<')
    return outer[i + 1:j]


def get_public_ip():
    """Get the public IP of the server where this app is running."""
    data = requests.get('http://checkip.dyndns.com/').text
    return re.search(r'Address: (\d+\.\d+\.\d+\.\d+)', data).group(1)


def naver_url(series_id, chapter_id=None, mobile=False):
    """Return appropriate webtoon URL for the given arguments."""
    if mobile:
        key = 'mobile'
    elif chapter_id is None:
        key = 'series'
    else:
        key = 'chapter'
    return URL[key].format(series_id=series_id, chapter_id=chapter_id)


def as_naver_time_zone(datetime_obj):
    return pytz.utc.localize(datetime_obj).astimezone(NAVER_TIMEZONE)
