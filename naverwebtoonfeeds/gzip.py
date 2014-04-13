"""
    naverwebtoonfeeds.gzip
    ~~~~~~~~~~~~~~~~~~~~~~

    Implements a customized version of :class:`flask_gzip.Gzip`.

"""
from flask_gzip import Gzip as GzipBase


class Gzip(GzipBase):

    def __init__(self, app=None):
        self._initialized = False
        if app is not None:
            super(Gzip, self).__init__(app)
            self._initialized = True

    def init_app(self, app):
        if not self._initialized:
            super(Gzip, self).__init__(app)
            self._initialized = True
        else:
            raise RuntimeError('already initialized')

    def after_request(self, response):
        # Fix https://github.com/elasticsales/Flask-gzip/issues/7
        response.direct_passthrough = False
        return Gzip.after_request(self, response)
