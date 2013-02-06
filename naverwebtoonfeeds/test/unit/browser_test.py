import unittest

from netaddr import IPAddress

import naverwebtoonfeeds.browser as b


# pylint: disable=C0103,R0904,E1103,R0201,C0301
class BrowserTest(unittest.TestCase):

    def test_is_forbidden(self):
        forbidden_addrs = ['204.236.194.51', '184.72.135.214', '50.16.183.158',
            '184.73.32.85', '50.17.104.181']
        allowed_addrs = ['174.129.79.204', '23.22.101.166', '23.21.14.123',
            '54.242.243.101', '54.242.231.213']
        browser = b.Browser()
        for addr in forbidden_addrs:
            self.assertTrue(browser.is_forbidden(IPAddress(addr)))
        for addr in allowed_addrs:
            self.assertFalse(browser.is_forbidden(IPAddress(addr)))
