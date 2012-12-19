# -*- coding: UTF-8 -*-
import HTMLParser, errno, logging, os, re, time, urlparse, urllib2
import pytz, lxml.html, requests
from datetime import datetime, timedelta
from flask import Flask, render_template, Response
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_object('default_settings')
app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

# Logging settings
app.logger.setLevel(app.config['LOG_LEVEL'])
formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
app.logger.addHandler(stream_handler)
if app.config.get('SEND_EMAIL'):
    from logging.handlers import SMTPHandler
    smtp_handler = SMTPHandler(app.config['MAIL_HOST'],
                               app.config['MAIL_FROMADDR'],
                               app.config['MAIL_TOADDRS'],
                               app.config['MAIL_SUBJECT'],
                               app.config['MAIL_CREDENTIALS'],
                               app.config['MAIL_SECURE'])
    smtp_handler.setLevel(app.config['EMAIL_LEVEL'])
    smtp_handler.setFormatter(formatter)
    app.logger.addHandler(smtp_handler)

# Naver is in the Seoul time zone (+0900)
tz = pytz.timezone('Asia/Seoul')

db = SQLAlchemy(app)
cache = Cache(app)
htmlparser = HTMLParser.HTMLParser()

class Naver(object):
    BASE = 'http://comic.naver.com/webtoon'
    MOBILE_BASE = 'http://m.comic.naver.com/webtoon'
    URL = {
        'last_chapter': BASE + '/detail.nhn?titleId={series_id}',
        'chapter': BASE + '/detail.nhn?titleId={series_id}&no={chapter_id}',
        'mobile': MOBILE_BASE + '/detail.nhn?titleId={series_id}&no={chapter_id}',
        'series': BASE + '/list.nhn?titleId={series_id}',
        'series_by_day': BASE + '/webtoon/weekday.nhn',
    }

    def __init__(self):
        self.cookies = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; ko; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }

    def login(self):
        if not app.config.get('NAVER_USERNAME'):
            return
        url = 'https://nid.naver.com/nidlogin.login'
        headers = {'Referer': 'http://static.nid.naver.com/login.nhn'}
        headers.update(self.headers)
        data = {
            'enctp': '2',
            'id': app.config['NAVER_USERNAME'],
            'pw': app.config['NAVER_PASSWORD'],
        }
        self.get('http://www.naver.com')   # Get cookies
        r = requests.post(url, data=data, cookies=self.cookies, headers=headers)
        self.cookies = r.cookies
        if 'location.replace' not in r.text[:100]:
            raise RuntimeError("Cannot log in to naver.com")
        app.logger.info('Logged in')

    def get(self, url):
        errors = 0
        while True:
            try:
                app.logger.debug('Requesting GET %s', url)
                r = requests.get(url, cookies=self.cookies, headers=self.headers)
                self.cookies = r.cookies
                if r.url != url and 'login' in r.url:
                    self.login()
                    continue
                if r.status_code == 403:
                    app.logger.error('Access forbidden to public IP %s', self.get_public_ip())
                    raise urllib2.HTTPError(url, 403, 'Forbidden', r.headers, None)
                return lxml.html.fromstring(r.text), r
            except urllib2.URLError:
                app.logger.info('A URLError occurred', exc_info=True)
                errors += 1
                if errors > 5:
                    raise
                app.logger.info('Waiting for 5 seconds before reconnecting')
                time.sleep(5)

    def get_public_ip(self):
        r = requests.get('http://checkip.dyndns.com/')
        # r.text = '<html><head><title>Current IP Check</title></head><body>Current IP Address: 65.96.168.198</body></html>\r\n'
        return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(r.text).group(1)

browser = Naver()


