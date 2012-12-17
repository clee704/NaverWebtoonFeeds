# -*- coding: UTF-8 -*-
import HTMLParser, errno, logging, os, re, sys, urlparse, lxml.html, mechanize
import time, pytz, urllib2
from datetime import datetime, timedelta
from flask import Flask, abort, render_template, Response
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_object('default_settings')
app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

if app.config.get('SEND_EMAIL'):
    from logging.handlers import SMTPHandler
    handler = SMTPHandler(app.config['MAIL_HOST'],
                          app.config['MAIL_FROMADDR'],
                          app.config['MAIL_TOADDRS'],
                          app.config['MAIL_SUBJECT'],
                          app.config['MAIL_CREDENTIALS'],
                          app.config['MAIL_SECURE'])
    handler.setLevel(app.config['EMAIL_LEVEL'])
    app.logger.addHandler(handler)

# Time zone should be the same as that used by Naver
tz = pytz.timezone('Asia/Seoul')

PROJECT_DIR = os.path.dirname(__file__)
NAVER_URLS = {
    'mobile': 'http://m.comic.naver.com/webtoon/detail.nhn?titleId={series_id}&no={chapter_id}',
    'chapter': 'http://comic.naver.com/webtoon/detail.nhn?titleId={series_id}&no={chapter_id}',
    'series': 'http://comic.naver.com/webtoon/list.nhn?titleId={series_id}',
    'last_chapter': 'http://comic.naver.com/webtoon/detail.nhn?titleId={series_id}',
    'series_by_day': 'http://comic.naver.com/webtoon/weekday.nhn',
}

db = SQLAlchemy(app)
cache = Cache(app)
htmlparser = HTMLParser.HTMLParser()
class MyBrowser(object):

    RELOGIN_INTERVAL = timedelta(minutes=10)

    def __init__(self):
        self.b = mechanize.Browser()
        self.b.set_handle_robots(False)
        self.last_login = None

    def login(self):
        """
        Log in to Naver using the username and password in the configuration file.

        """
        if not app.config.get('NAVER_USERNAME'):
            return
        self.b.open('http://static.nid.naver.com/login.nhn')
        self.b.select_form(nr=0)
        self.b.form['id'] = app.config['NAVER_USERNAME']
        self.b.form['pw'] = app.config['NAVER_PASSWORD']
        r = self.b.submit()
        if 'location.replace' not in r.read()[:100]:
            raise RuntimeError("Cannot log in to naver.com")
        self.last_login = datetime.now()

    def open(self, url):
        if (self.last_login is None or
                self.last_login + MyBrowser.RELOGIN_INTERVAL < datetime.now()):
            self.login()
        errors = 0
        while True:
            try:
                return self.b.open(url)
            except urllib2.URLError:
                if errors > 5:
                    raise
                errors += 1
                time.sleep(3)
browser = MyBrowser()


# Models
class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    last_chapter = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    thumbnail_url = db.Column(db.Text)

    def update(self):
        app.logger.debug('Updating series #%d', self.id)
        url = NAVER_URLS['last_chapter'].format(series_id=self.id)
        r = browser.open(url)
        try:
            doc = lxml.html.fromstring(r.read())
        except AttributeError:
            return
        if r.geturl() != url:
            app.logger.warning('Series #{0} seems removed'.format(self.id))
            self.is_completed = True
        else:
            comicinfo_dsc = doc.xpath('//*[@class="comicinfo"]/*[@class="dsc"]')[0]
            self.title = comicinfo_dsc.xpath('h2/text()')[0].strip()
            self.author = comicinfo_dsc.xpath('h2/em')[0].text_content().strip()
            self.description = br2nl(comicinfo_dsc.xpath('p[@class="txt"]')[0].inner_html()).strip()
            remote_url = doc.xpath('//meta[@property="og:url"]/@content')[0]
            self.last_chapter = int(re.search('no=(\d+)', remote_url).group(1))
            self.is_completed = doc.xpath('//*[@id="submenu"]//*[@class="current"]/em/text()')[0].strip() == u'완결웹툰'
            self.thumbnail_url = doc.xpath('//meta[@property="og:image"]/@content')[0]

    def update_chapters(self, update_self=False):
        if update_self:
            self.update()
        update_chapters(self)


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('chapters', order_by=id.desc(), lazy='dynamic'))
    title = db.Column(db.Text, nullable=False)
    pubdate = db.Column(db.DateTime, nullable=False)
    thumbnail_url = db.Column(db.Text)

    def update(self):
        app.logger.debug('Updating chapter #%d of series #%d', self.id, self.series.id)
        url = NAVER_URLS['chapter'].format(series_id=self.series.id, chapter_id=self.id)
        r = browser.open(url)
        try:
            doc = lxml.html.fromstring(r.read())
        except AttributeError:
            return
        if url != doc.xpath('//meta[@property="og:url"]/@content')[0]:
            raise Chapter.DoesNotExist
        self.title = doc.xpath('//meta[@property="og:description"]/@content')[0]
        date_str = doc.xpath('//form[@name="reportForm"]/input[@name="itemDt"]/@value')[0]
        naive_dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S KST %Y')
        self.pubdate = tz.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None)
        self.thumbnail_url = doc.xpath('//*[@id="comic_move"]//*[@class="on"]/img/@src')[0]
        assert '{0}/{1}'.format(self.series.id, self.id) in self.thumbnail_url

    class DoesNotExist(Exception):
        pass


