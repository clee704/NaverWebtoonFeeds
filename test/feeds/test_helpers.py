# -*- coding: UTF-8 -*-
from datetime import datetime

import lxml.html
from netaddr import IPAddress

from naverwebtoonfeeds.feeds.helpers import (
    as_naver_time_zone, get_public_ip, inner_html, NAVER_TIMEZONE, naver_url)

from ..conftest import MockHTTPHandler


def test_naver_url():
    assert naver_url(3) == 'http://comic.naver.com/webtoon/list.nhn?titleId=3'


def test_naver_url_with_chapter_id():
    assert (naver_url(42, 1) ==
            'http://comic.naver.com/webtoon/detail.nhn?titleId=42&no=1')


def test_naver_url_with_mobile():
    assert (naver_url(42, mobile=True) ==
            'http://m.comic.naver.com/webtoon/list.nhn?titleId=42')


def test_naver_url_with_chapter_id_with_mobile():
    assert (naver_url(42, 1, mobile=True) ==
            'http://m.comic.naver.com/webtoon/detail.nhn?titleId=42&no=1')


def test_as_naver_time_zone():
    assert (as_naver_time_zone(datetime(2013, 1, 1, 0)) ==
            NAVER_TIMEZONE.localize(datetime(2013, 1, 1, 9)))


def test_inner_html():
    elem = lxml.html.fromstring('<p>hello,<br>world!</p>')
    assert inner_html(elem) == 'hello,<br>world!'


def test_inner_html_a_little_more_complex():
    elem = lxml.html.fromstring(
        '<div class="foo"><span>bar <span>bar</span></span> bar</div>')
    assert inner_html(elem) == '<span>bar <span>bar</span></span> bar'


def test_inner_html_with_self_closing_element():
    elem = lxml.html.fromstring('<img src="http://nowhere.com/nothing.jpg" />')
    assert inner_html(elem) == ''


def test_inner_html_with_unicode():
    elem = lxml.html.fromstring(u'<p>논-아스키</p>')
    assert inner_html(elem) == u'논-아스키'


def test_get_public_ip(app):
    with app.test_client():
        app.config['PUBLIC_IP_SERVERS'] = {
            'http://mock.com/whatsmyip': r'Your IP address is '
                                         r'(\d{1,3}(\.\d{1,3}){3})'
        }
        MockHTTPHandler.mock_urls['http://mock.com/whatsmyip'] = (
            200,
            'text/html',
            '<html><head><title>Current IP Check</title></head>'
            '<body>Your IP address is 1.2.3.4</body></html>')
        assert get_public_ip() == IPAddress('1.2.3.4')
