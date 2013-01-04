
import datetime
from flask import current_app
from flask.ext.evolution import BaseMigration
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(current_app)
db.metadata.bind = db.engine


class Migration(BaseMigration):
    def up(self):
        self.execute("ALTER TABLE series DROP COLUMN last_update_status;")
        self.execute("ALTER TABLE series ADD COLUMN last_update_status text default '' not null;")

    def down(self):
        self.execute("ALTER TABLE series DROP COLUMN last_update_status;")
        self.execute("ALTER TABLE series ADD COLUMN last_update_status boolean default false not null;")
