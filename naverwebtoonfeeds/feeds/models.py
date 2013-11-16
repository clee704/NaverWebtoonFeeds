import pytz

from ..extensions import db
from .constants import NAVER_TIMEZONE


class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    last_chapter = db.Column(db.Integer, nullable=False, default=0)
    is_completed = db.Column(db.Boolean, nullable=False, default=False, index=True)
    thumbnail_url = db.Column(db.String(255))
    upload_days = db.Column(db.String(31))

    new_chapters_available = db.Column(db.Boolean, default=False)
    last_upload_status = db.Column(db.String(31), nullable=False, default='')
    retries_left = db.Column(db.Integer, nullable=False, default=0)


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    pubdate = db.Column(db.DateTime, nullable=False)
    thumbnail_url = db.Column(db.String(255))
    atom_id = db.Column(db.String(255), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), primary_key=True)
    series = db.relationship('Series', backref=db.backref('chapters', order_by=id.desc()))

    @property
    def pubdate_with_tz(self):
        return pytz.utc.localize(self.pubdate).astimezone(NAVER_TIMEZONE)


# TODO rename (candidates: Variable, Value, State, Status, ...)
class Config(db.Model):
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.PickleType)
