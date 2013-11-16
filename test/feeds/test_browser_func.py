from netaddr import IPAddress

from test import TestCase
from ..util import mock_obj, Mock, read_fixture, patch
import naverwebtoonfeeds.feeds.browser as feeds_browser


class TestBrowser(TestCase):

    @patch('naverwebtoonfeeds.feeds.browser.get_public_ip')
    def test_get_access_denied(self, mock_get_public_ip):
        self.b = feeds_browser.Browser()
        self.b.public_ip = IPAddress('1.3.5.7')
        self.b.session = Mock()
        self.b.session.get.return_value.status_code = 403
        self.b.session.get.return_value.raise_for_status.side_effect = feeds_browser.requests.exceptions.HTTPError()
        self.assertRaises(feeds_browser.AccessDenied, self.b.get, 'http://www.naver.com/')

    @patch('naverwebtoonfeeds.feeds.browser.get_public_ip')
    def test_get_access_denied_known_address(self, mock_get_public_ip):
        self.b = feeds_browser.Browser()
        self.b.public_ip = IPAddress('50.16.1.2')
        self.b.session = Mock()
        self.b.session.get.return_value.url = 'http://www.naver.com/'
        self.assertRaises(feeds_browser.AccessDenied, self.b.get, 'http://www.naver.com/')
        self.assertFalse(self.b.session.get.called)

    @patch('naverwebtoonfeeds.feeds.browser.get_public_ip')
    def test_get_issues(self, mock_get_public_ip):
        self.b = feeds_browser.Browser()
        self.b.session = Mock()
        self.b.session.get.side_effect = lambda url, **kwargs: mock_obj(url=url, text=read_fixture('weekday.nhn.html'))
        self.assertEqual(self.b.get_issues(), read_fixture('weekday.nhn.parsed.yaml'))
