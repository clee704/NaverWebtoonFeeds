import os

from flask.ext.testing import TestCase as Base, Twill

from naverwebtoonfeeds import create_app
from naverwebtoonfeeds.config.test import Config as TestConfig
from naverwebtoonfeeds.extensions import db


class TestCase(Base):

    def create_app(self):
        """Create and return a testing flask app."""
        app = create_app(TestConfig)
        self.twill = Twill(app, port=3000)
        return app

    def setUp(self):
        """Reset all tables before testing."""
        db.create_all()
        self.init_data()

    def tearDown(self):
        """Clean db session and drop all tables."""
        db.session.remove()
        db.drop_all()

    def init_data(self):
        pass