# Models
class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    last_chapter = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    thumbnail_url = db.Column(db.Text)

    def update(self):
        app.logger.debug('Updating series #%d', self.id)
        url = Naver.URL['last_chapter'].format(series_id=self.id)
        doc, response = browser.get(url)
        app.logger.debug('Response URL: %s', url)
        if response.url != url:
            if not self.is_completed:
                app.logger.warning('Series #%d seems removed', self.id)
                self.is_completed = True
        else:
            try:
                app.logger.debug('Parsing series info')
                comicinfo_dsc = doc.xpath('//*[@class="comicinfo"]/*[@class="dsc"]')[0]
                permalink = doc.xpath('//meta[@property="og:url"]/@content')[0]
                status = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em/text()')[0].strip()
                self.title = comicinfo_dsc.xpath('h2/text()')[0].strip()
                self.author = comicinfo_dsc.xpath('h2/em')[0].text_content().strip()
                self.description = br2nl(comicinfo_dsc.xpath('p[@class="txt"]')[0].inner_html())
                self.last_chapter = int(re.search('no=(\d+)', permalink).group(1))
                self.is_completed = status == u'완결웹툰'
                self.thumbnail_url = doc.xpath('//meta[@property="og:image"]/@content')[0]
            except IndexError:
                app.logger.error(response.url + '\n' + response.text)
                raise


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    pubdate = db.Column(db.DateTime, nullable=False)
    thumbnail_url = db.Column(db.Text)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('chapters', order_by=id.desc(), lazy='dynamic'))

    def update(self):
        app.logger.debug('Updating chapter #%d of series #%d', self.id, self.series.id)
        url = Naver.URL['chapter'].format(series_id=self.series.id, chapter_id=self.id)
        doc, _ = browser.get(url)
        if url != doc.xpath('//meta[@property="og:url"]/@content')[0]:
            raise Chapter.DoesNotExist
        date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]/@value')[0]
        naive_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        self.title = doc.xpath('//meta[@property="og:description"]/@content')[0]
        self.pubdate = tz.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None)
        self.thumbnail_url = doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/@src')[0]
        assert '{0}/{1}'.format(self.series.id, self.id) in self.thumbnail_url

    class DoesNotExist(Exception):
        pass


class UpdateDay(db.Model):
    day = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('updatedays', lazy='dynamic'))


class Config(db.Model):
    key = db.Column(db.Text, primary_key=True)
    value = db.Column(db.PickleType)


# Model helpers
def br2nl(html):
    """
    Convert newlines to spaces, <br> tags to newlines, collapse consecutive
    whitespaces into single whitespace, remove leading and trailing
    whitespaces, and unescape HTML entities.

    >>> br2nl('hello,<br>world! ')
    'hello,\\nworld!'
    >>> br2nl('\\nnice to meet you!<br />')
    'nice to meet you!'
    >>> br2nl(' <br> welcome<br >to  <br/>  earth')
    'welcome\\nto\\nearth'

    """
    newlines_removed = html.replace('\r\n', '\n').replace('\n', ' ')
    br_converted = re.sub(r'<br */?>', '\n', newlines_removed)
    whitespaces_collapsed = re.sub(r' +', ' ', br_converted)
    whitespaces_merged = re.sub(r' ?\n ?', '\n', whitespaces_collapsed)
    return htmlparser.unescape(whitespaces_merged.strip())


def inner_html(self):
    """
    Return the string for this HtmlElement, without enclosing start and end
    tags, or an empty string if this is a self-enclosing tag.

    >>> lxml.html.fromstring('<p>hello,<br>world!</p>').inner_html()
    u'hello,<br>world!'
    >>> lxml.html.fromstring('<div class="foo"><span>bar <span>bar</span></span> bar</div>').inner_html()
    u'<span>bar <span>bar</span></span> bar'
    >>> lxml.html.fromstring('<img src="http://nowhere.com/nothing.jpg" />').inner_html()
    u''
    >>> lxml.html.fromstring(u'<p>\ub17c\uc544\uc2a4\ud0a4</p>').text
    u'\ub17c\uc544\uc2a4\ud0a4'

    """
    outer = lxml.html.tostring(self, encoding='UTF-8').decode('UTF-8')
    i, j = outer.find('>'), outer.rfind('<')
    return outer[i + 1:j]
lxml.html.HtmlElement.inner_html = inner_html


# Views
@app.route('/')
def show_feed_list():
    app.logger.info('GET /')
    response = cache.get(show_feed_list.cache_key)
    if response:
        app.logger.debug('Cache hit')
        return response
    valid_for = update_series_info()
    series_list = Series.query.filter_by(is_completed=False).order_by(Series.title).all()
    response = render_template('feeds.html', series_list=series_list)
    cache.set(show_feed_list.cache_key, response, valid_for)
    app.logger.debug('Cache created, valid for %s seconds', valid_for)
    return response
show_feed_list.cache_key = 'feeds'


@app.route('/feeds/<int:series_id>.xml')
def show_feed(series_id):
    app.logger.info('GET /feeds/%d.xml', series_id)
    cache_key = show_feed.cache_key.format(series_id)
    response = cache.get(cache_key)
    if response:
        app.logger.debug('Cache hit')
        return response
    series = Series.query.get_or_404(series_id)
    valid_for = update_chapters(series, update_series=True)
    chapters = []
    for c in series.chapters:
        # _pubdate_tz is used in templates to correct time zone
        c._pubdate_tz = pytz.utc.localize(c.pubdate).astimezone(tz)
        chapters.append(c)
    xml = render_template('feed.xml', series=series, chapters=chapters, naver_url=naver_url)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set(cache_key, response, valid_for)
    app.logger.debug('Cache created, valid for %s seconds', valid_for)
    return response
