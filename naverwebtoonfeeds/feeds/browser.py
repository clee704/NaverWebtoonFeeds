# -*- coding: UTF-8 -*-
from datetime import datetime
import logging
import re
import time

from flask import current_app
import lxml.html
import lxml.html.soupparser
from netaddr import IPNetwork
import pytz
import requests

from .constants import NAVER_TIMEZONE, URLS
from .util import inner_html, get_public_ip


__logger__ = logging.getLogger(__name__)


class Browser(object):

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; ko; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
    }

    NETWORK_BLACKLIST = [IPNetwork(net) for net in [
        '50.16.0.0/15', '50.19.0.0/16', '184.72.64.0/18', '184.72.128.0/17',
        '184.73.0.0/16', '204.236.192/18',
    ]]

    def __init__(self, max_retry=3):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.max_retry = max_retry
        self.public_ip = None
        self._get_public_ip()

    def is_denied(self, addr):
        """
        Returns *True* if access from the given IPv4 address is denied by Naver.

        """
        return any(addr in net for net in self.NETWORK_BLACKLIST)

    def get(self, url):
        if self.public_ip is not None and self.is_denied(self.public_ip):
            __logger__.warning('Your IP address %s is in a blacklisted range', self.public_ip)
            raise AccessDenied()
        errors = 0
        delay = 1
        while True:
            response = None
            try:
                # Requests to Naver should be carefully monitored.
                __logger__.debug('Requesting GET %s', url)
                response = self.session.get(url)
                response.raise_for_status()
                if self.login_required(response):
                    if not self.login():
                        raise UnauthorizedRequest()
                    continue
                return response
            except UnauthorizedRequest:
                __logger__.warning('Failed to login to Naver')
                raise
            except requests.exceptions.HTTPError as e:
                __logger__.warning('An HTTP error occurred while requesting %s: %s', url, e)
                if response is not None and response.status_code == 403:
                    __logger__.warning('Access from your IP address %s is denied', self.public_ip)
                    raise AccessDenied()
            except:
                __logger__.warning('An error occurred while requesting %s', url, exc_info=True)
            errors += 1
            if errors > self.max_retry:
                raise TooManyErrors()
            __logger__.debug('Waiting for %.1f seconds before reconnecting', delay)
            time.sleep(delay)
            delay += 1

    def login(self):
        """
        Logs in to Naver and return *True* if logged in and *False* if failed.

        """
        __logger__.debug('Trying to log in to Naver')
        if not current_app.config.get('NAVER_USERNAME'):
            __logger__.info('Login failed: NAVER_USERNAME is not defined')
            return False
        url = 'https://nid.naver.com/nidlogin.login'
        data = {
            'enctp': '2',
            'id': current_app.config['NAVER_USERNAME'],
            'pw': current_app.config['NAVER_PASSWORD'],
        }
        self.get('http://www.naver.com/')   # Get initial cookies
        response = self.session.post(url, data=data,
                headers={'Referer': 'http://static.nid.naver.com/login.nhn'})
        if 'location.replace' not in response.text[:100]:
            __logger__.info('Login failed: wrong username or password')
            return False
        __logger__.info('Logged in')
        return True

    def get_issues(self):
        response = self.get(URLS['series_by_day'])
        return self._parse(response, '_parse_issues')

    def get_completed_series(self):
        response = self.get(URLS['completed_series'])
        return self._parse(response, '_parse_completed_series')

    def get_series_info(self, series_id):
        url = URLS['last_chapter'].format(series_id=series_id)
        response = self.get(url)
        if response.url != url:
            return dict(removed=True)
        return self._parse(response, '_parse_series_info', series_id)

    def get_chapter_info(self, series_id, chapter_id):
        url = URLS['chapter'].format(series_id=series_id, chapter_id=chapter_id)
        response = self.get(url)
        return self._parse(response, '_parse_chapter_info', series_id, chapter_id, url)

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
                __logger__.exception('An error occurred while parsing %s', response.url)
        raise UnparsableResponse(response.url)

    def _get_public_ip(self):
        try:
            self.public_ip = get_public_ip()
            __logger__.info('Current IP: %s', get_public_ip())
        except:
            __logger__.warning('Failed to get the public IP', exc_info=True)

    @staticmethod
    def login_required(response):
        return 'login' in response.url

    @staticmethod
    def _parse_issues(doc):
        __logger__.debug('Parsing the current series list')
        retval = []
        for a_elem in doc.xpath('//*[@class="list_area daily_all"]//li/*[@class="thumb"]/a'):
            url = a_elem.attrib['href']
            match = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
            series_id, day = int(match.group('id')), match.group('day')
            uploaded = len(a_elem.xpath('em[@class="ico_updt"]')) > 0
            retval.append(dict(id=series_id, day=day, days_uploaded=day if uploaded else False))
        return retval

    @staticmethod
    def _parse_completed_series(doc):
        __logger__.debug('Parsing the ended series list')
        retval = []
        for a_elem in doc.xpath('//*[@class="list_area"]//li/*[@class="thumb"]/a'):
            url = a_elem.attrib['href']
            match = re.search(r'titleId=(?P<id>\d+)', url)
            series_id = int(match.group('id'))
            retval.append(dict(id=series_id))
        return retval

    @staticmethod
    def _parse_series_info(doc, series_id):
        __logger__.debug('Parsing series %d', series_id)
        comicinfo_dsc = doc.xpath('//*[@class="comicinfo"]/*[@class="dsc"]')[0]
        permalink = doc.xpath('//meta[@property="og:url"]/@content')[0]
        status = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em/text()')[0].strip()
        return {
            'title': comicinfo_dsc.xpath('h2/text()')[0].strip(),
            'author': comicinfo_dsc.xpath('h2/*[@class="wrt_nm"]')[0].text_content().strip(),
            'description': inner_html(comicinfo_dsc.xpath('p[@class="txt"]')[0]),
            'last_chapter': int(re.search(r'no=(\d+)', permalink).group(1)),
            'is_completed': status == u'완결웹툰',
            'thumbnail_url': doc.xpath('//meta[@property="og:image"]/@content')[0],
        }

    @staticmethod
    def _parse_chapter_info(doc, series_id, chapter_id, url):
        __logger__.debug('Parsing chapter %d of series %d', chapter_id, series_id)
        if url != doc.xpath('//meta[@property="og:url"]/@content')[0]:
            return dict(not_found=True)
        date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]/@value')[0]
        naive_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        info = {
            'title': doc.xpath('//meta[@property="og:description"]/@content')[0],
            'pubdate': NAVER_TIMEZONE.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None),
            'thumbnail_url': doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/@src')[0],
        }
        if '{0}/{1}'.format(series_id, chapter_id) not in info['thumbnail_url']:
            __logger__.warning('Thumbnail URL looks strange: thumbnail_url=%s, series_id=%d, chapter_id=%d',
                    info['thumbnail_url'], series_id, chapter_id)
        return info


class BrowserException(Exception):
    pass


class UnparsableResponse(BrowserException):
    pass


class UnauthorizedRequest(BrowserException):
    pass


class AccessDenied(BrowserException):
    pass


class TooManyErrors(BrowserException):
    pass
