#! /usr/bin/env python
from flask.ext.script import Manager, prompt_bool
from naverwebtoonfeeds import app

manager = Manager(app)

db_manager = Manager()
manager.add_command('db', db_manager)

@db_manager.command
def create():
    """
    Create database tables. First check for the existence of each individual
    table, and if not found will issue the CREATE statements.

    """
    from naverwebtoonfeeds import db
    db.create_all()

@db_manager.command
def drop():
    """Drop all database tables."""
    from naverwebtoonfeeds import db
    try:
        if prompt_bool("Are you sure you want to lose all your data"):
            db.drop_all()
    except:
        pass

@db_manager.command
def fill():
    """Update database by fetching changes from Naver Comics."""
    from naverwebtoonfeeds import cache
    from naverwebtoonfeeds.lib.updater import update_series_list
    list_updated, series_updated = update_series_list(update_all=True)
    if list_updated:
        cache.delete('feed_index')
    for series_id in series_updated:
        cache.delete('feed_show_%d' % series_id)
    add_completed_series()

cache_manager = Manager()
manager.add_command('cache', cache_manager)

@cache_manager.command
def delete(target='index'):
    """
    Delete specified view cache. Call with the ID of the series to delete
    the view cache. If the target is not present or it is 'index', then the
    index view cache will be deleted.

    """
    from naverwebtoonfeeds import cache
    if target == 'index':
        cache.delete('feed_index')
    else:
        cache.delete('feed_show_%s' % target)

@manager.command
def migrate(action):
    from flask.ext.evolution import Evolution
    evolution = Evolution(app)
    evolution.manager(action)

@manager.command
def addcompletedseries():
    """Add completed series."""
    from naverwebtoonfeeds import cache, db
    from naverwebtoonfeeds.models import Series
    from naverwebtoonfeeds.lib.updater import __browser__, update_series
    completed_series_ids = set(data['id'] for data in __browser__.get_completed_series())
    existing_series_ids = set(row[0] for row in db.session.query(Series.id))
    for series_id in completed_series_ids - existing_series_ids:
        series = Series(id=series_id)
        series.new_chapters_available = True
        update_series(series)
    cache.delete('feed_index')

if __name__ == '__main__':
    manager.run()
