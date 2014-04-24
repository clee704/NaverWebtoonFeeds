from flask import g

from naverwebtoonfeeds.ext import get_queue
from naverwebtoonfeeds.feeds.worker import run_worker


def test_run_worker(app, db):
    with app.test_client() as client:
        client.get('/')
        assert get_queue().count == 1
        run_worker(burst=True)
        assert get_queue().count == 0
