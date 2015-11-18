__author__ = 'basit'

import datetime

from db import db


class SmartList(db.Model):
    __tablename__ = 'smart_list'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(127))
    user_id = db.Column('UserId', db.Integer, db.ForeignKey("user.id"), nullable=False)
    search_params = db.Column('SearchParams', db.String(1023))
    candidate_count = db.Column('CandidateCount', db.Integer)
    is_hidden = db.Column('IsHidden', db.Integer)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return '<SmartList (id = %r)>' % self.id

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id
        return cls.query.filter(
            db.and_(
                cls.user_id == user_id,
            )
        ).all()


class SmartListCandidate(db.Model):
    __tablename__ = 'smart_list_candidate'
    id = db.Column(db.Integer, primary_key=True)
    smart_list_id = db.Column('SmartListId', db.Integer, db.ForeignKey("smart_list.id"), nullable=False)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return '<SmartListCandidate (id = %r)>' % self.id

    @classmethod
    def get_by_smart_list_id(cls, smart_list_id):
        assert smart_list_id
        return cls.query.filter(
            db.and_(
                cls.smart_list_id == smart_list_id,
            )
        ).all()