import logging
import os
import signal

try:
    import heroku
except ImportError:
    pass
from flask import current_app
import rq

from ..extensions import cache, db, redis_connection, redis_queue
from .browser import AccessDenied
from .models import Series, Config
from .update import update_series_list, update_series


__logger__ = logging.getLogger(__name__)


def enqueue_update_series_list():
    _enqueue_job(_update_func_wrapper, ('list',))


def enqueue_update_series(series_id):
    _enqueue_job(_update_func_wrapper, ('series', series_id))


def _enqueue_job(func, args=None):
    __logger__.debug('_enqueue_job(func=%s, args=%s) invoked', func, args)
    redis_queue.enqueue_call(func=func, args=args, result_ttl=0, timeout=3600)
    if current_app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
        _heroku_scale('worker', 1)


def _update_func_wrapper(target, *args):
    try:
        if target == 'list':
            update_series_list(background=True)
        elif target == 'series':
            series_id = args[0]
            series = Series.query.get(series_id)
            update_series(series, background=True)
        else:
            __logger__.warning('Unknown target: %s', target)
    except AccessDenied:
        # Stop the current worker to get a new IP address
        os.kill(os.getppid(), signal.SIGTERM)


def run_worker(burst=False):
    __logger__.debug('run_worker(burst=%s) invoked', burst)
    try:
        with rq.Connection(connection=redis_connection):
            w = rq.Worker([rq.Queue()])
            # Remove default exception handler that moves job to failed queue
            w.pop_exc_handler()
            w.work(burst=burst)
    finally:
        if burst and current_app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
            _heroku_scale('worker', 0)


def _heroku_scale(process_name, qty):
    __logger__.debug('_heroku_scale(process_name=%s, qty=%s) invoked', process_name, qty)

    # Check if the scale command has already been issued recently.
    key = 'heroku:processes:{0}'.format(process_name)
    old_qty = cache.get(key)
    if old_qty == qty:
        __logger__.debug('%s is already scaled to %d processes', process_name, qty)
        return

    cloud = heroku.from_key(current_app.config['HEROKU_API_KEY'])
    try:
        app = cloud.apps[current_app.config['HEROKU_APP_NAME']]
        try:
            app.processes[process_name].scale(qty)
        except KeyError:
            # No existing processes
            app.processes.add((process_name, qty))
        __logger__.debug('%s is scaled to %d processes', process_name, qty)
        # Save the changed quantity for 5 minutes to make it possible
        # to re-issue the command after 5 minutes.
        # It is necessary since we don't know whether processes are actually
        # scaled to the specified quantity.
        cache.set(key, qty, timeout=300)
    except Exception as e:
        __logger__.exception('Could not scale heroku')
