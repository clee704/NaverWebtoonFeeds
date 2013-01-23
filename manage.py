#! /usr/bin/env python
from flask.ext.script import Manager, Shell, prompt_bool
from naverwebtoonfeeds import app, cache, db

manager = Manager(app)

db_manager = Manager()
manager.add_command('db', db_manager)

@db_manager.command
def create():
    """
    Create database tables. First check for the existence of each individual
    table, and if not found will issue the CREATE statements.

    """
    db.create_all()

@db_manager.command
def drop():
    """Drop all database tables."""
    try:
        if prompt_bool("Are you sure you want to lose all your data"):
            db.drop_all()
    except:
        pass

@db_manager.command
def fill():
    """Update database by fetching changes from Naver Comics."""
    from naverwebtoonfeeds.update import update_series_list
    list_updated, series_updated = update_series_list(update_all=True)
    if list_updated:
        cache.delete('feed_index')
    for series_id in series_updated:
        cache.delete('feed_show_%d' % series_id)
    addcompletedseries()

cache_manager = Manager()
manager.add_command('cache', cache_manager)

@cache_manager.command
def delete(target='index'):
    """
    Delete specified view cache. Call with the ID of the series to delete
    the view cache. If the target is not present or it is 'index', then the
    index view cache will be deleted. If the target is 'all', then all
    view caches will be deleted.

    """
    if target == 'index':
        cache.delete('feed_index')
    elif target == 'all':
        for series_id in db.session.query(Series.id):
            cache.delete('feed_show_%s' % series_id)
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
    from naverwebtoonfeeds.models import Series
    from naverwebtoonfeeds.update import add_completed_series
    add_completed_series()
    cache.delete('feed_index')

@manager.command
def runworker(burst=False):
    """Run the worker that fetches data from Naver and update the database."""
    from rq import Connection
    import rq
    from naverwebtoonfeeds import redis_connection
    from naverwebtoonfeeds.misc import heroku_scale
    with Connection(connection=redis_connection):
        w = rq.Worker([rq.Queue()], exc_handler=lambda job, *exc_info: False)
        w.work(burst=burst)
        if burst and app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
            heroku_scale('worker', 0)

@manager.shell
def make_shell_context():
    from naverwebtoonfeeds.models import Series, Chapter, Config
    return dict(app=app, cache=cache, db=db, Series=Series, Chapter=Chapter, Config=Config)

if __name__ == '__main__':
    manager.run()
