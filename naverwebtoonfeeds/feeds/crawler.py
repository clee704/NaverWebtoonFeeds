# -*- coding: UTF-8 -*-
"""
    naverwebtoonfeeds.crawler
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the functionality that synchronizes data from the Naver website.

"""
import logging
import re
import time
from datetime import datetime, timedelta

import lxml.html
import lxml.html.soupparser
import pytz
import requests
from flask import current_app
from netaddr import IPNetwork
from requests.exceptions import HTTPError, RequestException
from sqlalchemy.exc import SQLAlchemyError

from ..ext import cache, db
from .helpers import (as_naver_time_zone, get_public_ip, index_cache_key,
                      inner_html, NAVER_TIMEZONE, NAVER_URLS)
from .models import Chapter, Series
from .views import render_feed, render_index


logger = logging.getLogger(__name__)


class Crawler(object):

    def __init__(self):
        self.browser = NaverBrowser()

    def update_series_list(self, update_all=False, render_views=True):
        updated = [False, []]
        # updated[0]: index page is updated
        # updated[1]: feed page with series id in this list is updated

        if not series_list_needs_update():
            logger.debug('Series list is recently updated')
            return updated

        fetched_data = self._fetch_series_list()
        series_list = self._update_existing_series(fetched_data, update_all,
                                                   updated)

        # Update badges are cleared at the midnight and generated when the
        # series has been uploaded today.
        #
        # If offset is too long, say 3 hours, and a series is uploaded at 10pm,
        # and there was no request to the app until right after the midnight,
        # then we'll miss the update badge for the series.
        #
        # If offset is too short, say 1 minute, then all series will be marked
        # as 'new chapters available' however frequent requests are, since
        # the minimum interval to fetch series list is 15 minutes or so. It
        # will increase the rate of requests to Naver (1 per series per day)
        # and slow the page loading.
        #
        # If the requests to the app is frequent enough, setting it to just
        # above the minimum fetch interval will be fine.
        if series_list_out_of_sync():
            # The last time the series list is fetched is too far in the past.
            # It can happen if your app is not very popular.  Mark all series
            # as 'new chapters available' since we might have missed the upload
            # badges for some series.
            for series in series_list:
                if not series.is_completed:
                    series.new_chapters_available = True

        existing_series_ids = set(series.id for series in series_list)
        new_series_ids = fetched_data.viewkeys() - existing_series_ids
        self._add_new_series(new_series_ids, fetched_data, update_all, updated)

        self._commit()

        for series in Series.query.filter_by(new_chapters_available=True):
            series_updated, chapters_added = self.update_series(
                series, do_commit=False, render_views=False)
            updated[0] |= series_updated
            if series_updated or chapters_added:
                updated[1].append(series.id)

        self._commit()

        # Pre-render pages for better performance for end users. However, if
        # the cache is not large enough to contain all the rendered page, it
        # can be unhelpful.
        if render_views:
            if updated[0]:
                render_index()
            for series_id in updated[1]:
                render_feed(series_id)

        cache.set_permanently('series_list_fetched', datetime.utcnow())

        return updated

    def add_ended_series(self, add_new_chapters=True):
        completed_series = self.browser.get_completed_series()
        completed_series_ids = set(data['id'] for data in completed_series)
        existing_series_ids = set(row[0] for row
                                  in db.session.query(Series.id))
        for series_id in completed_series_ids - existing_series_ids:
            series = Series(id=series_id)
            series.new_chapters_available = True
            self.update_series(series, add_new_chapters)
        cache.delete(index_cache_key())

    def update_series(self, series, add_new_chapters=True, do_commit=True,
                      render_views=True):
        try:
            series_updated = self._update_series_info(series)
        except UnauthorizedRequest:
            return [False, False]
        chapters_added = False
        db.session.add(series)
        if add_new_chapters and series.new_chapters_available:
            chapters_added = self._add_new_chapters(series)
            if chapters_added:
                series.new_chapters_available = False
                series.retries_left = 0
            elif series.retries_left == 0:
                logger.warning("Couldn't find new chapters in series %d",
                               series.id)
                series.new_chapters_available = False
            else:
                # Sometimes new chapters are not available on the website even
                # though there are update badges. We should try later in those
                # cases.
                logger.info('No new chapters in series %d; retry later',
                            series.id)
                series.retries_left -= 1

        if do_commit:
            self._commit()

        if render_views and (series_updated or chapters_added):
            render_feed(series.id)

        return [series_updated, chapters_added]

    def _update_existing_series(self, fetched_data, update_all, updated):
        logger.debug('Updating series in the database')
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
            if any(day not in series.last_upload_status for day
                   in info['days_uploaded']):
                series.new_chapters_available = True
                series.retries_left = 3
            series.last_upload_status = ','.join(info['days_uploaded'])
            if update_all:
                series_updated, chapters_added = self.update_series(
                    series, update_all, do_commit=False, render_views=False)
                updated[0] |= series_updated
                if chapters_added:
                    updated[1].append(series.id)
        return series_list

    def _add_new_series(self, new_series_ids, fetched_data, update_all,
                        updated):
        if not new_series_ids:
            return
        logger.debug('Adding new series to the database')
        updated[0] = True
        for series_id in new_series_ids:
            series = Series(id=series_id)
            series_updated, chapters_added = self.update_series(
                series, update_all, do_commit=False, render_views=False)
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

    def _add_new_chapters(self, series):
        logger.debug('Adding new chapters to series %d', series.id)
        updated = False
        current_last_chapter = (series.chapters[0].id if len(series.chapters)
                                else 0)
        start = current_last_chapter + 1
        chapter_ids = range(start, series.last_chapter + 1)
        logger.debug('New chapters: %s', chapter_ids)
        for chapter_id in chapter_ids:
            chapter = Chapter(series=series, id=chapter_id)
            # chapter is in a pending state, probably because of the series
            # attribute. But I couldn't find this in the documentation.
            if self._update_chapter_info(chapter):
                logger.debug('Chapter %d is fetched', chapter_id)
                chapter.atom_id = make_atom_id(chapter)
                # Not necessary; it doesn't hurt to do so.
                db.session.add(chapter)
                updated = True
            else:
                db.session.expunge(chapter)
        return updated

    def _fetch_series_list(self):
        fetched_data = {}
        series_list = self.browser.get_series_list()
        logger.debug('Got a series list from Naver')
        for data in series_list:
            info = fetched_data.setdefault(data['id'], {})
            info.setdefault('upload_days', []).append(data['day'])
            days_uploaded = info.setdefault('days_uploaded', [])
            if data['days_uploaded']:
                days_uploaded.append(data['days_uploaded'])
        return fetched_data

    def _update_series_info(self, series):
        info = self.browser.get_series_info(series.id)
        logger.debug('Got info for series %d', series.id)
        if info.get('removed'):
            if not series.is_completed:
                logger.warning('Series %d seems to be removed', series.id)
                series.is_completed = True
                return True
            return False
        return update_attrs(series,
                            info,
                            ['title', 'author', 'description', 'last_chapter',
                             'is_completed', 'thumbnail_url'])

    def _update_chapter_info(self, chapter):
        info = self.browser.get_chapter_info(chapter.series.id, chapter.id)
        logger.debug('Got info for chapter %d in series %d', chapter.id,
                     chapter.series.id)
        if info.get('not_found'):
            return False
        return update_attrs(chapter,
                            info,
                            ['title', 'pubdate', 'thumbnail_url'])

    def _commit(self):
        try:
            db.session.commit()
            logger.debug('Changes committed')
        except SQLAlchemyError:
            logger.exception('Failed to commit')
            db.session.rollback()


