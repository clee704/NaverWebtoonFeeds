from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    last_chapter = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    thumbnail_url = db.Column(db.Text)


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    pubdate = db.Column(db.DateTime, nullable=False)
    thumbnail_url = db.Column(db.Text)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('chapters', order_by=id.desc()))

    class DoesNotExist(Exception):
        pass


class UpdateDay(db.Model):
    day = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('updatedays'))
