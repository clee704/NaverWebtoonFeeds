# -*- coding: UTF-8 -*-
import re
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
import pytz

from naverwebtoonfeeds import app, cache, db, tz
from naverwebtoonfeeds.models import Series, Chapter
from naverwebtoonfeeds.lib.naver import URL, NaverBrowser
from naverwebtoonfeeds.lib.updater.helpers import inner_html


# The longer this interval, the fewer HTTP requests will be made to Naver.
# 30 min to 1 hour would be a good choice.
# Should be shorter than 1 day.
SERIES_STATS_UPDATE_INTERVAL = timedelta(hours=1)

# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10


browser = NaverBrowser(app)


def update_series_list(update_all=False):
    fetched = cache.get('series_list_fetched')
    if (update_all or fetched is None or
            fetched + SERIES_STATS_UPDATE_INTERVAL < datetime.now()):
        _fetch_series_list(update_all)
        cache.set('series_list_fetched', datetime.now(), CACHE_PERMANENT)


def _fetch_series_list(update_all):
    fetched_data = {}
    doc, _ = browser.get(URL['series_by_day'])
    for a in doc.xpath('//*[@class="list_area daily_all"]//li/*[@class="thumb"]/a'):
        url = a.attrib['href']
        m = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
        series_id, day = int(m.group('id')), m.group('day')
        updated = len(a.xpath('em[@class="ico_updt"]')) > 0
        info = fetched_data.setdefault(series_id, {})
        info.setdefault('update_days', []).append(day)
        if info.get('updated') is None or updated:
            info['updated'] = updated
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
        if not series.last_update_status and info['updated']:
            series.new_chapters_available = True
        series.last_update_status = info['updated']
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
    url = URL['last_chapter'].format(series_id=series.id)
    doc, response = browser.get(url)
    app.logger.debug('Response URL: %s', url)
    if response.url != url:
        if not series.is_completed:
            app.logger.warning('Series #%d seems removed', series.id)
            series.is_completed = True
    else:
        try:
            app.logger.debug('Parsing data for series #%d', series.id)
            comicinfo_dsc = doc.xpath('//*[@class="comicinfo"]/*[@class="dsc"]')[0]
            permalink = doc.xpath('//meta[@property="og:url"]/@content')[0]
            status = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em/text()')[0].strip()
            series.title = comicinfo_dsc.xpath('h2/text()')[0].strip()
            series.author = comicinfo_dsc.xpath('h2/em')[0].text_content().strip()
            series.description = inner_html(comicinfo_dsc.xpath('p[@class="txt"]')[0])
            series.last_chapter = int(re.search('no=(\d+)', permalink).group(1))
            series.is_completed = status == u'완결웹툰'
            series.thumbnail_url = doc.xpath('//meta[@property="og:image"]/@content')[0]
        except IndexError:
            app.logger.error(response.url + '\n' + response.text)
            raise


def _fetch_chapter_data(chapter):
    url = URL['chapter'].format(series_id=chapter.series.id, chapter_id=chapter.id)
    doc, _ = browser.get(url)
    if url != doc.xpath('//meta[@property="og:url"]/@content')[0]:
        raise Chapter.DoesNotExist
    app.logger.debug('Parsing data for chapter #%d of series #%d', chapter.id, chapter.series.id)
    date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]/@value')[0]
    naive_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    chapter.title = doc.xpath('//meta[@property="og:description"]/@content')[0]
    chapter.pubdate = tz.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None)
    chapter.thumbnail_url = doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/@src')[0]
    assert '{0}/{1}'.format(chapter.series.id, chapter.id) in chapter.thumbnail_url


def _add_new_chapters(series):
    current_last_chapter = series.chapters[0].id if len(series.chapters) else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    for chapter_id in chapter_ids:
        chapter = Chapter(series=series, id=chapter_id)
        try:
            _fetch_chapter_data(chapter)
        except Chapter.DoesNotExist:
            continue
        db.session.add(chapter)
