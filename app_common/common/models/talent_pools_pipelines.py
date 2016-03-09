__author__ = 'ufarooqi'

from db import db
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

    # Relationships
    candidate = db.relationship('Candidate', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<TalentPoolCandidate: (talent_pool_id = {})>".format(self.talent_pool_id)

    @classmethod
    def get(cls, candidate_id, talent_pool_id):
        return cls.query.filter_by(candidate_id=candidate_id, talent_pool_id=talent_pool_id).first()


class TalentPoolStats(db.Model):
    __tablename__ = 'talent_pool_stats'
    id = db.Column(db.Integer, primary_key=True)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id', ondelete='CASCADE'), nullable=False)
    total_number_of_candidates = db.Column(db.Integer, nullable=False, default=0)
    candidates_engagement = db.Column(db.Integer, nullable=False, default=0)
    added_datetime = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)

    # Relationships
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pool_stats', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<TalentPoolStats (id = {})>".format(self.id)


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
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pipeline'))

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


