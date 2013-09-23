#! /usr/bin/env python
from flask.ext.script import Manager, Shell, prompt_bool
from naverwebtoonfeeds import create_app
from naverwebtoonfeeds.extensions import cache, db
from naverwebtoonfeeds.feeds.browser import BrowserException


app = create_app()
manager = Manager(app)


@manager.shell
def make_shell_context():
    """Returns shell context with common objects and classes."""
    from naverwebtoonfeeds.feeds.models import Series, Chapter, Config
    return dict(app=app, cache=cache, db=db, Series=Series, Chapter=Chapter, Config=Config)

@manager.command
def addcompletedseries():
    """Adds completed series."""
    from naverwebtoonfeeds.feeds.models import Series
    from naverwebtoonfeeds.feeds.update import add_completed_series
    add_completed_series()
    cache.delete('feed_index')

@manager.command
def runworker(burst=False):
    """Runs the worker that fetches data from Naver and update the database."""
    try:
        import rq
        from naverwebtoonfeeds.extensions import redis_connection
        from naverwebtoonfeeds.feeds.util import heroku_scale
        with rq.Connection(connection=redis_connection):
            w = rq.Worker([rq.Queue()])
            # Remove default exception handler that moves job to failed queue
            w.pop_exc_handler()
            w.work(burst=burst)
    finally:
        if burst and app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
            heroku_scale('worker', 0)


db_manager = Manager()
manager.add_command('db', db_manager)

@db_manager.command
def create():
    """
    Creates database tables. First check for the existence of each individual
    table, and if not found will issue the CREATE statements.

    """
    db.create_all()

@db_manager.command
def drop():
    """Drops all database tables."""
    try:
        if prompt_bool("Are you sure you want to lose all your data"):
            db.drop_all()
    except:
        pass

@db_manager.command
def fill():
    """Updates database by fetching changes from Naver Comics."""
    from naverwebtoonfeeds.feeds.update import update_series_list
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
    Deletes specified view cache. Call with the ID of the series to delete
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


if __name__ == '__main__':
    manager.run()
