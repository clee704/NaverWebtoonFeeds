"""
    naverwebtoonfeeds.filters
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Template filters for Jinja2.

"""
import inspect
import sys

from flask import current_app

from ._compat import urlunparse


def externalize_filter(path):
    """Externalizes the given internal URL path like /foo/bar to
    http://example.com/foo/bar so that it can be used in feeds.

    """
    scheme = current_app.config['PREFERRED_URL_SCHEME']
    netloc = current_app.config['SERVER_NAME']
    return urlunparse([scheme, netloc, path, '', '', ''])


def proxify_filter(url):
    """Proxifies the given image URL to prevent resource blocking based on the
    Referer header.

    """
    if not current_app.config.get('IMGPROXY_URL_PATTERN'):
        url_format = current_app.config.get('IMGPROXY_URL')
        return url_format.format(url=url) if url_format else url
    pattern = current_app.config['IMGPROXY_URL_PATTERN']
    variable = current_app.config['IMGPROXY_URL_VARIABLE'](url)
    return pattern.format(v=variable, url=url)


def register_filters(app, module_name=__name__):
    """Registers filters in the given module. Any function whose name ends
    with ``_filter`` will be considered as a filter. The registered filter name
    will be without the ``_filter`` suffix.

    """
    current_module = sys.modules[module_name]
    for name, obj in inspect.getmembers(current_module):
        if name.endswith('_filter') and hasattr(obj, '__call__'):
            shortname = name[:-len('_filter')]
            app.jinja_env.filters[shortname] = obj
