import urlparse

from flask import current_app


def externalize(url):
    """
    Externalizes the given internal URL path like /foo/bar to
    http://example.com/foo/bar so that it can be used in feeds.

    """
    return urlparse.urljoin(current_app.config['URL_ROOT'], url)


def proxify(url):
    """
    Proxifies the given image URL to prevent resource blocking based on
    the Referer header.

    """
    if not current_app.config.get('IMGPROXY_URL_PATTERN'):
        url_format = current_app.config.get('IMGPROXY_URL')
        return url_format.format(url=url) if url_format else url
    pattern = current_app.config['IMGPROXY_URL_PATTERN']
    variable = current_app.config['IMGPROXY_URL_VARIABLE'](url)
    return pattern.format(variable=variable, url=url)
