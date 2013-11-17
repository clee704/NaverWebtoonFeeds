import logging
import os
import signal

try:
    import heroku
except ImportError:
    pass
from flask import current_app
import rq

from ..extensions import cache, redis_connection, redis_queue
from .browser import AccessDenied
from .models import Series
from .update import update_series_list, update_series


__logger__ = logging.getLogger(__name__)


def enqueue_update_series_list():
    if cache.get('job_enqueued_list'):
        # Do nothing if already enqueued
        return
    cache.set('job_enqueued_list', True, timeout=300)
    try:
        _enqueue_job(_job_update_series_list)
    except:
        __logger__.exception('Failed to enqueue a job')
        cache.delete('job_enqueued_list')


def enqueue_update_series(series_id):
    key = 'job_enqueued_series_{0}'.format(series_id)
    if cache.get(key):
        # Do nothing if already enqueued
        return
    cache.set(key, True, timeout=300)
    try:
        _enqueue_job(_job_update_series, series_id)
    except:
        __logger__.exception('Failed to enqueue a job')
        cache.delete(key)


def _job_update_series_list():
    __logger__.debug('_job_update_series_list() called')
    try:
        update_series_list(background=True)
    except AccessDenied:
        # finally block is not executed when the process is killed by os.kill
        cache.delete('job_enqueued_list')
        # Stop the current worker as we can't do anything with the current IP.
        os.kill(os.getppid(), signal.SIGTERM)
    except:
        __logger__.exception('An error occurred while processing a job')
    finally:
        cache.delete('job_enqueued_list')


def _job_update_series(series_id):
    __logger__.debug('_job_update_series(series_id=%s) called', series_id)
    key = 'job_enqueued_series_{0}'.format(series_id)
    try:
        series = Series.query.get(series_id)
        update_series(series, background=True)
    except AccessDenied:
        # finally block is not executed when the process is killed by os.kill
        cache.delete(key)
        # Stop the current worker as we can't do anything with the current IP.
        os.kill(os.getppid(), signal.SIGTERM)
    except:
        __logger__.exception('An error occurred while processing a job')
    finally:
        cache.delete(key)


def _enqueue_job(func, *args):
    __logger__.debug('_enqueue_job(func=%s, args=%s) called', func, args)
    redis_queue.enqueue_call(func=func, args=args, result_ttl=0, timeout=900)
    if current_app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
        _heroku_run('worker')


def run_worker(burst=False):
    __logger__.debug('run_worker(burst=%s) called', burst)
    with rq.Connection(connection=redis_connection):
        w = rq.Worker([rq.Queue()])
        # Remove default exception handler that moves job to failed queue
        w.pop_exc_handler()
        w.work(burst=burst)
    __logger__.debug('run_worker(burst=%s) done', burst)


def _heroku_run(command):
    __logger__.debug('_heroku_run(command=%s) called', command)
    h = heroku.from_key(current_app.config['HEROKU_API_KEY'])
    try:
        app = h.apps[current_app.config['HEROKU_APP_NAME']]
        app.processes.add(command)
        __logger__.debug('%s is started', command)
    except:
        __logger__.exception('Could not run heroku process')
