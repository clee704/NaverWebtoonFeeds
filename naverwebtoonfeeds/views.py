from flask import Response, render_template
from sqlalchemy.orm import joinedload
import pytz

from naverwebtoonfeeds import app, cache, tz
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.updater import add_new_series, update_series


@app.route('/')
def feed_index():
    app.logger.info('GET /')
    cache_key = 'feed_index'
    cache_lifetime = 86400   # 1 day
    response = cache.get(cache_key)
    if response:
        app.logger.debug('Cache hit')
        return response
    add_new_series()
    series_list = Series.query.filter_by(is_completed=False).order_by(Series.title).all()
    response = render_template('feed_index.html', series_list=series_list)
    cache.set(cache_key, response, cache_lifetime)
    app.logger.debug('Cache created, valid for %s seconds', cache_lifetime)
    return response


@app.route('/feeds/<int:series_id>.xml')
def feed_show(series_id):
    app.logger.info('GET /feeds/%d.xml', series_id)
    cache_key = 'feed_show_%d' % series_id
    cache_lifetime = 3600   # 1 hour
    response = cache.get(cache_key)
    if response:
        app.logger.debug('Cache hit')
        return response
    series = Series.query.options(joinedload('chapters')).get_or_404(series_id)
    update_series(series)
    chapters = []
    for c in series.chapters:
        # _pubdate_tz is used in templates to correct time zone
        c._pubdate_tz = pytz.utc.localize(c.pubdate).astimezone(tz)
        chapters.append(c)
    xml = render_template('feed_show.xml', series=series, chapters=chapters)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set(cache_key, response, cache_lifetime)
    app.logger.debug('Cache created, valid for %s seconds', cache_lifetime)
    return response


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
