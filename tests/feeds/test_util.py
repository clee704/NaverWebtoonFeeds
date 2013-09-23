# -*- coding: UTF-8 -*-
from datetime import datetime

import lxml.html
from netaddr import IPAddress

from tests import TestCase
from ..util import Mock, patch
from naverwebtoonfeeds.feeds.constants import NAVER_TIMEZONE
from naverwebtoonfeeds.feeds.models import Config
import naverwebtoonfeeds.feeds.util as feeds_util


class TestUtil(TestCase):

    @patch('naverwebtoonfeeds.feeds.util.current_app')
    @patch('naverwebtoonfeeds.feeds.util.heroku')
    def test_heroku_scale(self, mock_heroku, mock_current_app):
        mock_current_app.config = dict(HEROKU_API_KEY='foobar123', HEROKU_APP_NAME='testapp')
        feeds_util.heroku_scale('beaver', 5)
        mock_heroku.from_key.assert_called_with('foobar123')
        mock_heroku.from_key('foobar123')._http_resource.assert_called_with(
                method='POST',
                resource=('apps', 'testapp', 'ps', 'scale'),
                data=dict(type='beaver', qty=5)
        )
        assert Config.query.get('heroku:beaver').value == 5
        mock_heroku.from_key('foobar123')._http_resource.reset_mock()
        feeds_util.heroku_scale('beaver', 5)
        assert not mock_heroku.from_key('foobar123')._http_resource.called

    def test_naver_url(self):
        self.assertEqual(feeds_util.naver_url(42), 'http://comic.naver.com/webtoon/list.nhn?titleId=42')

    def test_naver_url_with_chapter_id(self):
        self.assertEqual(feeds_util.naver_url(42, 1), 'http://comic.naver.com/webtoon/detail.nhn?titleId=42&no=1')

    def test_naver_url_with_mobile(self):
        self.assertEqual(feeds_util.naver_url(42, mobile=True), 'http://m.comic.naver.com/webtoon/list.nhn?titleId=42')

    def test_naver_url_with_chapter_id_with_mobile(self):
        self.assertEqual(feeds_util.naver_url(42, 1, mobile=True),
                'http://m.comic.naver.com/webtoon/detail.nhn?titleId=42&no=1')

    def test_as_naver_time_zone(self):
        self.assertEqual(feeds_util.as_naver_time_zone(datetime(2013, 1, 1, 0)),
                NAVER_TIMEZONE.localize(datetime(2013, 1, 1, 9)))

    def test_inner_html_1(self):
        elem = lxml.html.fromstring('<p>hello,<br>world!</p>')
        self.assertEqual(feeds_util.inner_html(elem), 'hello,<br>world!')

    def test_inner_html_2(self):
        elem = lxml.html.fromstring('<div class="foo"><span>bar <span>bar</span></span> bar</div>')
        self.assertEqual(feeds_util.inner_html(elem), '<span>bar <span>bar</span></span> bar')

    def test_inner_html_3(self):
        elem = lxml.html.fromstring('<img src="http://nowhere.com/nothing.jpg" />')
        self.assertEqual(feeds_util.inner_html(elem), '')

    def test_inner_html_4(self):
        elem = lxml.html.fromstring(u'<p>논-아스키</p>')
        self.assertEqual(feeds_util.inner_html(elem), u'논-아스키')

    @patch('naverwebtoonfeeds.feeds.util.requests')
    def test_get_public_ip(self, mock_requests):
        mock_requests.get.return_value.text = '<html><head><title>Current IP Check</title></head><body>Current IP Address: 1.2.3.4</body></html>'
        rv = feeds_util.get_public_ip()
        mock_requests.get.assert_called_with('http://checkip.dyndns.com/')
        self.assertEqual(rv, IPAddress('1.2.3.4'))