show_feed.cache_key = 'feed_{0}'


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# View helpers
@app.template_filter()
def make_external(url):
    """
    Externalize the given internal URL path like /foo/bar to
    http://myserver.com/foo/bar so that it can be used in feeds.

    """
    return urlparse.urljoin(app.config['URL_ROOT'], url)


@app.template_filter()
def via_imgproxy(url):
    u = app.config.get('IMGPROXY_URL')
    return u.format(url=url) if u else url


def naver_url(series_id, chapter_id=None, mobile=False):
    """Return appropriate webtoon URL for the given arguments."""
    key = 'mobile' if mobile else 'series' if chapter_id is None else 'chapter'
    return Naver.URL[key].format(series_id=series_id, chapter_id=chapter_id)


# Update functions
def update_series_info(force_update=False, should_update_chapters=False):
    """
    Update all series information to date. Returns the remaining seconds before
    the next update can occur.

    Every update occurs at least 7 days after the previous update. If the
    previous update is within 7 days ago, update will not occur.

    If force_update is True, it will work as if the update interval is passed.

    """
    update_interval = timedelta(days=7)
    timer_key = 'series_info_updated'
    u = Config.query.get(timer_key)
    if u is not None and not force_update:
        since_last_update = datetime.now() - u.value
        if since_last_update < update_interval:
            return int(since_last_update.total_seconds())
    today = datetime.now().weekday()
    for series_id, update_days in fetch_series_ids().items():
        s = Series.query.get(series_id)
        if s is None:
            s = Series(id=series_id)
        s.update()
        db.session.add(s)
        db.session.query(UpdateDay).filter_by(series=s).delete()
        db.session.add_all(UpdateDay(series=s, day=day) for day in update_days)
        try:
            db.session.commit()
        except IntegrityError:
            app.logger.error('IntegrityError', exc_info=True)
            db.session.rollback()
            continue
        if should_update_chapters:
            s.update_chapters()
    return reset_cache(show_feed_list.cache_key, timer_key, update_interval)


def update_chapters(series, update_series=False):
    """
    Get new chapters of the specified series. Returns the remaining seconds
    before the next update can occur.

    Every update occurs at least 1 hour after the previous update. If the
    previous update is within 1 hour ago, update will not occur.

    """
    if update_series:
        series.update()
        db.session.add(series)
        db.session.commit()
    update_interval = timedelta(hours=1)
    timer_key = '{0}_chapters_updated'.format(series.id)
    u = Config.query.get(timer_key)
    if u is not None:
        since_last_update = datetime.now() - u.value
        if since_last_update < update_interval:
            return int(since_last_update.total_seconds())
    current_last_chapter = series.chapters[0].id if series.chapters.count() else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    if not chapter_ids:
        # Nothing new
        return int(update_interval.total_seconds())
    for chapter_id in chapter_ids:
        c = Chapter(series=series, id=chapter_id)
        try:
            c.update()
        except Chapter.DoesNotExist:
            db.session.rollback()
            continue
        db.session.add(c)
        try:
            db.session.commit()
        except IntegrityError:
            app.logger.error('IntegrityError', exc_info=True)
            db.session.rollback()
            continue
    return reset_cache(show_feed.cache_key.format(series.id), timer_key, update_interval)


def reset_cache(cache_key, timer_key, update_interval):
    cache.delete(cache_key)
    Config.query.filter_by(key=timer_key).delete()
    updated = datetime.now()
    db.session.add(Config(key=timer_key, value=updated))
    db.session.commit()
    return int(update_interval.total_seconds())


NUMERIC_DAYS = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
def fetch_series_ids():
    """Fetch series IDs and their update days and return a dictionary."""
    series_ids = {}
    doc, _ = browser.get(Naver.URL['series_by_day'])
    for url in doc.xpath('//*[@class="list_area daily_all"]//li//a[@class="title"]/@href'):
        m = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
        series_id, day = int(m.group('id')), m.group('day')
        series_ids.setdefault(series_id, []).append(NUMERIC_DAYS[day])
    return series_ids


# Create tables for models
db.create_all()


if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception:
        app.logger.critical('A critical error occurred', exc_info=True)
