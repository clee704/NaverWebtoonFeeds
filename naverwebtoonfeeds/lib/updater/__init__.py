# -*- coding: UTF-8 -*-
import re
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
import pytz

from naverwebtoonfeeds import app, db, tz
from naverwebtoonfeeds.models import Series, Chapter
from naverwebtoonfeeds.lib.naver import URL, NaverBrowser
from naverwebtoonfeeds.lib.updater.helpers import inner_html


browser = NaverBrowser(app)


def update_series_list(append_only=False):
    old_series_ids = set(map(lambda r: r[0], db.session.query(Series.id).all()))
    for series_id, update_days in _fetch_series_ids().items():
        if append_only and series_id in old_series_ids:
            continue
        series = Series.query.get(series_id)
        if series is None:
            series = Series(id=series_id)
        series.update_days = ','.join(update_days)
        update_series(series)


def update_series(series):
    _fetch_series_data(series)
    db.session.add(series)
    _commit()
    _add_new_chapters(series)


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        app.logger.error('IntegrityError', exc_info=True)
        db.session.rollback()


def _fetch_series_ids():
    series_ids = {}
    doc, _ = browser.get(URL['series_by_day'])
    for url in doc.xpath('//*[@class="list_area daily_all"]//li//a[@class="title"]/@href'):
        m = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
        series_id, day = int(m.group('id')), m.group('day')
        series_ids.setdefault(series_id, []).append(day)
    return series_ids


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
            db.session.rollback()
            continue
        db.session.add(chapter)
        _commit()
