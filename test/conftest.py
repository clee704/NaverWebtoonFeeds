import io
import os
from tempfile import mkstemp

import lxml.etree
import lxml.html
import yaml
from flask import Response as ResponseBase
from lxml.html import HtmlElementClassLookup, HTMLParser, submit_form
from mock import Mock
from pytest import fixture

from naverwebtoonfeeds.app import create_app
from naverwebtoonfeeds.ext import db as flask_db

from ._compat import (addinfourl, build_opener, http_client, HTTPHandler,
                      install_opener)


tempfile_path = mkstemp()[1]
test_settings = dict(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + tempfile_path,
    CACHE_TYPE='simple',
)


@fixture
def app(request):
    ctx = None

    def fin():
        if ctx is not None:
            ctx.pop()
    request.addfinalizer(fin)

    app = create_app(test_settings)
    app.testing = True
    app.response_class = Response
    ctx = app.app_context()
    ctx.push()
    return app


@fixture
def db(app, request):
    def fin():
        flask_db.session.close()
        flask_db.drop_all()
        flask_db.get_engine(app).dispose()
    request.addfinalizer(fin)

    flask_db.drop_all()
    flask_db.create_all()
    return flask_db


@fixture(scope='session', autouse=True)
def setup(request):
    def teardown():
        os.unlink(tempfile_path)
        MockHTTPHandler.mock_urls.clear()
    request.addfinalizer(teardown)


class Response(ResponseBase):
    html_mimetypes = frozenset(['text/html', 'application/xhtml+xml'])
    xml_mimetypes = frozenset(['application/atom+xml'])

    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)
        print(self.mimetype)
        if self.mimetype in self.html_mimetypes:
            self.doc = lxml.html.fromstring(self.data)
        elif self.mimetype in self.xml_mimetypes:
            self.doc = lxml.etree.fromstring(self.data)


class MockHTTPHandler(HTTPHandler):

    mock_urls = {}

    def http_open(self, req):
        url = req.get_full_url()
        try:
            status_code, mimetype, content = self.mock_urls[url]
        except KeyError:
            return HTTPHandler.http_open(self, req)
        resp = addinfourl(io.BytesIO(content), {'content-type': mimetype},
                          url)
        resp.code = status_code
        resp.msg = http_client.responses[status_code]
        return resp

mock_opener = build_opener(MockHTTPHandler)
install_opener(mock_opener)


def mock_obj(**kwargs):
    mock = Mock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock


def read_fixture(filename):
    path = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
    with open(path, 'rb') as f:
        text = f.read()
        if filename.endswith('yaml'):
            return yaml.load(text)
        else:
            return text
