from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False, index=True)
    author = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    last_chapter = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False, index=True)
    thumbnail_url = db.Column(db.Text)
    update_days = db.Column(db.Text)

    new_chapters_available = db.Column(db.Boolean, default=False)
    last_update_status = db.Column(db.Text, nullable=False, default='')


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    pubdate = db.Column(db.DateTime, nullable=False)
    thumbnail_url = db.Column(db.Text)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('chapters', order_by=id.desc()))

    class DoesNotExist(Exception):
        pass
