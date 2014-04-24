import functools
import logging
import os
import signal

from flask import current_app, g

from ..ext import cache, db
from .crawler import AccessDenied, Crawler, series_list_needs_update
from .models import Series
from .signals import feed_requested, index_requested
from .views import feeds


logger = logging.getLogger(__name__)


def run_worker(burst=False):
    logger.debug('run_worker(burst=%r) called', burst)
    try:
        import rq
    except ImportError:
        raise RuntimeError('rq module is not installed')
    w = rq.Worker([rq.Queue()])
    # Remove default exception handler that moves job to failed queue
    w.pop_exc_handler()
    w.work(burst=burst)
    logger.debug('run_worker(burst=%r) done', burst)


@index_requested.connect_via(feeds)
def on_index_requested(sender, **extra):
    logger.debug('on_index_requested')
    if not current_app.config.get('USE_REDIS_QUEUE'):
        return
    if series_list_needs_update():
        enqueue_update_series_list()


@feed_requested.connect_via(feeds)
def on_feed_requested(sender, **extra):
    logger.debug('on_feed_requested')
    if not current_app.config.get('USE_REDIS_QUEUE'):
        return
    if series_list_needs_update():
        enqueue_update_series_list()
    series_id = extra['series_id']
    new_chapters_available = db.session.query(Series.new_chapters_available) \
                                       .filter_by(id=series_id).scalar()
    if new_chapters_available:
        enqueue_update_series(series_id)


def update_series_list_job():
    crawler = Crawler()
    crawler.update_series_list()


def update_series_job(series_id):
    crawler = Crawler()
    series = Series.query.get(series_id)
    if series:
        crawler.update_series(series)


def enqueue_update_series_list():
    enqueue_job(update_series_list_job, 'feeds:jobs:list')


def enqueue_update_series(series_id):
    enqueue_job(update_series_job, 'feeds:jobs:series:{}'.format(series_id),
                series_id)


def enqueue_job(job_func, cache_key, *args):
    if cache.get(cache_key):
        return
    cache.set(cache_key, True, timeout=300)
    try:
        func = get_rq_func(job_func, cache_key)
        g.queue.enqueue_call(func=func, args=args, result_ttl=0, timeout=900)
        logger.debug('Job enqueued (job_func=%r, args=%r)', job_func, args)
        if current_app.config.get('START_HEROKU_WORKER_ON_REQUEST'):
            start_heroku_process('worker')
    except Exception:
        logger.exception('Failed to enqueue the job')
        cache.delete(cache_key)


def get_rq_func(job_func, cache_key):
    @functools.wraps(job_func)
    def wrapper(*args, **kwargs):
        try:
            return job_func(*args, **kwargs)
        except AccessDenied:
            # Cache should be deleted here as finally block is not executed
            # when the process is killed by os.kill.
            cache.delete(cache_key)
            # Stop the current worker as we can't do anything with the current
            # IP address. This can happen if we are on AWS (e.g. Heroku). You
            # should start another worker process with a different public IP
            # address.
            logger.warning('Stopping the worker')
            os.kill(os.getppid(), signal.SIGTERM)
        except Exception:
            logger.exception('Failed to process the job')
        finally:
            cache.delete(cache_key)
    return wrapper


def start_heroku_process(command):
    try:
        import heroku
    except ImportError:
        logger.error('heroku module is required to start a Heroku process')
    else:
        h = heroku.from_key(current_app.config['HEROKU_API_KEY'])
        try:
            app = h.apps[current_app.config['HEROKU_APP_NAME']]
            app.processes.add(command)
            logger.debug("Heroku process '%s' is started", command)
        except Exception:
            logger.exception('Failed to start the Heroku process')
