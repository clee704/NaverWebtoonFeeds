from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from naverwebtoonfeeds import app, db
from naverwebtoonfeeds.models import Series, Chapter, Config
from naverwebtoonfeeds.lib.naver import as_naver_time_zone, NaverBrowser


__browser__ = NaverBrowser(app)


def update_series_list(update_all=False):
    updated = [False, []]
    # updated[0]: index view cache should be purged
    # updated[1]: view cache of series with id in this list should be purged
    now = datetime.utcnow()
    interval = _series_stats_update_interval()
    fetched = Config.query.get('series_list_fetched')
    if (update_all or fetched is None or fetched.value + interval < now):
        # Update the fetched time ASAP to prevent duplicate requests
        last_fetched_date = None
        if fetched is None:
            fetched = Config(key='series_list_fetched', value=now)
            db.session.add(fetched)
        else:
            last_fetched_date = fetched.value
            fetched.value = now
        _fetch_series_list(update_all, last_fetched_date, updated)
        # We don't have to revert the value of series_list_fetched since
        # if the above call fails, it will not change since it's not commited.
    return updated


def update_series(series, add_new_chapters=True, do_commit=True):
    series_updated = _fetch_series_data(series)
    chapters_updated = False
    db.session.add(series)
    if add_new_chapters and series.new_chapters_available:
        chapters_updated = _add_new_chapters(series)
        series.new_chapters_available = False
        # updated indicates the view cache should be purged.
        # new_chapters_available doesn't affect the view, so it doesn't set
        # updated to True.
    if do_commit:
        _commit()
    return [series_updated, chapters_updated]


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


def _fetch_series_list(update_all, last_fetched_date, updated):
    fetched_data = {}
    try:
        issues = __browser__.get_issues()
    except:
        app.logger.error("An error occurred while getting series list", exc_info=True)
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
    now = datetime.utcnow()
    last_midnight = as_naver_time_zone(now).replace(hour=0, minute=0, second=0, microsecond=0)
    offset = timedelta(minutes=30)
    if last_fetched_date is None or as_naver_time_zone(last_fetched_date) < last_midnight - offset:
        # The last time the series list is fetched is too far in the past.
        # It can happen if the app is not very popular.  Mark all series as
        # 'new chapters available' since we might have missed the upload
        # badges for some series.
        for series in series_list:
            series.new_chapters_available = True
    _commit()
    return series_list


def _update_existing_series(fetched_data, update_all, updated):
    series_list = Series.query.all()
    for series in series_list:
        if update_all:
            series_updated, chapters_updated = update_series(series, update_all, False)
            updated[0] |= series_updated
            if chapters_updated:
                updated[1].append(series.id)
        info = fetched_data.get(series.id)
        if info is None:
            # The series is completed or somehow not showing up in the index
            continue
        upload_days = ','.join(info['upload_days'])
        if series.upload_days != upload_days:
            series.upload_days = upload_days
            updated[0] = True
        # updated[0] is not changed below because new_chapters_available and
        # last_update_stattus don't affect the view.
        if any(day not in series.last_upload_status for day in info['days_uploaded']):
            series.new_chapters_available = True
        series.last_upload_status = ','.join(info['days_uploaded'])
    return series_list


def _add_new_series(new_series_ids, fetched_data, update_all, updated):
    if not new_series_ids:
        return
    updated[0] = True
    for series_id in new_series_ids:
        series = Series(id=series_id)
        _, chapters_updated = update_series(series, update_all, False)
        if chapters_updated:
            updated[1].append(series.id)
        info = fetched_data[series.id]
        upload_days = ','.join(info['upload_days'])
        if series.upload_days != upload_days:
            series.upload_days = upload_days
        series.new_chapters_available = True
        series.last_upload_status = ','.join(info['days_uploaded'])


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        app.logger.error('IntegrityError', exc_info=True)
        db.session.rollback()


def _fetch_series_data(series):
    try:
        data = __browser__.get_series_data(series.id)
    except:
        app.logger.error("An error occurred while getting data for series #%d", series.id, exc_info=True)
        return False
    if data.get('removed'):
        if not series.is_completed:
            app.logger.warning('Series #%d seems removed', series.id)
            series.is_completed = True
            return True
        return False
    attributes = ['title', 'author', 'description', 'last_chapter', 'is_completed', 'thumbnail_url']
    return _update_attributes(series, data, attributes)


def _fetch_chapter_data(chapter):
    try:
        data = __browser__.get_chapter_data(chapter.series.id, chapter.id)
    except:
        app.logger.error("An error occurred while getting data for chapter #%d of series #%d",
                chapter.id, chapter.series.id, exc_info=True)
        return False
    if data.get('not_found'):
        raise Chapter.DoesNotExist
    attributes = ['title', 'pubdate', 'thumbnail_url']
    return _update_attributes(chapter, data, attributes)


def _update_attributes(obj, data, attribute_names):
    updated = False
    for attribute_name in attribute_names:
        if getattr(obj, attribute_name) != data[attribute_name]:
            updated = True
            setattr(obj, attribute_name, data[attribute_name])
    return updated


def _add_new_chapters(series):
    updated = False
    current_last_chapter = series.chapters[0].id if len(series.chapters) else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    for chapter_id in chapter_ids:
        chapter = Chapter(series=series, id=chapter_id)
        try:
            if _fetch_chapter_data(chapter):
                # No need to call db.session.add(chapter)
                # It is already in a pending state since series is set.
                # However, it doesn't hurt to do so.
                db.session.add(chapter)
                updated = True
        except Chapter.DoesNotExist:
            db.session.expunge(chapter)
    return updated