def series_list_needs_update():
    now = datetime.utcnow()
    interval = series_stats_update_interval()
    fetched = cache.get('series_list_fetched')
    return fetched is None or fetched + interval < now


def series_stats_update_interval():
    # The longer this interval, the fewer HTTP requests will be made to Naver.
    # 30 min to 1 hour would be a good choice and should be shorter than 1 day.
    hour = as_naver_time_zone(datetime.utcnow()).hour

    # Values are based on the upload history since May 31, 2012
    # when the official upload time was changed from midnight to 11pm.
    if hour == 23:
        # The rush hour; 85% of chapters were uploaded at 11pm.
        return timedelta(minutes=10)
    elif hour in (10, 11, 0):
        # 7% of chapters were uploaded either at 10am, 11am, or midnight.
        return timedelta(minutes=30)
    else:
        return timedelta(hours=1)


def series_list_out_of_sync():
    # Update badges in the series list page on Naver are cleared at the
    # midnight and generated when the series has been uploaded today.
    #
    # If offset is too long, say 3 hours, and a series is uploaded at 10pm,
    # and there was no request to the app until right after the midnight,
    # then we'll miss the update badge for that series.
    #
    # If offset is too short, say 1 minute, then all series will be marked
    # as 'new chapters available' however frequent requests are, since
    # the minimum interval to fetch series list is 15 minutes or so. It
    # will increase the rate of requests to Naver (1 per series per day)
    # and slow the page loading.
    #
    # If the requests to the app is frequent enough, setting it to just
    # above the minimum fetch interval will be fine.
    fetched = cache.get('series_list_fetched')
    if fetched is None:
        return True
    now = datetime.utcnow()
    last_midnight = as_naver_time_zone(now).replace(hour=0,
                                                    minute=0,
                                                    second=0,
                                                    microsecond=0)
    offset = timedelta(minutes=30)
    return as_naver_time_zone(fetched) < last_midnight - offset


