#! /usr/bin/env python
from flask.ext.script import Manager
from naverwebtoonfeeds import app

manager = Manager(app)

@manager.command
def resetdb():
    """Delete all tables (if any) in the database and recreate them."""
    from naverwebtoonfeeds import db
    try:
        db.drop_all()
    except:
        pass
    db.create_all()

@manager.command
def update(debug=False):
    """Update database by fetching changes from Naver Comics."""
    if debug:
        app.config['DEBUG'] = True
    from naverwebtoonfeeds import cache
    from naverwebtoonfeeds.lib.updater import update_series_list
    list_updated, series_updated = update_series_list(update_all=True)
    if list_updated:
        cache.delete('feed_index')
    for series_id in series_updated:
        cache.delete('feed_show_%d' % series_id)

@manager.command
def migrate(action):
    from flask.ext.evolution import Evolution
    evolution = Evolution(app)
    evolution.manager(action)

if __name__ == '__main__':
    manager.run()
