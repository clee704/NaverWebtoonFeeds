"""
    naverwebtoonfeeds.commands
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines command line tasks.

"""
from __future__ import print_function

import logging.config
import sys
from datetime import timedelta

from flask import current_app, g
from flask_assets import ManageAssets
from flask_script import Manager, prompt_bool
from flask_script.commands import Server, Shell, ShowUrls

from ..ext import assets_env, cache, db
from ..feeds.crawler import Crawler
from ..feeds.helpers import feed_cache_key, index_cache_key
from ..feeds.models import Chapter, Series
from ..feeds.worker import run_worker
from .base import Manager


db_manager = Manager(help='run commands for database')


@db_manager.command
def create():
    """create tables in the database"""
    db.create_all()


@db_manager.command
def drop(yes=False):
    """drop all database tables"""
    try:
        if yes or prompt_bool("Are you sure you want to lose all your data"):
            db.drop_all()
    except KeyboardInterrupt:
        pass


@db_manager.command
def reset(yes=False):
    """drop and creates all database tables; shortcut for 'drop' then 'create'
    """
    drop(yes)
    create()


cache_manager = Manager(help='run commands for cache')


@cache_manager.command
def delete(target='index'):
    """delete specified view cache; 'index' removes the index page; otherwise
    it is assumed to be a series key and the feed page for that series is
    removed

    """
    if target == 'index':
        cache.delete(index_cache_key())
    else:
        cache.delete(feed_cache_key(target))


@cache_manager.command
def clear():
    """clear the cache"""
    cache.clear()


asset_manager = ManageAssets(assets_env)
asset_manager.help = 'run commands for assets'


def _shell_context():
    return dict(current_app=current_app, g=g, db=db, cache=cache,
                Series=Series, Chapter=Chapter)

shell_command = Shell(make_context=_shell_context)
shell_command.help = 'run a Python shell inside the Flask app context'


server_command = Server()
server_command.help = 'run the Flask development server i.e. app.run()'


routes_command = ShowUrls()
routes_command.help = 'print all of the URL mathcing routes for the project'


manager = Manager()
manager.add_command('db', db_manager)
manager.add_command('cache', cache_manager)
manager.add_command('assets', asset_manager)
manager.add_command('serve', server_command)
manager.add_command('shell', shell_command)
manager.add_command('routes', routes_command)


@manager.command
def update():
    """update the database by fetching changes from the Naver Comics website"""
    crawler = Crawler()
    crawler.update_series_list(update_all=True)


@manager.command
def updateseries(series_id):
    """update the specified series by fetching changes from the Naver Comics
    website"""
    crawler = Crawler()
    series = Series.query.get(series_id)
    if series:
        crawler.update_series(series)
    else:
        print('Series #{} does not exist'.format(series_id), file=sys.stderr)


@manager.command
def addendedseries():
    """add ended series to the database which may not exist in the database
    because they were ended before the database is constructed

    """
    crawler = Crawler()
    crawler.add_ended_series()


@manager.command
def runworker(burst=False):
    """run the worker that processes jobs in the queue"""
    run_worker(burst)


@manager.command
def triggerupdate():
    fetched = cache.get('series_list_fetched')
    if fetched is not None:
        cache.set_permanently('series_list_fetched',
                              fetched - timedelta(hours=1))
