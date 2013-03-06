import unittest

from netaddr import IPAddress

from naverwebtoonfeeds.test.utilities import mock_obj, Mock, read_fixture
# pylint: disable=W0611
import naverwebtoonfeeds.objects   # Resolves a circular import issue below.
import naverwebtoonfeeds.browser as b


# pylint: disable=C0103,R0904,E1103
class BrowserTest(unittest.TestCase):

    def setUp(self):
        self.originals = {}
        for name in dir(b):
            self.originals[name] = getattr(b, name)
        self.browser = b.Browser()

    def tearDown(self):
        for name in self.originals:
            setattr(b, name, self.originals[name])

    def test_get_access_denied(self):
        b.PUBLIC_IP = IPAddress('1.3.5.7')
        self.browser.session = Mock()
        self.browser.session.get.return_value.status_code = 403
        self.browser.session.get.return_value.raise_for_status.side_effect = b.requests.exceptions.HTTPError()
        self.assertRaises(self.browser.AccessDenied, self.browser.get, 'http://www.naver.com/')

    def test_get_access_denied_known_address(self):
        b.PUBLIC_IP = IPAddress('50.16.1.2')
        self.browser.session = Mock()
        self.assertRaises(self.browser.AccessDenied, self.browser.get, 'http://www.naver.com/')
        self.assertFalse(self.browser.session.get.called)

    def test_get_issues(self):
        self.browser.session = Mock()
        self.browser.session.get.side_effect = lambda url, **kwargs: mock_obj(url=url, text=read_fixture('weekday.nhn.html'))
        self.assertEqual(self.browser.get_issues(), read_fixture('weekday.nhn.parsed.yml'))
