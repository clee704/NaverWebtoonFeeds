from flask import Response, render_template, request, redirect
import pytz

from naverwebtoonfeeds import app, cache, CACHE_PERMANENT
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.naver import NAVER_TIMEZONE


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


def render_and_cache_feed_index():
    series_list = Series.query.order_by(Series.title).all()
    response = render_template('feed_index.html', series_list=series_list)
    cache.set('feed_index', response, CACHE_PERMANENT)
    return response


def render_and_cache_feed_show(series):
    chapters = []
    for chapter in series.chapters:
        # pubdate_with_tz is used in templates to correct time zone
        pubdate_with_tz = pytz.utc.localize(chapter.pubdate).astimezone(NAVER_TIMEZONE)
        chapter.pubdate_with_tz = pubdate_with_tz
        chapters.append(chapter)
    xml = render_template('feed_show.xml', series=series, chapters=chapters)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set('feed_show_%d' % series.id, response, CACHE_PERMANENT)
    return response