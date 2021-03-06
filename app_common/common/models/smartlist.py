import json

from contracts import contract

from candidate import Candidate
from db import db
import datetime
from talent_pools_pipelines import TalentPipeline, TalentPool, TalentPoolCandidate


class Smartlist(db.Model):
    __tablename__ = 'smart_list'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(127))
    search_params = db.Column('SearchParams', db.TEXT)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    talent_pipeline_id = db.Column('talentPipelineId', db.Integer, db.ForeignKey('talent_pipeline.id'))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.utcnow)
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

    @classmethod
    @contract
    def get_by_ids(cls, smartlist_id, is_hidden=True):
        """
        This method returns candidates against list of Candidate Ids or single Candidate Id
        :param positive|list smartlist_id: Smartlist Id
        :param bool is_hidden: if True returns all candidates with hidden if False returns unhidden candidates
        :rtype: type(x)
        """
        if isinstance(smartlist_id, list):
            if not is_hidden:
                return cls.query.filter(cls.id.in_(smartlist_id), cls.is_hidden == 0).all()
            return cls.query.filter(cls.id.in_(smartlist_id)).all()
        return cls.query.filter_by(id=smartlist_id).first()

    def to_dict(self, include_stats=False, get_stats_function=None):
        smart_list = {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'is_hidden': self.is_hidden,
            'search_params': json.loads(self.search_params) if self.search_params else None,
            'added_time': self.added_time.isoformat() if self.added_time else None
        }
        if include_stats and get_stats_function:
            to_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            to_date = to_date.replace(hour=23, minute=59, second=59)
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

    @classmethod
    @contract
    def get_smartlist_ids_in_talent_pools(cls, user_id, talentpool_names=None):
        """
        This returns smartlist Ids in a pipeline which is in specified talentpool
        :param positive user_id: User Id
        :param list|None talentpool_names: Talent pool names
        :rtype: list
        """
        talent_pools = TalentPool.get_by_user_id_and_name(user_id, talentpool_names)
        talent_pool_ids = [talent_pool.id for talent_pool in talent_pools]  # Extracting data on 0th index from tuple
        candidate_ids = TalentPoolCandidate.query.with_entities(TalentPoolCandidate.candidate_id). \
            filter(TalentPoolCandidate.talent_pool_id.in_(talent_pool_ids)).distinct().all()
        """
        candidate_ids is a list of tuple
         [(358L,), (1005L,), (1054L,), (1055L,)]
        when we zip it "zip(*candidate_ids)". It makes pairs of 1st-to-1st and 2nd-to-2nd elements of tuples.
         Since second element is empty so it gets skipped and candidate_ids changes into
         [(358L, 1005L, 1054L, 1055L)]
         And then we use * to extract elements of list of tuple and pass them to list() function and receive
         [358L, 1005L, 1054L, 1055L]
        """
        candidate_ids = list(*zip(*candidate_ids))  # Converting tuple to list
        candidates = Candidate.get_by_id(candidate_ids, False)
        candidate_ids = [candidate.id for candidate in candidates]
        smartlist_ids = SmartlistCandidate.query.with_entities(SmartlistCandidate.smartlist_id). \
            filter(SmartlistCandidate.candidate_id.in_(candidate_ids)).distinct().all()
        smartlist_ids = [smartlist_id[0] for smartlist_id in smartlist_ids]  # Extracting data on 0th index from tuple
        # Checking if any of the selected smartlists is hidden
        smartlists = Smartlist.get_by_ids(smartlist_ids, False)
        smartlist_ids = [smartlist.id for smartlist in smartlists]
        return smartlist_ids
