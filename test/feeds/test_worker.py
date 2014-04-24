from flask import g

from naverwebtoonfeeds.feeds.worker import run_worker


def test_run_worker(app, db):
    with app.test_client() as client:
        client.get('/')
        assert g.queue.count == 1
        run_worker(burst=True)
        assert g.queue.count == 0
