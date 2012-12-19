import urlparse

from naverwebtoonfeeds import app
from naverwebtoonfeeds.lib import naver


@app.template_filter()
def make_external(url):
    """
    Externalize the given internal URL path like /foo/bar to
    http://myserver.com/foo/bar so that it can be used in feeds.

    """
    return urlparse.urljoin(app.config['URL_ROOT'], url)


@app.template_filter()
def via_imgproxy(url):
    u = app.config.get('IMGPROXY_URL')
    return u.format(url=url) if u else url


@app.context_processor
def utility_processor():
    def naver_url(series_id, chapter_id=None, mobile=False):
        """Return appropriate webtoon URL for the given arguments."""
        key = 'mobile' if mobile else 'series' if chapter_id is None else 'chapter'
        return naver.URL[key].format(series_id=series_id, chapter_id=chapter_id)
    return locals()