def update_attrs(obj, info, attrs):
    updated = False
    for attr in attrs:
        if getattr(obj, attr) != info[attr]:
            updated = True
            setattr(obj, attr, info[attr])
    return updated


def make_atom_id(chapter):
    date = datetime.utcnow().strftime('%Y-%m-%d')
    tagging_entity = current_app.config['AUTHORITY_NAME'] + ',' + date
    specific_list = ['generator=naverwebtoonfeeds']
    specific_list.append('series={0}'.format(chapter.series.id))
    specific_list.append('chapter={0}'.format(chapter.id))
    return 'tag:' + tagging_entity + ':' + ';'.join(specific_list)


class NaverBrowser(object):

    headers = {
        'User-Agent': 'Mozilla/5.0 '
                      '(Windows; U; Windows NT 6.1; ko; rv:1.9.2.3) '
                      'Gecko/20100401 Firefox/3.6.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                  '*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
    }

    blacklist = [IPNetwork(net) for net in [
        '50.16.0.0/15',
        '50.19.0.0/16',
        '184.72.64.0/18',
        '184.72.128.0/17',
        '184.73.0.0/16',
        '204.236.192/18',
    ]]

    def __init__(self, max_retries=3):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.max_retries = max_retries
        self.public_ip = get_public_ip()

    def ensure_not_blacklisted(self):
        if any(self.public_ip in net for net in self.blacklist):
            logger.warning('Your IP address %s is blacklisted', self.public_ip)
            raise AccessDenied()

    def get(self, url):
        self.ensure_not_blacklisted()
        errors = 0
        delay = 1
        while 1:
            resp, errors, delay = self._get(url, errors, delay)
            if resp is not None:
                return resp

    def _get(self, url, errors, delay):
        resp = None
        try:
            logger.debug('Requesting GET %s', url)
            resp = self.session.get(url)
            resp.raise_for_status()
            if 'login' in resp.url:
                if not current_app.config['FETCH_ADULT_ONLY']:
                    raise AdultOnly()
                if self.login():
                    resp = None  # request again
                else:
                    raise UnauthorizedRequest()
            return resp, errors, delay
        except HTTPError as exc:
            if resp is not None and resp.status_code == 403:
                logger.error('Your IP address %s is denied', self.public_ip)
                raise AccessDenied()
            logger.warning('Failed to request %s: %s', url, exc)
        except RequestException:
            logger.warning('Failed to request %s', url, exc_info=True)
        if errors >= self.max_retries:
            raise TooManyErrors()
        logger.debug('Waiting for %.1f seconds before reconnecting', delay)
        time.sleep(delay)
        return None, errors + 1, delay + 1

    def login(self):
        """Logs in to Naver and return *True* if logged in and *False* if
        failed.

        """
        logger.debug('Trying to log in to Naver')
        url = 'https://nid.naver.com/nidlogin.login'
        data = {
            'enctp': '2',
            'id': current_app.config['NAVER_USERNAME'],
            'pw': current_app.config['NAVER_PASSWORD'],
        }
        self.get('http://www.naver.com/')  # Get initial cookies
        resp = self.session.post(
            url,
            data=data,
            headers={'Referer': 'http://static.nid.naver.com/login.nhn'})
        if 'location.replace' not in resp.text[:100]:
            logger.error('Login failed: wrong username or password')
            return False
        logger.info('Logged in')
        return True

    def get_series_list(self):
        resp = self.get(NAVER_URLS['series_by_day'])
        doc = parse_html(resp.content, resp.url)
        return parse_series_list(doc)

    def get_completed_series(self):
        resp = self.get(NAVER_URLS['completed_series'])
        doc = parse_html(resp.content, resp.url)
        return parse_completed_series(doc)

    def get_series_info(self, series_id):
        url = NAVER_URLS['last_chapter'].format(series_id=series_id)
        resp = self.get(url)
        if resp.url == 'http://comic.naver.com/main.nhn':
            return dict(removed=True)
        doc = parse_html(resp.content, resp.url)
        return parse_series_info(doc, series_id)

    def get_chapter_info(self, series_id, chapter_id):
        url = NAVER_URLS['chapter'].format(series_id=series_id,
                                           chapter_id=chapter_id)
        resp = self.get(url)
        if resp.url == 'http://comic.naver.com/main.nhn':
            return dict(not_found=True)
        doc = parse_html(resp.content, resp.url)
        return parse_chapter_info(doc, series_id, chapter_id, url)


