from flask import Response, render_template
from sqlalchemy.orm import joinedload
import pytz

from naverwebtoonfeeds import app, cache, tz
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.updater import update_series_list, update_series


@app.route('/')
@cache.cached(timeout=86400)
def feed_index():
    app.logger.info('GET /')
    update_series_list(append_only=True)
    series_list = Series.query.filter_by(is_completed=False).order_by(Series.title).all()
    response = render_template('feed_index.html', series_list=series_list)
    return response


@app.route('/feeds/<int:series_id>.xml')
@cache.cached(timeout=3600)
def feed_show(series_id):
    app.logger.info('GET /feeds/%d.xml', series_id)
    series = Series.query.options(joinedload('chapters')).get_or_404(series_id)
    update_series(series)
    chapters = []
    for c in series.chapters:
        # _pubdate_tz is used in templates to correct time zone
        c._pubdate_tz = pytz.utc.localize(c.pubdate).astimezone(tz)
        chapters.append(c)
    xml = render_template('feed_show.xml', series=series, chapters=chapters)
    response = Response(response=xml, content_type='application/atom+xml')
    return response


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
