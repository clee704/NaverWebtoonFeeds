from naverwebtoonfeeds.filters import externalize_filter, proxify_filter


def test_externalize(app):
    with app.test_client():
        assert externalize_filter('/a/b') == 'http://localhost:5000/a/b'


def test_externalize_with_usual_server_name(app):
    with app.test_client():
        app.config['SERVER_NAME'] = 'example.com'
        assert externalize_filter('/q?v=1') == 'http://example.com/q?v=1'


def test_externalize_with_https(app):
    with app.test_client():
        app.config['SERVER_NAME'] = 'example.com'
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        assert externalize_filter('/foo') == 'https://example.com/foo'


def test_proxify_with_no_proxy(app):
    with app.test_client():
        app.config.pop('IMGPROXY_URL')
        app.config.pop('IMGPROXY_URL_PATTERN')
        app.config.pop('IMGPROXY_URL_VARIABLE')
        assert (proxify_filter('http://naver.com/foo.jpg') ==
                'http://naver.com/foo.jpg')


def test_proxify_with_url(app):
    with app.test_client():
        app.config['IMGPROXY_URL'] = 'http://imgprx.com/{url}'
        app.config.pop('IMGPROXY_URL_PATTERN')
        app.config.pop('IMGPROXY_URL_VARIABLE')
        assert (proxify_filter('http://naver.com/foo.jpg') ==
                'http://imgprx.com/http://naver.com/foo.jpg')


def test_proxify_with_pattern(app):
    with app.test_client():
        app.config['IMGPROXY_URL_PATTERN'] = 'http://imgprx.com/{v}/{url}'
        app.config['IMGPROXY_URL_VARIABLE'] = lambda url: 0
        assert (proxify_filter('http://naver.com/foo.jpg') ==
                'http://imgprx.com/0/http://naver.com/foo.jpg')
