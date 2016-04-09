import json
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
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.utcnow())
    is_hidden = db.Column('isHidden', db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('smart_list', cascade="all, delete-orphan"))
    talent_pipeline = db.relationship('TalentPipeline', backref=db.backref('smart_list', cascade="all, delete-orphan"))

    def delete(self):
        """Hide smartlist"""
        # TODO: if smartlist exists in email campaign do not allow to delete.
        # [Ask for active and completed campaign] [Ask for SMS campaign or other campaigns]
        self.is_hidden = True
        db.session.commit()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.id)

    def to_dict(self, include_stats=False, get_stats_function=None):
        smart_list = {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'is_hidden': self.is_hidden,
            'search_params': json.loads(self.search_params) if self.search_params else None,
            'added_time': str(self.added_time)
        }
        if include_stats and get_stats_function:
            to_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            from_date = to_date - datetime.timedelta(days=29)
            smart_list['stats'] = [] if self.added_time.date() == datetime.datetime.utcnow().date() else \
                get_stats_function(self, 'SmartList', None, from_date.isoformat(), to_date.isoformat(), offset=1)

        return smart_list


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
