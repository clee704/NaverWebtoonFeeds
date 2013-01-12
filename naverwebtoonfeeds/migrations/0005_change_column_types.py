
import datetime
from flask import current_app
from flask.ext.evolution import BaseMigration
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(current_app)
db.metadata.bind = db.engine


class Migration(BaseMigration):
    def up(self):
        self.execute("ALTER TABLE series ALTER COLUMN title TYPE varchar(255);")
        self.execute("ALTER TABLE series ALTER COLUMN author TYPE varchar(255);")
        self.execute("ALTER TABLE series ALTER COLUMN thumbnail_url TYPE varchar(255);")
        self.execute("ALTER TABLE series ALTER COLUMN update_days TYPE varchar(31);")
        self.execute("ALTER TABLE series ALTER COLUMN last_update_status TYPE varchar(31);")
        self.execute("ALTER TABLE chapter ALTER COLUMN title TYPE varchar(255);")
        self.execute("ALTER TABLE chapter ALTER COLUMN thumbnail_url TYPE varchar(255);")

    def down(self):
        self.execute("ALTER TABLE series ALTER COLUMN title TYPE text;")
        self.execute("ALTER TABLE series ALTER COLUMN author TYPE text;")
        self.execute("ALTER TABLE series ALTER COLUMN thumbnail_url TYPE text;")
        self.execute("ALTER TABLE series ALTER COLUMN update_days TYPE text;")
        self.execute("ALTER TABLE series ALTER COLUMN last_update_status TYPE text;")
        self.execute("ALTER TABLE chapter ALTER COLUMN title TYPE text;")
        self.execute("ALTER TABLE chapter ALTER COLUMN thumbnail_url TYPE text;")
