#! /usr/bin/env python
from flask.ext.script import Manager
from naverwebtoonfeeds import app

manager = Manager(app)

@manager.command
def db_create_all():
    """
    Create database tables. First check for the existence of each individual
    table, and if not found will issue the CREATE statements.

    """
    from naverwebtoonfeeds import db
    db.create_all()

@manager.command
def db_drop_all():
    """Drop all database tables."""
    try:
        db.drop_all()
    except:
        pass

@manager.command
def update():
    """Update database by fetching changes from Naver Comics."""
    from naverwebtoonfeeds import cache
    from naverwebtoonfeeds.lib.updater import update_series_list
    list_updated, series_updated = update_series_list(update_all=True)
    if list_updated:
        cache.delete('feed_index')
    for series_id in series_updated:
        cache.delete('feed_show_%d' % series_id)
    add_completed_series()

@manager.command
def add_completed_series():
    """Add completed series."""
    from naverwebtoonfeeds import db
    from naverwebtoonfeeds.models import Series
    from naverwebtoonfeeds.lib.updater import __browser__, update_series
    completed_series_ids = set(data['id'] for data in __browser__.get_completed_series())
    existing_series_ids = set(row[0] for row in db.session.query(Series.id))
    for series_id in completed_series_ids - existing_series_ids:
        series = Series(id=series_id)
        series.new_chapters_available = True
        update_series(series)
    cache.delete('feed_index')

@manager.command
def delete_cache(target='index'):
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

if __name__ == '__main__':
    manager.run()
