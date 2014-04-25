import rq
from flask import g
from mock import Mock, patch

from naverwebtoonfeeds.ext import get_queue
from naverwebtoonfeeds.feeds.worker import run_worker

class Worker(rq.Worker):
    def fork_and_perform_job(self, job):
        self.perform_job(job)

@patch('naverwebtoonfeeds.feeds.worker.Crawler')
def test_run_worker(Crawler, app, db):
    mock_crawler = Mock()
    Crawler.return_value = mock_crawler
    with app.test_client() as client:
        client.get('/')
        assert get_queue().count == 1
        run_worker(burst=True, worker_class=Worker)
        assert get_queue().count == 0
        mock_crawler.update_series_list.assert_called_with()
