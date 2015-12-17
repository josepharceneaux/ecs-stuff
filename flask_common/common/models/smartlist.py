from db import db
import datetime
from candidate import Candidate
from sqlalchemy.orm import relationship, backref

__author__ = 'jitesh'


class Smartlist(db.Model):
    __tablename__ = 'smart_list'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(127))
    search_params = db.Column('searchParams', db.String(1023))
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    is_hidden = db.Column('isHidden', db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('smart_list', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<Smartlist(name= %r)>" % self.name


class SmartlistCandidate(db.Model):
    __tablename__ = 'smart_list_candidate'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column('SmartlistId', db.Integer, db.ForeignKey('smart_list.id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'), nullable=False)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

    smart_list = db.relationship('Smartlist', backref=db.backref('smart_list_candidate', cascade="all, delete-orphan"))
    candidate = db.relationship('Candidate', backref=db.backref('smart_list_candidate', cascade="all, delete-orphan"))
