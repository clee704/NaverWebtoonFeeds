# -*- coding: UTF-8 -*-
from datetime import datetime

from flask import url_for
import lxml.html

from tests import TestCase
from ..util import patch
from naverwebtoonfeeds.feeds.models import Series, Chapter
from naverwebtoonfeeds.feeds.render import permanent_cache, render_feed_index, render_feed_show
from naverwebtoonfeeds.extensions import db
from naverwebtoonfeeds.template import externalize


class TestRender(TestCase):

    @patch('naverwebtoonfeeds.feeds.render.cache')
    def test_render_feed_index_without_series(self, mock_cache):
        response = render_feed_index()
        doc = lxml.html.fromstring(response)
        mock_cache.set.assert_called_with('feed_index', response, permanent_cache())
        self.assertIn(u'구독할 수 있는 웹툰이 없습니다.', response)
        self.assertEqual([], doc.xpath('//article'))

    @patch('naverwebtoonfeeds.feeds.render.cache')
    def test_render_feed_index_with_series(self, mock_cache):
        db.session.add(Series(id=1, title='Peanuts', author='Charles M. Schulz'))
        db.session.add(Series(id=2, title="Alice's Adventures in Wonderland", author='Lewis Carroll',
                description='A girl named Alice falls down a rabbit hole into a fantasy world.'))
        db.session.commit()
        response = render_feed_index()
        doc = lxml.html.fromstring(response)

        mock_cache.set.assert_called_with('feed_index', response, permanent_cache())
        self.assertIn('Peanuts', response)
        self.assertIn('Charles M. Schulz', response)
        self.assertIn("Alice&#39;s Adventures in Wonderland", response)
        self.assertIn('Lewis Carroll', response)
        self.assertIn('A girl named Alice falls down a rabbit hole into a fantasy world.', response)
        self.assertNotIn(u'구독할 수 있는 웹툰이 없습니다.', response)
        self.assertEqual(doc.xpath('count(//article)'), 2)
        self.assertEqual(doc.xpath('//article/attribute::id'), ['series-2', 'series-1'],
                "Series should be sorted by title.")
        self.assertIn(externalize(url_for('feeds.show', series_id=1)),
                doc.xpath('//article//a/attribute::href'))

    @patch('naverwebtoonfeeds.feeds.render.cache')
    def test_render_feed_show_with_chapters(self, mock_cache):
        db.session.add(Series(id=1, title='Peanuts', author='Charles M. Schulz'))
        db.session.add(Chapter(id=1, title='Strip #1', pubdate=datetime(1950, 10, 2), atom_id='atom1', series_id=1))
        db.session.add(Chapter(id=2, title='Strip #2', pubdate=datetime(1950, 10, 3), atom_id='atom2', series_id=1))
        db.session.commit()
        response = render_feed_show(Series.query.get(1))
        doc = lxml.html.fromstring(response.data)

        mock_cache.set.assert_called_with('feed_show_1', response, permanent_cache())
        self.assertEqual(doc.xpath('//feed/title/text()'), ['Peanuts'])
        self.assertEqual(doc.xpath('//feed/author/name/text()'), ['Charles M. Schulz'])
        self.assertEqual(doc.xpath('count(//entry)'), 2)
        self.assertEqual(doc.xpath('//entry/id/text()'), ['atom2', 'atom1'])
