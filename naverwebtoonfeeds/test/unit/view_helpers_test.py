import unittest

from naverwebtoonfeeds.test.utilities import mock_obj, Mock
import naverwebtoonfeeds.view_helpers as v


# pylint: disable=C0103,R0904
class ViewHelpersTest(unittest.TestCase):

    def setUp(self):
        self.originals = {}
        for name in dir(v):
            self.originals[name] = getattr(v, name)

    def tearDown(self):
        for name in self.originals:
            setattr(v, name, self.originals[name])

    def test_urlpath_minimum(self):
        self.assertEqual(v.urlpath('http://a.co'), '')

    def test_urlpath_root(self):
        self.assertEqual(v.urlpath('http://foo.bar.com/'), '/')

    def test_urlpath_path(self):
        self.assertEqual(v.urlpath('http://bit.ly/bEf232'), '/bEf232')

    def test_urlpath_full(self):
        self.assertEqual(v.urlpath('http://a.co/p;p1;p2;p3?a=1&b=2#frag'),
                '/p;p1;p2;p3?a=1&b=2#frag')

    def test_heroku_scale(self):
        v.app = mock_obj(config=dict(HEROKU_API_KEY='foobar123', HEROKU_APP_NAME='testapp'))
        v.heroku = Mock()
        v.heroku_scale('beaver', 5)
        v.heroku.from_key.assert_called_with('foobar123')
        v.heroku.from_key('foobar123')._http_resource.assert_called_with(
                method='POST',
                resource=('apps', 'testapp', 'ps', 'scale'),
                data=dict(type='beaver', qty=5)
        )

    def test_redirect_to_canonical_url_no_raw_uri_no_force_redirect(self):
        v.app = mock_obj(config=dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=False))
        v.request = mock_obj(environ=dict(), url='http://foo.com/baa/aar')
        view = mock_obj(__name__='view', __doc__=None)
        decorated_view = v.redirect_to_canonical_url(view)
        decorated_view(1, 'x', y=3)
        view.assert_called_with(1, 'x', y=3)

    def test_redirect_to_canonical_url_no_raw_uri_force_redirect(self):
        v.app = mock_obj(config=dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=True))
        v.request = mock_obj(environ=dict(), url='http://foo.com/baa/aar')
        v.redirect = Mock()
        view = mock_obj(__name__='view', __doc__=None)
        decorated_view = v.redirect_to_canonical_url(view)
        decorated_view(1, 'x', y=3)
        v.redirect.assert_called_with('http://bit.ly/baa/aar', 301)

    def test_redirect_to_canonical_url_raw_uri_force_redirect(self):
        v.app = mock_obj(config=dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=True))
        v.request = mock_obj(environ=dict(RAW_URI='/baa/aar'), url='http://foo.com/baa/aar')
        v.redirect = Mock()
        view = mock_obj(__name__='view', __doc__=None)
        decorated_view = v.redirect_to_canonical_url(view)
        decorated_view(1, 'x', y=3)
        v.redirect.assert_called_with('http://bit.ly/baa/aar', 301)
