from flask import Response, render_template, request, redirect, url_for
from sqlalchemy.orm import joinedload
import pytz

from naverwebtoonfeeds import app, cache, CACHE_PERMANENT
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.naver import NAVER_TIMEZONE
from naverwebtoonfeeds.lib.updater import update_series_list, update_series


def redirect_to_canonical_url(view):
    def new_view(*args, **kwargs):
        path = request.environ['RAW_URI']
        canonical_url = app.config['URL_ROOT'] + path
        if app.config.get('FORCE_REDIRECT') and request.url != canonical_url:
            return redirect(canonical_url, 301)
        else:
            return view(*args, **kwargs)
    new_view.__name__ = view.__name__
    new_view.__doc__ = view.__doc__
    return new_view


@app.route('/')
@redirect_to_canonical_url
def feed_index():
    app.logger.info('feed_index (GET %s)', url_for('feed_index'))
    updated = update_series_list()
    cache_key = 'feed_index'
    if not updated:
        response = cache.get(cache_key)
        if response:
            app.logger.info('Cache hit')
            return response
    current_series_query = Series.query.filter_by(is_completed=False)
    sorted_series_list = current_series_query.order_by(Series.title).all()
    response = render_template('feed_index.html', series_list=sorted_series_list)
    cache.set(cache_key, response, CACHE_PERMANENT)
    return response


@app.route('/feeds/<int:series_id>.xml')
@redirect_to_canonical_url
def feed_show(series_id):
    url = url_for('feed_show', series_id=series_id)
    app.logger.info('feed_show, series_id=%d (GET %s)', series_id, url)
    update_series_list()
    series = Series.query.get_or_404(series_id)
    updated = False
    if series.new_chapters_available:
        updated |= update_series(series)
    cache_key = 'feed_show_%d' % series_id
    if not updated:
        response = cache.get(cache_key)
        if response:
            app.logger.info('Cache hit')
            return response
    chapters = []
    for chapter in series.chapters:
        # pubdate_with_tz is used in templates to correct time zone
        pubdate_with_tz = pytz.utc.localize(chapter.pubdate).astimezone(NAVER_TIMEZONE)
        chapter.pubdate_with_tz = pubdate_with_tz
        chapters.append(chapter)
    xml = render_template('feed_show.xml', series=series, chapters=chapters)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set(cache_key, response, CACHE_PERMANENT)
    return response


@app.errorhandler(500)
def internal_server_error(_):
    return render_template('500.html'), 500