class BrowserException(Exception):
    pass


class AccessDenied(BrowserException):
    pass


class AdultOnly(BrowserException):
    pass


class TooManyErrors(BrowserException):
    pass


class UnauthorizedRequest(BrowserException):
    pass


class UnparsableResponse(BrowserException):
    pass


def parse_html(html, url):
    modules = [lxml.html.soupparser, lxml.html]
    # lxml.html.soupparser.fromstring (requires BeautifulSoup) is generally
    # more tolerant than lxml.html.fromstring, so it can parse HTML with
    # unescaped brackets (<, >) which appear often. But there are some
    # cases where lxml.html.soupparser.fromstring misbehaves while
    # lxml.html.fromstring works.
    for mod in modules:
        try:
            return mod.fromstring(html)
        except Exception:
            logger.exception('Failed to parse %s with %s', url, mod.__name__)
    raise UnparsableResponse()


def parse_series_list(doc):
    logger.debug('Parsing the current series list')
    retval = []
    for a_elem in doc.xpath('//*[@class="list_area daily_all"]//li'
                            '/*[@class="thumb"]/a'):
        url = a_elem.attrib['href']
        match = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
        series_id, day = int(match.group('id')), match.group('day')
        uploaded = len(a_elem.xpath('em[@class="ico_updt"]')) > 0
        retval.append(dict(id=series_id, day=day,
                           days_uploaded=day if uploaded else False))
    return retval


def parse_completed_series(doc):
    logger.debug('Parsing the ended series list')
    retval = []
    for a_elem in doc.xpath('//*[@class="list_area"]//li/*[@class="thumb"]/a'):
        url = a_elem.attrib['href']
        match = re.search(r'titleId=(?P<id>\d+)', url)
        series_id = int(match.group('id'))
        retval.append(dict(id=series_id))
    return retval


def parse_series_info(doc, series_id):
    logger.debug('Parsing series %d', series_id)
    comicinfo = doc.xpath('//*[@class="comicinfo"]/'
                          '*[@class="detail" or @class="dsc"]')[0]
    permalink = doc.xpath('//meta[@property="og:url"]/@content')[0]
    status = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em'
                       '/text()')[0].strip()
    return {
        'title': comicinfo.xpath('h2/text()')[0].strip(),
        'author': comicinfo.xpath('h2/*[@class="wrt_nm"]|h2/em')[0]
                           .text_content().strip(),
        'description': inner_html(comicinfo.xpath('p[@class="txt"]')[0]),
        'last_chapter': int(re.search(r'no=(\d+)', permalink).group(1)),
        'is_completed': status == u'완결웹툰',
        'thumbnail_url': doc.xpath('//meta[@property="og:image"]/@content')[0],
    }


def parse_chapter_info(doc, series_id, chapter_id, url):
    logger.debug('Parsing chapter %d of series %d', chapter_id, series_id)
    date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]'
                         '/@value')[0]
    naive_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    info = {
        'title': doc.xpath('//meta[@property="og:description"]/@content')[0],
        'pubdate': NAVER_TIMEZONE.localize(naive_dt)
                                 .astimezone(pytz.utc)
                                 .replace(tzinfo=None),
        'thumbnail_url': doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/'
                                   '@src')[0],
    }
    if '{}/{}'.format(series_id, chapter_id) not in info['thumbnail_url']:
        logger.error('Thumbnail URL looks strange: thumbnail_url=%s, '
                     'series_id=%d, chapter_id=%d',
                     info['thumbnail_url'], series_id, chapter_id)
    return info
