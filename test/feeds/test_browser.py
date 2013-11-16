from netaddr import IPAddress

from test import TestCase
from ..util import patch
import naverwebtoonfeeds.feeds.browser as feeds_browser


class TestBrowser(TestCase):

    @patch('naverwebtoonfeeds.feeds.browser.get_public_ip')
    def test_is_denied(self, mock_get_public_ip):
        self.b = feeds_browser.Browser()
        blacklist = ['204.236.194.51', '184.72.135.214', '50.16.183.158',
            '184.73.32.85', '50.17.104.181']
        allowed_addrs = ['174.129.79.204', '23.22.101.166', '23.21.14.123',
            '54.242.243.101', '54.242.231.213']
        for addr in blacklist:
            self.assertTrue(self.b.is_denied(IPAddress(addr)))
        for addr in allowed_addrs:
            self.assertFalse(self.b.is_denied(IPAddress(addr)))
