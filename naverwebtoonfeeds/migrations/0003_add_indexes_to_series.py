
import datetime
from flask import current_app
from flask.ext.evolution import BaseMigration
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(current_app)
db.metadata.bind = db.engine


class Migration(BaseMigration):
    def up(self):
        self.execute("CREATE INDEX title_idx on series (title asc);")
        self.execute("CREATE INDEX is_completed_idx on series (is_completed asc);")

    def down(self):
        self.execute("DROP INDEX title_idx on series;")
        self.execute("DROP INDEX is_completed_idx on series;")
