from test import TestCase
from ..util import Mock, patch
import naverwebtoonfeeds.feeds.views as feeds_views


class TestViews(TestCase):

    @patch('naverwebtoonfeeds.feeds.views.current_app')
    @patch('naverwebtoonfeeds.feeds.views.request')
    def test_redirect_to_canonical_url_without_raw_uri_without_force_redirect(self, mock_request, mock_current_app):
        mock_current_app.config = dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=False)
        mock_request.environ = dict()
        mock_request.url = 'http://foo.com/baa/aar'
        view = Mock()
        view_wrapper = lambda *args, **kwargs: view(*args, **kwargs)
        decorated_view = feeds_views.redirect_to_canonical_url(view_wrapper)
        decorated_view(1, 'x', y=3)
        view.assert_called_with(1, 'x', y=3)

    @patch('naverwebtoonfeeds.feeds.views.current_app')
    @patch('naverwebtoonfeeds.feeds.views.request')
    @patch('naverwebtoonfeeds.feeds.views.redirect')
    def test_redirect_to_canonical_url_without_raw_uri_with_force_redirect(self, mock_redirect, mock_request, mock_current_app):
        mock_current_app.config = dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=True)
        mock_request.environ = dict()
        mock_request.url = 'http://foo.com/baa/aar'
        view = Mock()
        view_wrapper = lambda *args, **kwargs: view(*args, **kwargs)
        decorated_view = feeds_views.redirect_to_canonical_url(view_wrapper)
        decorated_view(1, 'x', y=3)
        mock_redirect.assert_called_with('http://bit.ly/baa/aar', 301)

    @patch('naverwebtoonfeeds.feeds.views.current_app')
    @patch('naverwebtoonfeeds.feeds.views.request')
    @patch('naverwebtoonfeeds.feeds.views.redirect')
    def test_redirect_to_canonical_url_with_raw_uri_with_force_redirect(self, mock_redirect, mock_request, mock_current_app):
        mock_current_app.config = dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=True)
        mock_request.environ = dict(RAW_URI='/baa/aar')
        mock_request.url = 'http://foo.com/baa/aar'
        view = Mock()
        view_wrapper = lambda *args, **kwargs: view(*args, **kwargs)
        decorated_view = feeds_views.redirect_to_canonical_url(view_wrapper)
        decorated_view(1, 'x', y=3)
        mock_redirect.assert_called_with('http://bit.ly/baa/aar', 301)

    def test_urlpath_minimum(self):
        self.assertEqual(feeds_views.urlpath('http://a.co'), '')

    def test_urlpath_root(self):
        self.assertEqual(feeds_views.urlpath('http://foo.bar.com/'), '/')

    def test_urlpath_path(self):
        self.assertEqual(feeds_views.urlpath('http://bit.ly/bEf232'), '/bEf232')

    def test_urlpath_full(self):
        self.assertEqual(feeds_views.urlpath('http://a.co/p;p1;p2;p3?a=1&b=2#frag'),
                '/p;p1;p2;p3?a=1&b=2#frag')
