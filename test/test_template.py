from test import TestCase
from .util import patch
import naverwebtoonfeeds.template as template


class TestUtil(TestCase):

    @patch('naverwebtoonfeeds.template.current_app')
    def test_externalize(self, mock_current_app):
        mock_current_app.config = dict(URL_ROOT='https://example.com')
        self.assertEqual(template.externalize('/foo/bar'), 'https://example.com/foo/bar')

    @patch('naverwebtoonfeeds.template.current_app')
    def test_proxify_null(self, mock_current_app):
        mock_current_app.config = dict()
        self.assertEqual(template.proxify('http://naver.com/test.png'),
                'http://naver.com/test.png')

    @patch('naverwebtoonfeeds.template.current_app')
    def test_proxify_with_url(self, mock_current_app):
        mock_current_app.config = dict(IMGPROXY_URL='http://imgproxy.com/{url}')
        self.assertEqual(template.proxify('http://naver.com/test.png'),
                'http://imgproxy.com/http://naver.com/test.png')

    @patch('naverwebtoonfeeds.template.current_app')
    def test_proxify_with_pattern(self, mock_current_app):
        mock_current_app.config = dict(
            IMGPROXY_URL_PATTERN='http://imgproxy.com/{variable}/{url}',
            IMGPROXY_URL_VARIABLE=lambda url: 0
        )
        self.assertEqual(template.proxify('http://naver.com/test.png'),
                'http://imgproxy.com/0/http://naver.com/test.png')
