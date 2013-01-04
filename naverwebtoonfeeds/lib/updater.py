from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
import pytz

from naverwebtoonfeeds import app, cache, db, tz
from naverwebtoonfeeds.models import Series, Chapter
from naverwebtoonfeeds.lib.naver import NaverBrowser


# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10


browser = NaverBrowser(app)


def update_series_list(update_all=False):
    fetched = cache.get('series_list_fetched')
    if (update_all or fetched is None or
            fetched + _series_stats_update_interval() < datetime.utcnow()):
        _fetch_series_list(update_all)
        cache.set('series_list_fetched', datetime.utcnow(), CACHE_PERMANENT)


def _series_stats_update_interval():
    # The longer this interval, the fewer HTTP requests will be made to Naver.
    # 30 min to 1 hour would be a good choice.
    # Should be shorter than 1 day.
    naver_time = pytz.utc.localize(datetime.utcnow()).astimezone(tz)
    hour = naver_time.hour
    if 23 <= hour or hour < 1:
        return timedelta(minutes=15)
    elif 1 <= hour < 3:
        return timedelta(minutes=30)
    else:
        return timedelta(hours=1)


def _fetch_series_list(update_all):
    fetched_data = {}
    try:
        issues = browser.get_issues()
    except:
        app.logger.error("An error occurred while getting series list",
            exc_info=True)
        return
    for data in issues:
        info = fetched_data.setdefault(data['id'], {})
        info.setdefault('update_days', []).append(data['day'])
        days_updated = info.setdefault('days_updated', [])
        if data['days_updated']:
            days_updated.append(data['days_updated'])
    series_list = Series.query.all()
    series_ids = set()
    for series in series_list:
        series_ids.add(series.id)
        if update_all:
            update_series(series, add_new_chapters=update_all, do_commit=False)
        info = fetched_data.get(series.id)
        if info is None:
            # The series is completed or somehow not showing up in the index
            continue
        series.update_days = ','.join(info['update_days'])
        if any(day not in series.last_update_status for day in info['days_updated']):
            series.new_chapters_available = True
        series.last_update_status = ','.join(info['days_updated'])
    for series_id in fetched_data.viewkeys() - series_ids:
        series = Series(id=series_id)
        update_series(series, add_new_chapters=update_all, do_commit=False)
    _commit()


def update_series(series, add_new_chapters=True, do_commit=True):
    _fetch_series_data(series)
    db.session.add(series)
    if add_new_chapters and series.new_chapters_available:
        _add_new_chapters(series)
        series.new_chapters_available = False
    if do_commit:
        _commit()


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        app.logger.error('IntegrityError', exc_info=True)
        db.session.rollback()


def _fetch_series_data(series):
    try:
        data = browser.get_series_data(series.id)
    except:
        app.logger.error("An error occurred while getting data for series #%d",
            series.id, exc_info=True)
        return
    if data.get('removed'):
        if not series.is_completed:
            app.logger.warning('Series #%d seems removed', series.id)
            series.is_completed = True
    else:
        series.title = data['title']
        series.author = data['author']
        series.description = data['description']
        series.last_chapter = data['last_chapter']
        series.is_completed = data['is_completed']
        series.thumbnail_url = data['thumbnail_url']


def _fetch_chapter_data(chapter):
    try:
        data = browser.get_chapter_data(chapter.series.id, chapter.id, tz)
    except:
        app.logger.error(
            "An error occurred while getting data for chapter #%d of series #%d",
            chapter.id, chapter.series.id, exc_info=True)
        return False
    if data.get('not_found'):
        raise Chapter.DoesNotExist
    chapter.title = data['title']
    chapter.pubdate = data['pubdate']
    chapter.thumbnail_url = data['thumbnail_url']
    return True


def _add_new_chapters(series):
    current_last_chapter = series.chapters[0].id if len(series.chapters) else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    for chapter_id in chapter_ids:
        chapter = Chapter(series=series, id=chapter_id)
        try:
            success = _fetch_chapter_data(chapter)
        except Chapter.DoesNotExist:
            continue
        if success:
            db.session.add(chapter)
