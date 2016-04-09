__author__ = 'ufarooqi'

import json
from db import db
from datetime import datetime, timedelta
from user import Domain, UserGroup, User
from candidate import Candidate


class TalentPool(db.Model):
    __tablename__ = 'talent_pool'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.TEXT)
    added_time = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_time = db.Column(db.DateTime, server_default=db.text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), nullable=False)

    # Relationships
    domain = db.relationship('Domain', backref=db.backref('talent_pool', cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('talent_pool', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<TalentPool (id = %r)>" % self.id

    def get_id(self):
        return unicode(self.id)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class TalentPoolCandidate(db.Model):
    __tablename__ = 'talent_pool_candidate'
    id = db.Column(db.Integer, primary_key=True)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'), nullable=False)
    added_time = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_time = db.Column(db.DateTime, server_default=db.text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), nullable=False)

    # Relationships
    candidate = db.relationship('Candidate', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<TalentPoolCandidate: (talent_pool_id = {})>".format(self.talent_pool_id)

    @classmethod
    def get(cls, candidate_id, talent_pool_id):
        return cls.query.filter_by(candidate_id=candidate_id, talent_pool_id=talent_pool_id).first()


class TalentPoolGroup(db.Model):
    __tablename__ = 'talent_pool_group'
    id = db.Column(db.Integer, primary_key=True)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id', ondelete='CASCADE'), nullable=False)
    user_group_id = db.Column(db.Integer, db.ForeignKey('user_group.Id', ondelete='CASCADE'), nullable=False)

    # Relationships
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pool_group', cascade="all, delete-orphan"))
    user_group = db.relationship('UserGroup', backref=db.backref('talent_pool_group', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<TalentPoolGroup: (talent_pool_id = {})>".format(self.talent_pool_id)

    @classmethod
    def get(cls, talent_pool_id, user_group_id):
        return cls.query.filter_by(talent_pool_id=talent_pool_id, user_group_id=user_group_id).first()

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
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'),  nullable=False)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id'), nullable=False)
    search_params = db.Column(db.String(1023))
    added_time = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_time = db.Column(db.TIMESTAMP, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                             nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('talent_pipeline', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pipeline', cascade="all, delete-orphan"))

    def get_id(self):
        return unicode(self.id)

    def get_email_campaigns(self, page=1, per_page=20):
        from candidate_pool_service.common.models.email_campaign import EmailCampaign, EmailCampaignSmartlist
        from candidate_pool_service.common.models.smartlist import Smartlist
        return EmailCampaign.query.join(EmailCampaignSmartlist).join(Smartlist).join(TalentPipeline).\
            filter(TalentPipeline.id == self.id).paginate(page=page, per_page=per_page, error_out=False).items

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self, include_stats=False, get_stats_function=None, include_growth=False, interval=None, get_growth_function=None):

        talent_pipeline = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'positions': self.positions,
            'search_params': json.loads(
                self.search_params) if self.search_params else None,
            'talent_pool_id': self.talent_pool_id,
            'date_needed': self.date_needed.isoformat() if self.date_needed else None,
            'added_time': self.added_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }
        if include_growth and interval and get_growth_function:
            talent_pipeline['growth'] = get_growth_function(self, int(interval))
        if include_stats and get_stats_function:
            # Include Last 30 days stats in response body
            to_date = datetime.utcnow() - timedelta(days=1)
            from_date = to_date - timedelta(days=29)
            talent_pipeline['stats'] = [] if self.added_time.date() == datetime.datetime.utcnow().date() else \
                get_stats_function(self, 'TalentPipeline', None, from_date.isoformat(), to_date.isoformat(), offset=0)

        return talent_pipeline

    @classmethod
    def get_by_user_and_talent_pool_id(cls, user_id, talent_pool_id):
        """
        This returns talent-pipeline object for particular user and talent_pool_id
        :param user_id: id of user object
        :param talent_pool_id: id of talent_pool object
        :rtype: TalentPipeline | None
        """
        assert user_id, 'user_id not provided'
        assert talent_pool_id, 'talent_pool_id not provided'
        return cls.query.filter_by(user_id=user_id, talent_pool_id=talent_pool_id).first()
