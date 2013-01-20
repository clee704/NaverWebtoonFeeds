import logging

from flask import render_template, url_for

from naverwebtoonfeeds import app, cache
from naverwebtoonfeeds.view_helpers import redirect_to_canonical_url, enqueue_job
from naverwebtoonfeeds.view_helpers import render_and_cache_feed_index, render_and_cache_feed_show
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.updater import series_list_needs_fetching, update_series_list, update_series


__logger__ = logging.getLogger(__name__)


@app.route('/')
@redirect_to_canonical_url
def feed_index():
    __logger__.info('feed_index (GET %s)', url_for('feed_index'))
    invalidate_cache = False
    if series_list_needs_fetching():
        if app.config.get('USE_REDIS_QUEUE'):
            enqueue_job(update_series_list)
        else:
            list_updated, _ = update_series_list()
            invalidate_cache = list_updated
    if not invalidate_cache:
        response = cache.get('feed_index')
        if response:
            __logger__.info('Cache hit')
            return response
    return render_and_cache_feed_index()


@app.route('/feeds/<int:series_id>.xml')
@redirect_to_canonical_url
def feed_show(series_id):
    url = url_for('feed_show', series_id=series_id)
    __logger__.info('feed_show, series_id=%d (GET %s)', series_id, url)
    series = None
    invalidate_cache = False
    if series_list_needs_fetching():
        if app.config.get('USE_REDIS_QUEUE'):
            enqueue_job(update_series_list)
        else:
            # update_series_list with no argument only adds new series.
            # The current series never gets updated.
            list_updated, _ = update_series_list()
            if list_updated:
                cache.delete('feed_index')
    series = Series.query.get_or_404(series_id)
    if series.new_chapters_available:
        if app.config.get('USE_REDIS_QUEUE'):
            enqueue_job(update_series, args=(series,))
        else:
            invalidate_cache = any(update_series(series))
    if not invalidate_cache:
        response = cache.get('feed_show_%d' % series_id)
        if response:
            __logger__.info('Cache hit')
            return response
    return render_and_cache_feed_show(series)


@app.errorhandler(500)
def internal_server_error(_):
    return render_template('500.html'), 500


@app.errorhandler(404)
def not_found(_):
    return render_template('404.html'), 404
