import unittest

from naverwebtoonfeeds.test.utilities import mock_obj
import naverwebtoonfeeds.view_helpers as v


# pylint: disable=C0103,R0904
class ViewHelpersTest(unittest.TestCase):

    def setUp(self):
        self.original_app = v.app
        self.original_request = v.request
        self.original_urlpath = v.urlpath

    def tearDown(self):
        v.app = self.original_app
        v.request = self.original_request
        v.urlpath = self.original_urlpath

    def test_urlpath_minimum(self):
        self.assertEqual(v.urlpath('http://a.co'), '')

    def test_urlpath_root(self):
        self.assertEqual(v.urlpath('http://foo.bar.com/'), '/')

    def test_urlpath_path(self):
        self.assertEqual(v.urlpath('http://bit.ly/bEf232'), '/bEf232')

    def test_urlpath_full(self):
        self.assertEqual(v.urlpath('http://a.co/p;p1;p2;p3?a=1&b=2#frag'),
                '/p;p1;p2;p3?a=1&b=2#frag')
