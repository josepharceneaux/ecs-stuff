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