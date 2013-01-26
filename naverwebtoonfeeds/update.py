from datetime import datetime, timedelta
import logging

from sqlalchemy.exc import IntegrityError

from naverwebtoonfeeds.objects import app, db
from naverwebtoonfeeds.browser import Browser
from naverwebtoonfeeds.misc import as_naver_time_zone
from naverwebtoonfeeds.models import Series, Chapter, Config
from naverwebtoonfeeds.render import render_feed_index, render_feed_show


__browser__ = Browser(app)
__logger__ = logging.getLogger(__name__)


def series_list_needs_fetching():
    now = datetime.utcnow()
    interval = _series_stats_update_interval()
    fetched = Config.query.get('series_list_fetched')
    return fetched is None or fetched.value + interval < now


def update_series_list(update_all=False, background=False):
    # Check the time when series list was fetched once more if running in
    # the background.
    if background and not series_list_needs_fetching():
        return

    updated = [False, []]
    # updated[0]: index view cache should be purged
    # updated[1]: view cache of series with id in this list should be purged

    series_list = _fetch_series_list(update_all, updated)
    if series_list is None:
        return updated

    # Upload badges are cleared at the midnight and generated when the
    # series has been uploaded today.
    #
    # If offset is too long, say 3 hours, and a series is uploaded at 10pm,
    # and there was no request to the app until right after the midnight,
    # then we'll miss the upload badge for the series.
    #
    # If offset is too short, say 1 minute, then all series will be marked
    # as 'new chapters available' however frequent requests are, since
    # the minimum interval to fetch series list is 15 minutes or so. It will
    # increase the rate of requests to Naver and slow the page loading
    # (1 per series per day).
    #
    # If the requests to the app is frequent enough, setting it to just
    # above the minimum fetch interval will be fine.
    fetched = Config.query.get('series_list_fetched')
    now = datetime.utcnow()
    last_midnight = as_naver_time_zone(now).replace(hour=0, minute=0, second=0, microsecond=0)
    offset = timedelta(minutes=30)
    if fetched is None or as_naver_time_zone(fetched.value) < last_midnight - offset:
        # The last time the series list is fetched is too far in the past.
        # It can happen if the app is not very popular.  Mark all series as
        # 'new chapters available' since we might have missed the upload
        # badges for some series.
        for series in series_list:
            if not series.is_completed:
                series.new_chapters_available = True

    # Update the time when series list was fetched.
    if fetched is None:
        db.session.add(Config(key='series_list_fetched', value=now))
    else:
        fetched.value = now

    _commit()

    if background:
        for series in Series.query.filter_by(new_chapters_available=True):
            series_updated, chapters_added = update_series(series)
            updated[0] |= series_updated
            if chapters_added:
                updated[1].append(series.id)
            if series_updated or chapters_added:
                render_feed_show(series)
        if updated[0]:
            render_feed_index()

    return updated


def update_series(series, add_new_chapters=True, do_commit=True, background=False):
    series_updated = _fetch_series_data(series)
    chapters_added = False
    if series_updated is None:
        return [series_updated, chapters_added]
    db.session.add(series)
    if add_new_chapters and series.new_chapters_available:
        chapters_added = _add_new_chapters(series)
        if chapters_added:
            series.new_chapters_available = False
            series.retries_left = 0
        else:
            __logger__.warning('New chapters for series #%d were not found', series.id)
            if series.retries_left == 0:
                series.new_chapters_available = False
            else:
                series.retries_left -= 1
        # updated indicates the view cache should be purged.
        # new_chapters_available doesn't affect the view, so it doesn't set
        # updated to True.
    if do_commit:
        _commit()
    if background and (series_updated or chapters_added):
        render_feed_show(series)
    return [series_updated, chapters_added]


def add_completed_series():
    try:
        completed_series = __browser__.get_completed_series()
    except:
        return
    completed_series_ids = set(data['id'] for data in completed_series)
    existing_series_ids = set(row[0] for row in db.session.query(Series.id))
    for series_id in completed_series_ids - existing_series_ids:
        series = Series(id=series_id)
        series.new_chapters_available = True
        update_series(series)


def _series_stats_update_interval():
    # The longer this interval, the fewer HTTP requests will be made to Naver.
    # 30 min to 1 hour would be a good choice.
    # Should be shorter than 1 day.
    hour = as_naver_time_zone(datetime.utcnow()).hour
    if 23 <= hour or hour < 1:
        return timedelta(minutes=10)
    elif 1 <= hour < 3:
        return timedelta(minutes=30)
    else:
        return timedelta(hours=1)


