# -*- coding: UTF-8 -*-
from datetime import datetime

from flask import url_for

from naverwebtoonfeeds.ext import cache
from naverwebtoonfeeds.feeds.helpers import feed_cache_key, index_cache_key
from naverwebtoonfeeds.feeds.models import Chapter, Series
from naverwebtoonfeeds.filters import externalize_filter


def test_index_with_empty_db(app, db):
    with app.test_client() as client:
        d = client.get('/').doc
        assert cache.get(index_cache_key()) is not None
        assert d.cssselect('.no-feeds')[0].text == u'구독할 수 있는 웹툰이 없습니다.'
        assert d.cssselect('.series') == []


def test_index_with_series(app, db):
    with app.test_client() as client:
        db.session.add(Series(
            id=1,
            title='Peanuts',
            author='Charles M. Schulz'))
        db.session.add(Series(
            id=2,
            title="Alice's Adventures in Wonderland",
            author='Lewis Carroll',
            description='A girl named Alice falls down a rabbit hole into a '
                        'fantasy world.'))
        db.session.commit()

        d = client.get('/').doc
        a1 = d.cssselect('#series-1')[0]
        assert a1.cssselect('.series-title a')[0].text.strip() == 'Peanuts'
        assert a1.cssselect('.series-author')[0].text == 'Charles M. Schulz'

        a2 = d.cssselect('#series-2')[0]
        assert (a2.cssselect('.series-title a')[0].text.strip() ==
                "Alice's Adventures in Wonderland")
        assert a2.cssselect('.series-author')[0].text == 'Lewis Carroll'
        assert (a2.cssselect('.series-description')[0].text ==
                'A girl named Alice falls down a rabbit hole into a fantasy '
                'world.')
        assert d.cssselect('.no-feeds') == []
        assert len(d.cssselect('.series')) == 2
        assert ([e.attrib['id'] for e in d.cssselect('.series')] ==
                ['series-2', 'series-1']), 'Series should be sorted by title.'
        assert (a1.cssselect('.series-feed-url input')[0].attrib['value'] ==
                externalize_filter(url_for('feeds.show', series_id=1)))


def test_show_with_chapters(app, db):
    with app.test_client() as client:
        db.session.add(Series(
            id=1, title='Peanuts', author='Charles M. Schulz'))
        db.session.add(Chapter(
            id=1,
            title='Strip #1',
            pubdate=datetime(1950, 10, 2),
            atom_id='atom1',
            series_id=1))
        db.session.add(Chapter(
            id=2,
            title='Strip #2',
            pubdate=datetime(1950, 10, 3),
            atom_id='atom2',
            series_id=1))
        db.session.commit()

        d = client.get('/feeds/1.xml').doc
        ns = {'a': 'http://www.w3.org/2005/Atom'}

        assert cache.get(feed_cache_key(1)) is not None
        assert d.xpath('a:title/text()', namespaces=ns) == ['Peanuts']
        assert (d.xpath('a:author/a:name/text()', namespaces=ns) ==
                ['Charles M. Schulz'])
        assert d.xpath('count(a:entry)', namespaces=ns) == 2
        assert (d.xpath('a:entry/a:id/text()', namespaces=ns) ==
                ['atom2', 'atom1'])