class UpdateDay(db.Model):
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('updatedays', lazy='dynamic'))
    day = db.Column(db.Integer, primary_key=True)


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
    html = html.replace('\r\n', '\n')
    html = html.replace('\n', ' ')
    html = re.sub(r'<br */?>', '\n', html)
    html = re.sub(r' +', ' ', html)
    html = re.sub(r' ?\n ?', '\n', html)
    html = html.strip()
    html = htmlparser.unescape(html)
    return html


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
    response = cache.get(show_feed_list.cache_key)
    if response:
        return response
    valid_for = update_series_info()
    series_list = Series.query.filter_by(is_completed=False).order_by(Series.title).all()
    response = render_template('feeds.html', series_list=series_list)
    cache.set(show_feed_list.cache_key, response, valid_for)
    return response
show_feed_list.cache_key = 'feeds'


@app.route('/feeds/<int:series_id>.xml')
def show_feed(series_id):
    cache_key = show_feed.cache_key.format(series_id)
    response = cache.get(cache_key)
    if response:
        return response
    series = Series.query.get(series_id)
    if series is None:
        abort(404)
    valid_for = series.update_chapters(update_self=True)
    chapters = []
    for c in series.chapters:
        # _pubdate_tz is used in templates to correct time zone
        c._pubdate_tz = pytz.utc.localize(c.pubdate).astimezone(tz)
        chapters.append(c)
    xml = render_template('feed.xml', series=series, chapters=chapters, naver_url=naver_url)
    response = Response(response=xml, content_type='application/atom+xml')
    cache.set(cache_key, response, valid_for)
    return response
show_feed.cache_key = 'feed_{0}'


@app.errorhandler(500)
def page_not_found(e):
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
def fix_strange_url(url):
    """
    Fix the strange URL returned by request.url which has duplicate domain
    names, e.g. "http://example.com,example.com/path/to/foo".

    """
    parsed = urlparse.urlparse(url)
    x = parsed.netloc.split(',')
    if len(x) == 2 and x[0] == x[1]:
        return urlparse.urlunparse(parsed._replace(netloc=x[0]))
    else:
        return url


@app.template_filter()
def via_imgproxy(url):
    u = app.config.get('IMGPROXY_URL')
    return u.format(url=url) if u else url


def naver_url(series_id, chapter_id=None, mobile=False):
    """Return appropriate webtoon URL for the given arguments."""
    key = 'mobile' if mobile else 'series' if chapter_id is None else 'chapter'
    return NAVER_URLS[key].format(series_id=series_id, chapter_id=chapter_id)


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
    config_key = 'series_info_updated'
    u = Config.query.get(config_key)
    if not force_update and u is not None:
        since_last_update = datetime.now() - u.value
        if since_last_update < update_interval:
            return int(since_last_update.total_seconds())
    today = datetime.now().weekday()
    for series_id, update_days in fetch_series_ids().items():
        s = Series.query.get(series_id)
        new = s is None
        if new:
            s = Series(id=series_id)
        s.update()
        db.session.add(s)
        db.session.query(UpdateDay).filter_by(series=s).delete()
        db.session.add_all(UpdateDay(series=s, day=day) for day in update_days)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            continue
        if should_update_chapters:
            s.update_chapters()
    remove_cache(show_feed_list)
    Config.query.filter_by(key=config_key).delete()
    updated = datetime.now()
    db.session.add(Config(key=config_key, value=updated))
    db.session.commit()
    return update_interval


def update_chapters(series):
    """
    Get new chapters of the specified series. Returns the remaining seconds
    before the next update can occur.

    Every update occurs at least 1 hour after the previous update. If the
    previous update is within 1 hour ago, update will not occur.

    """
    update_interval = timedelta(hours=1)
    config_key = '{0}_chapters_updated'.format(series.id)
    u = Config.query.get(config_key)
    if u is not None:
        since_last_update = datetime.now() - u.value
        if since_last_update < update_interval:
            return int(since_last_update.total_seconds())
    current_last_chapter = series.chapters[0].id if series.chapters.count() else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    if not chapter_ids:
        # Nothing new
        return
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
            db.session.rollback()
            continue
    remove_cache(show_feed, series.id)
    Config.query.filter_by(key=config_key).delete()
    updated = datetime.now()
    db.session.add(Config(key=config_key, value=updated))
    db.session.commit()
    return update_interval


NUMERIC_DAYS = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
def fetch_series_ids():
    """Fetch series IDs and their update days and return a dictionary."""
    r = browser.open(NAVER_URLS['series_by_day'])
    series_ids = {}
    try:
        doc = lxml.html.fromstring(r.read())
    except AttributeError:
        return series_ids
    for url in doc.xpath('//*[@class="list_area daily_all"]//li//a[@class="title"]/@href'):
        m = re.search(r'titleId=(?P<id>\d+)&weekday=(?P<day>[a-z]+)', url)
        series_id, day = int(m.group('id')), m.group('day')
        series_ids.setdefault(series_id, []).append(NUMERIC_DAYS[day])
    return series_ids


def remove_cache(view_func, *args):
    cache.delete(view_func.cache_key.format(*args))


# Create tables for models
db.create_all()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