def _fetch_series_list(update_all, updated):
    fetched_data = {}
    try:
        issues = __browser__.get_issues()
    except:
        return
    for data in issues:
        info = fetched_data.setdefault(data['id'], {})
        info.setdefault('upload_days', []).append(data['day'])
        days_uploaded = info.setdefault('days_uploaded', [])
        if data['days_uploaded']:
            days_uploaded.append(data['days_uploaded'])
    series_list = _update_existing_series(fetched_data, update_all, updated)
    existing_series_ids = set(series.id for series in series_list)
    new_series_ids = fetched_data.viewkeys() - existing_series_ids
    _add_new_series(new_series_ids, fetched_data, update_all, updated)
    return series_list


def _update_existing_series(fetched_data, update_all, updated):
    series_list = Series.query.all()
    for series in series_list:
        info = fetched_data.get(series.id)
        if info is None:
            # The series is not on the list.
            if not series.is_completed:
                # The series is now completed.
                series.is_completed = True
                updated[0] = True
            continue
        else:
            if series.is_completed:
                # The series is on the list and it was marked as completed.
                series.is_completed = False
                updated[0] = True
        upload_days = ','.join(info['upload_days'])
        if series.upload_days != upload_days:
            series.upload_days = upload_days
            updated[0] = True
        # updated[0] is not changed below because new_chapters_available and
        # last_update_stattus don't affect the view.
        if any(day not in series.last_upload_status for day in info['days_uploaded']):
            series.new_chapters_available = True
            series.retries_left = 2
        series.last_upload_status = ','.join(info['days_uploaded'])
        if update_all:
            series_updated, chapters_added = update_series(series, update_all, False)
            updated[0] |= series_updated
            if chapters_added:
                updated[1].append(series.id)
    return series_list


def _add_new_series(new_series_ids, fetched_data, update_all, updated):
    if not new_series_ids:
        return
    updated[0] = True
    for series_id in new_series_ids:
        series = Series(id=series_id)
        series_updated, chapters_added = update_series(series, update_all, False)
        if not series_updated:
            # It failed to fetch data for the series.
            # It may happen when it failed to login to Naver and the series
            # requires login to view.
            continue
        if chapters_added:
            updated[1].append(series.id)
        info = fetched_data[series.id]
        upload_days = ','.join(info['upload_days'])
        if series.upload_days != upload_days:
            series.upload_days = upload_days
        series.new_chapters_available = True
        series.last_upload_status = ','.join(info['days_uploaded'])


def _fetch_series_data(series):
    try:
        data = __browser__.get_series_data(series.id)
    except:
        return
    if data.get('removed'):
        if not series.is_completed:
            __logger__.warning('Series #%d seems removed', series.id)
            series.is_completed = True
            return True
        return False
    attributes = ['title', 'author', 'description', 'last_chapter', 'is_completed', 'thumbnail_url']
    return _update_attributes(series, data, attributes)


def _add_new_chapters(series):
    updated = False
    current_last_chapter = series.chapters[0].id if len(series.chapters) else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    for chapter_id in chapter_ids:
        chapter = Chapter(series=series, id=chapter_id)
        # chapter is in a pending state, probably because of the series
        # attribute. But I couldn't find this in the documentation.
        if _fetch_chapter_data(chapter):
            chapter.atom_id = _make_atom_id(chapter)
            # Not necessary; it doesn't hurt to do so.
            db.session.add(chapter)
            updated = True
        else:
            db.session.expunge(chapter)
    return updated


def _make_atom_id(chapter):
    date = datetime.utcnow().strftime('%Y-%m-%d')
    tagging_entity = app.config['AUTHORITY_NAME'] + ',' + date
    specific_list = ['generator=naverwebtoonfeeds']
    specific_list.append('series={0}'.format(chapter.series.id))
    specific_list.append('chapter={0}'.format(chapter.id))
    return 'tag:' + tagging_entity + ':' + ';'.join(specific_list)


def _fetch_chapter_data(chapter):
    try:
        data = __browser__.get_chapter_data(chapter.series.id, chapter.id)
    except:
        return
    if data.get('not_found'):
        return False
    return _update_attributes(chapter, data, ['title', 'pubdate', 'thumbnail_url'])


def _update_attributes(obj, data, attribute_names):
    updated = False
    for attribute_name in attribute_names:
        if getattr(obj, attribute_name) != data[attribute_name]:
            updated = True
            setattr(obj, attribute_name, data[attribute_name])
    return updated


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        __logger__.error('IntegrityError', exc_info=True)
        db.session.rollback()
