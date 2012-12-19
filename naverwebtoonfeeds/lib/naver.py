import re
import time
import urllib2

import lxml.html
import requests


BASE_URL = 'http://comic.naver.com/webtoon'
MOBILE_BASE_URL = 'http://m.comic.naver.com/webtoon'
URL = {
    'last_chapter': BASE_URL + '/detail.nhn?titleId={series_id}',
    'chapter': BASE_URL + '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'mobile': MOBILE_BASE_URL + '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'series': BASE_URL + '/list.nhn?titleId={series_id}',
    'series_by_day': BASE_URL + '/webtoon/weekday.nhn',
}


class NaverBrowser(object):

    def __init__(self, app, max_retry=5):
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
                self.app.logger.debug('Requesting GET %s', url)
                response = requests.get(url, cookies=self.cookies, headers=self.headers)
                self.cookies = response.cookies
                if self.login_required(response):
                    self.login()
                    continue
                if response.status_code == 403:
                    raise urllib2.HTTPError(url, 403, 'Forbidden', response.headers, None)
                return lxml.html.fromstring(response.text), response
            except urllib2.URLError:
                self.app.logger.info('A URLError occurred', exc_info=True)
                errors += 1
                if errors > self.max_retry:
                    raise
                self.app.logger.info('Waiting for %d seconds before reconnecting', delay)
                time.sleep(delay)
                delay *= 2

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
