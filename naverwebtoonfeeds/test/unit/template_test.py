import unittest

from naverwebtoonfeeds.test.utilities import mock_obj
import naverwebtoonfeeds.template as t


# pylint: disable=C0103,R0904
class TemplateTest(unittest.TestCase):

    def setUp(self):
        self.original_app = t.app

    def test_externalize(self):
        t.app = mock_obj(config=dict(URL_ROOT='https://example.com'))
        self.assertEqual(t.externalize('/foo/bar'), 'https://example.com/foo/bar')

    def test_via_imgproxy_null(self):
        t.app = mock_obj(config=dict())
        self.assertEqual(t.via_imgproxy('http://naver.com/test.png'),
                'http://naver.com/test.png')

    def test_via_imgproxy_with_url(self):
        t.app = mock_obj(config=dict(IMGPROXY_URL='http://imgproxy.com/{url}'))
        self.assertEqual(t.via_imgproxy('http://naver.com/test.png'),
                'http://imgproxy.com/http://naver.com/test.png')

    def test_via_imgproxy_with_pattern(self):
        t.app = mock_obj(config=dict(
            IMGPROXY_URL_PATTERN='http://imgproxy.com/{variable}/{url}',
            IMGPROXY_URL_VARIABLE=lambda url: 0
        ))
        self.assertEqual(t.via_imgproxy('http://naver.com/test.png'),
                'http://imgproxy.com/0/http://naver.com/test.png')

    def tearDown(self):
        t.app = self.original_app
