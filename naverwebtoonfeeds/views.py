from flask import render_template, url_for

from naverwebtoonfeeds import app, cache, queue
from naverwebtoonfeeds.view_helpers import redirect_to_canonical_url, render_and_cache_feed_index, render_and_cache_feed_show
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.updater import update_series_list, update_series


@app.route('/')
@redirect_to_canonical_url
def feed_index():
    app.logger.info('feed_index (GET %s)', url_for('feed_index'))
    if app.config.get('USE_REDIS_QUEUE'):
        queue.enqueue_call(func=update_series_list, kwargs={'background': True}, result_ttl=0, timeout=3600)
        invalidate_cache = False
    else:
        list_updated, _ = update_series_list()
        invalidate_cache = list_updated
    if not invalidate_cache:
        response = cache.get('feed_index')
        if response:
            app.logger.info('Cache hit')
            return response
    return render_and_cache_feed_index()


@app.route('/feeds/<int:series_id>.xml')
@redirect_to_canonical_url
def feed_show(series_id):
    url = url_for('feed_show', series_id=series_id)
    app.logger.info('feed_show, series_id=%d (GET %s)', series_id, url)
    series = None
    if app.config.get('USE_REDIS_QUEUE'):
        queue.enqueue_call(func=update_series_list, kwargs={'background': True}, result_ttl=0, timeout=3600)
        invalidate_cache = False
    else:
        # update_series_list with no argument only adds new series.
        # The current series never gets updated.
        list_updated, _ = update_series_list()
        if list_updated:
            cache.delete('feed_index')
        series = Series.query.get_or_404(series_id)
        updated = False
        if series.new_chapters_available:
            updated = any(update_series(series))
        invalidate_cache = updated
    if not invalidate_cache:
        response = cache.get('feed_show_%d' % series_id)
        if response:
            app.logger.info('Cache hit')
            return response
    if series is None:
        series = Series.query.get_or_404(series_id)
    return render_and_cache_feed_show(series)


@app.errorhandler(500)
def internal_server_error(_):
    return render_template('500.html'), 500


@app.errorhandler(404)
def not_found(_):
    return render_template('404.html'), 404
