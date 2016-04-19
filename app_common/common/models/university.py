import datetime
from db import db


class University(db.Model):
    __tablename__ = 'university'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(255))
    state_id = db.Column('StateId', db.Integer, db.ForeignKey('state.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<University (name=' %r')>" % self.name
