#! /usr/bin/env python
# pylint: disable=import-error,no-name-in-module
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask.ext.script import Manager, prompt_bool

from naverwebtoonfeeds import create_app
from naverwebtoonfeeds.extensions import cache, db
from naverwebtoonfeeds.feeds.models import Series, Chapter, Config
from naverwebtoonfeeds.feeds.update import update_series_list, add_ended_series
from naverwebtoonfeeds.feeds.worker import run_worker


app = create_app()
manager = Manager(app)


@manager.shell
def make_shell_context():
    """Returns shell context with common objects and classes."""
    return dict(app=app, cache=cache, db=db, Series=Series, Chapter=Chapter, Config=Config)

@manager.command
def addendedseries():
    """
    Adds ended series to the database. They are not added in normal operation,
    though existing series will remain after it is ended.

    """
    add_ended_series()
    cache.delete('feed_index')

@manager.command
def runworker(burst=False):
    """Runs the worker that fetches data from Naver and update the database."""
    run_worker(burst)

@manager.command
def triggerupdate():
    c = Config.query.get('series_list_fetched')
    if not c:
        return
    c.value = datetime.utcnow() - timedelta(hours=1)
    db.session.commit()


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
    """
    Updates the database by fetching changes from Naver Comics.

    """
    list_updated, series_updated = update_series_list(update_all=True)
    if list_updated:
        cache.delete('feed_index')
    for series_id in series_updated:
        cache.delete('feed_show_%d' % series_id)


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


def main():
    manager.run()


if __name__ == '__main__':
    main()
