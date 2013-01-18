import urlparse

from naverwebtoonfeeds import app
from naverwebtoonfeeds.lib.naver import naver_url


@app.template_filter()
def make_external(url):
    """
    Externalize the given internal URL path like /foo/bar to
    http://myserver.com/foo/bar so that it can be used in feeds.

    """
    return urlparse.urljoin(app.config['URL_ROOT'], url)


@app.template_filter()
def via_imgproxy(url):
    if not app.config.get('IMGPROXY_URL_PATTERN'):
        url_format = app.config.get('IMGPROXY_URL')
        return url_format.format(url=url) if url_format else url
    pattern = app.config['IMGPROXY_URL_PATTERN']
    variable = app.config['IMGPROXY_URL_VARIABLE'](url)
    return pattern.format(variable=variable, url=url)


@app.context_processor
def utility_processor():
    return dict(naver_url=naver_url)
