# -*- coding: UTF-8 -*-
from datetime import datetime
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
}


class NaverBrowser(object):

    def __init__(self, app, max_retry=3):
        self.app = app
        self.cookies = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; ko; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }
        self.max_retry = max_retry

    def get(self, url):
        errors = 0
        delay = 1
        while True:
            try:
                self.app.logger.info('Requesting GET %s', url)
                response = requests.get(url, cookies=self.cookies, headers=self.headers)
                self.cookies = response.cookies
                if self.login_required(response):
                    self.login()
                    continue
                if response.status_code == 403:
                    self.app.logger.warning('Forbidden IP: %s', self._get_public_ip())
                    raise urllib2.HTTPError(url, 403, 'Forbidden', response.headers, None)
                return lxml.html.soupparser.fromstring(response.text), response
            except urllib2.URLError:
                self.app.logger.info('A URLError occurred', exc_info=True)
                errors += 1
                if errors > self.max_retry:
                    raise
                self.app.logger.info('Waiting for %d seconds before reconnecting', delay)
                time.sleep(delay)
                delay += 0.5

    def login_required(self, response):
        return 'login' in response.url

    def login(self):
        if not self.app.config.get('NAVER_USERNAME'):
            return
        url = 'https://nid.naver.com/nidlogin.login'
        headers = {'Referer': 'http://static.nid.naver.com/login.nhn'}
        headers.update(self.headers)
        data = {
            'enctp': '2',
            'id': self.app.config['NAVER_USERNAME'],
            'pw': self.app.config['NAVER_PASSWORD'],
        }
        self.get('http://www.naver.com')   # Get cookies
        r = requests.post(url, data=data, cookies=self.cookies, headers=headers)
        self.cookies = r.cookies
        if 'location.replace' not in r.text[:100]:
            raise RuntimeError("Cannot log in to naver.com")
        self.app.logger.info('Logged in')

    def get_series_list(self):
        doc, response = self.get(URL['series_by_day'])
        self.app.logger.info('Final URL: %s', response.url)
        for a in doc.xpath('//*[@class="list_area daily_all"]//li/*[@class="thumb"]/a'):
            url = a.attrib['href']
            m = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
            series_id, day = int(m.group('id')), m.group('day')
            updated = len(a.xpath('em[@class="ico_updt"]')) > 0
            yield {'id': series_id, 'day': day, 'updated': updated}

    def get_series_data(self, series_id):
        url = URL['last_chapter'].format(series_id=series_id)
        doc, response = self.get(url)
        self.app.logger.info('Final URL: %s', response.url)
        if response.url != url:
            return {'removed': True}
        try:
            self.app.logger.debug('Parsing data for series #%d', series_id)
            comicinfo_dsc = doc.xpath('//*[@class="comicinfo"]/*[@class="dsc"]')[0]
            permalink = doc.xpath('//meta[@property="og:url"]/@content')[0]
            status = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em/text()')[0].strip()
            return {
                'title': comicinfo_dsc.xpath('h2/text()')[0].strip(),
                'author': comicinfo_dsc.xpath('h2/em')[0].text_content().strip(),
                'description': inner_html(comicinfo_dsc.xpath('p[@class="txt"]')[0]),
                'last_chapter': int(re.search('no=(\d+)', permalink).group(1)),
                'is_completed': status == u'완결웹툰',
                'thumbnail_url': doc.xpath('//meta[@property="og:image"]/@content')[0],
            }
        except:
            self.app.logger.error(response.url + '\n' + response.text, exc_info=True)
            raise

    def get_chapter_data(self, series_id, chapter_id, tz):
        url = URL['chapter'].format(series_id=series_id, chapter_id=chapter_id)
        doc, response = self.get(url)
        self.app.logger.info('Final URL: %s', response.url)
        if url != doc.xpath('//meta[@property="og:url"]/@content')[0]:
            return {'not_found': True}
        self.app.logger.debug('Parsing data for chapter #%d of series #%d', chapter_id, series_id)
        date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]/@value')[0]
        naive_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        data = {
            'title': doc.xpath('//meta[@property="og:description"]/@content')[0],
            'pubdate': tz.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None),
            'thumbnail_url': doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/@src')[0],
        }
        if '{0}/{1}'.format(series_id, chapter_id) not in data['thumbnail_url']:
            self.app.logger.error('Thumbnail URL looks strange: thumbnail_url=%s, series_id=%d, chapter_id=%d', data['thumbnail_url'], series_id, chapter_id)
        return data

    def _get_public_ip(self):
        data = requests.get('http://checkip.dyndns.com/').text
        # data = '<html><head><title>Current IP Check</title></head><body>Current IP Address: 65.96.168.198</body></html>\r\n'
        return re.search('Address: (\d+\.\d+\.\d+\.\d+)', data).group(1)


def inner_html(element):
    """
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
