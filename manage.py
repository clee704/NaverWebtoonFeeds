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
    from naverwebtoonfeeds.lib.updater import update_all
    update_all()

if __name__ == '__main__':
    manager.run()
