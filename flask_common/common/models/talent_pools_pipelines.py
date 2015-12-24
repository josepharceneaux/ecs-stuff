__author__ = 'ufarooqi'

import datetime
from db import db
from user import Domain, UserGroup, User
from candidate import Candidate


class TalentPool(db.Model):

    __tablename__ = 'talent_pool'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id', ondelete='CASCADE'), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),  nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.TEXT)
    added_time = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_time = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                             nullable=False)

    domain = db.relationship('Domain', backref=db.backref('talent_pool', cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('talent_pool', cascade="all, delete-orphan"))

    def get_id(self):
        return unicode(self.id)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class TalentPoolCandidate(db.Model):

    __tablename__ = 'talent_pool_candidate'

    id = db.Column(db.Integer, primary_key=True)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'), nullable=False)

    candidate = db.relationship('Candidate', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))


class TalentPoolGroup(db.Model):

    __tablename__ = 'talent_pool_group'

    id = db.Column(db.Integer, primary_key=True)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id', ondelete='CASCADE'), nullable=False)
    user_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id', ondelete='CASCADE'), nullable=False)

    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pool_group', cascade="all, delete-orphan"))
    user_group = db.relationship('UserGroup', backref=db.backref('talent_pool_group', cascade="all, delete-orphan"))

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class TalentPipeline(db.Model):

    __tablename__ = 'talent_pipeline'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.TEXT)
    positions = db.Column(db.Integer, default=1, nullable=False)
    date_needed = db.Column(db.DateTime, nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),  nullable=False)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id'), nullable=False)
    search_params = db.Column(db.String(1023))
    added_time = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_time = db.Column(db.TIMESTAMP, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                             nullable=False)

    user = db.relationship('User', backref=db.backref('talent_pipeline', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pipeline'))

    def get_id(self):
        return unicode(self.id)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Smartlist(db.Model):

    __tablename__ = 'smart_list'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(127))
    search_params = db.Column('searchParams', db.String(1023))
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    talent_pipeline_id = db.Column('talentPipelineId', db.Integer, db.ForeignKey('talent_pipeline.id'))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    is_hidden = db.Column('isHidden', db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('smart_list', cascade="all, delete-orphan"))
    talent_pipeline = db.relationship('TalentPipeline', backref=db.backref('smart_list'))

    def __repr__(self):
        return "<Smartlist(name= %r)>" % self.name

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id
        return cls.query.filter(
            db.and_(
                cls.user_id == user_id,
            )
        ).all()


class SmartlistCandidate(db.Model):

    __tablename__ = 'smart_list_candidate'

    id = db.Column(db.Integer, primary_key=True)
    smart_list_id = db.Column('SmartlistId', db.Integer, db.ForeignKey('smart_list.id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'), nullable=False)
    added_time = db.Column('AddedTime', db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    updated_time = db.Column('UpdatedTime', db.DateTime,
                             server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), nullable=False)

    smart_list = db.relationship('Smartlist', backref=db.backref('smart_list_candidate', cascade="all, delete-orphan"))
    candidate = db.relationship('Candidate', backref=db.backref('smart_list_candidate', cascade="all, delete-orphan"))

    @classmethod
    def get_by_smart_list_id(cls, smart_list_id):
        assert smart_list_id
        return cls.query.filter(
            db.and_(
                cls.smart_list_id == smart_list_id,
            )
        ).all()

