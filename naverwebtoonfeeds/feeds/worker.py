import logging

try:
    import heroku
except ImportError:
    pass
from flask import current_app
import rq

from ..extensions import redis_connection, redis_queue
from .models import Series
from .update import update_series_list, update_series


__logger__ = logging.getLogger(__name__)


def enqueue_update_series_list():
    # TODO check duplicate
    _enqueue_job(_update_func_wrapper, ('list',))


def enqueue_update_series(series_id):
    # TODO check duplicate
    _enqueue_job(_update_func_wrapper, ('series', series_id))


def _enqueue_job(func, args=None):
    __logger__.debug('_enqueue_job(func=%s, args=%s) called', func, args)
    redis_queue.enqueue_call(func=func, args=args, result_ttl=0, timeout=3600)
    if current_app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
        _heroku_run('worker')


def _update_func_wrapper(target, *args):
    if target == 'list':
        update_series_list(background=True)
    elif target == 'series':
        series_id = args[0]
        series = Series.query.get(series_id)
        update_series(series, background=True)
    else:
        __logger__.warning('Unknown target: %s', target)
    # TODO retry on failure


def run_worker(burst=False):
    __logger__.debug('run_worker(burst=%s) called', burst)
    with rq.Connection(connection=redis_connection):
        w = rq.Worker([rq.Queue()])
        # Remove default exception handler that moves job to failed queue
        w.pop_exc_handler()
        w.work(burst=burst)


def _heroku_run(command):
    __logger__.debug('_heroku_run(command=%s) called', command)
    h = heroku.from_key(current_app.config['HEROKU_API_KEY'])
    try:
        app = h.apps[current_app.config['HEROKU_APP_NAME']]
        app.processes.add(command)
        __logger__.debug('%s is started', command)
    except:
        __logger__.exception('Could not run heroku process')
