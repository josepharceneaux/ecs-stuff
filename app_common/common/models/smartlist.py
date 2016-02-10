from db import db
import datetime
from talent_pools_pipelines import TalentPipeline


class Smartlist(db.Model):
    __tablename__ = 'smart_list'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(127))
    search_params = db.Column('SearchParams', db.String(1023))
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    talent_pipeline_id = db.Column('talentPipelineId', db.Integer, db.ForeignKey('talent_pipeline.id'))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    is_hidden = db.Column('isHidden', db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('smart_list', cascade="all, delete-orphan"))
    talent_pipeline = db.relationship('TalentPipeline', backref=db.backref('smart_list'))

    def delete(self):
        """Hide smartlist"""
        # TODO: if smartlist exists in email campaign do not allow to delete.
        # [Ask for active and completed campaign] [Ask for SMS campaign or other campaigns]
        self.is_hidden = True
        db.session.commit()

    def __repr__(self):
        return "<Smartlist(name= %r)>" % self.name


class SmartlistCandidate(db.Model):
    __tablename__ = 'smart_list_candidate'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column('SmartlistId', db.Integer, db.ForeignKey('smart_list.Id', ondelete='CASCADE'),
                             nullable=False)
    candidate_id = db.Column('CandidateId', db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'),
                             nullable=False)
    added_time = db.Column('AddedTime', db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    updated_time = db.Column('UpdatedTime', db.DateTime,
                             server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                             nullable=False)

    # Relationships
    smartlist = db.relationship('Smartlist', backref=db.backref('smart_list_candidate',
                                                                cascade="all, delete-orphan"))
    candidate = db.relationship('Candidate', backref=db.backref('smart_list_candidate',
                                                                cascade="all, delete-orphan"))

    def __repr__(self):
        return "<SmartListCandidate> (id = {})".format(self.id)


class SmartlistStats(db.Model):
    __tablename__ = 'smartlist_stats'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey('smart_list.Id', ondelete='CASCADE'), nullable=False)
    total_candidates = db.Column(db.Integer, nullable=False, default=0)
    number_of_candidates_removed_or_added = db.Column(db.Integer, nullable=False, default=0)
    candidates_engagement = db.Column(db.Integer, nullable=False, default=0)
    added_datetime = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), nullable=False)

    # Relationships
    smart_list = db.relationship('Smartlist', backref=db.backref('smartlist_stats', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<SmartListStats (id = {})>".format(self.id)
