__author__ = 'ufarooqi'

from contracts import contract
import json
from db import db
from datetime import datetime, timedelta
from user import Domain, UserGroup, User
from candidate import Candidate
from ..error_handling import NotFoundError
from ..utils.talentbot_utils import OWNED
# 3rd party imports
from sqlalchemy import or_, and_, extract
from sqlalchemy.dialects.mysql import TINYINT


class TalentPool(db.Model):
    __tablename__ = 'talent_pool'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    simple_hash = db.Column(db.String(8))
    description = db.Column(db.TEXT)
    added_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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

    @classmethod
    @contract
    def get_talent_pools_in_user_domain(cls, user_id, page_number=None):
        """
        This method returns whether all talent pools or 10 talent pools according to page number in a user's domain
        :param None|positive page_number: Page number for returning limited number of records
        :param int|long user_id: User Id
        :rtype: list
        """
        domain_id = User.get_domain_id(user_id)
        if page_number is None:
            return cls.query.filter(cls.domain_id == domain_id).all()
        number_of_records = 10
        start = (page_number - 1) * number_of_records
        end = page_number * number_of_records
        return cls.query.filter(cls.domain_id == domain_id)[start:end]

    @classmethod
    @contract
    def get_by_user_id_and_name(cls, user_id, names):
        """
        This returns TalentPool list against names if no names are specified it returns all talent pools in usr domain
        :param positive user_id: User Id
        :param list|None names: Talentpool names or None
        :rtype: list
        """
        domain_id = User.get_domain_id(user_id)
        if names is not None:
            return cls.query.join(User).filter(cls.name.in_(names), User.domain_id == domain_id).all()
        return cls.query.join(User).filter(User.domain_id == domain_id).all()

    @classmethod
    @contract
    def get_talent_pool_owned_by_user(cls, user_id):
        """
        This returns Talentpool names owend by a user
        :param positive user_id: User Id
        :rtype: list
        """
        return cls.query.with_entities(cls.name).filter(cls.user_id == user_id).all()


class TalentPoolCandidate(db.Model):
    __tablename__ = 'talent_pool_candidate'
    id = db.Column(db.Integer, primary_key=True)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'), nullable=False)
    added_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    candidate = db.relationship('Candidate', backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool',
                                  backref=db.backref('talent_pool_candidate', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<TalentPoolCandidate: (talent_pool_id = {})>".format(self.talent_pool_id)

    @classmethod
    def get(cls, candidate_id, talent_pool_id):
        return cls.query.filter_by(candidate_id=candidate_id, talent_pool_id=talent_pool_id).first()

    @classmethod
    @contract
    def candidate_imports(cls, user_id, user_name=None, talent_pool_list=None, user_specific_date=None):
        """
        Returns number of candidate added by a user in a talent pool during a specific time interval
        :param string|None user_name: User name
        :param int|long user_id: User Id
        :param list|None talent_pool_list: Talent pool name
        :param datetime|None|string user_specific_date: Datetime this should be later than or equal to updated_time
        or added_time
        :rtype: int|long|string
        """
        user = None
        if user_name:
            if user_name.lower() == 'i':
                first_name = User.filter_by_keywords(id=user_id)[0].first_name
                last_name = User.filter_by_keywords(id=user_id)[0].last_name
                user_name = first_name if first_name else last_name
                if user_name is None:
                    raise NotFoundError
            domain_id = User.get_domain_id(user_id)
            users = User.get_by_domain_id_and_name(domain_id, user_name)
            if users:
                user = users[0]
            else:
                raise NotFoundError
        if user_name is None:
            user = User.get_by_id(user_id)
            if user is None:
                raise NotFoundError
        # Joining talent_pool table and talent_pool_candidate table on basis of Id.
        common_query = cls.query.filter(cls.talent_pool_id == TalentPool.id, Candidate.id ==
                                        TalentPoolCandidate.candidate_id, Candidate.is_web_hidden == 0)
        if isinstance(user_specific_date, datetime):
            # User's specified time should be smaller or equal to the time when candidate was added or updated
            common_query = common_query.filter(or_((cls.added_time >= user_specific_date),
                                                   (cls.updated_time >= user_specific_date)))
        if isinstance(user_specific_date, basestring):
            # User's specified year equal to the year when candidate was added or updated
            common_query = common_query.filter(or_((extract("year", cls.added_time) == user_specific_date),
                                                   (extract("year", cls.updated_time) == user_specific_date)))
        if user_name and talent_pool_list:
            # Querying how many candidates have user added in specified talent pools
            # TODO: Join, count ?
            return common_query.filter(
                and_(TalentPool.user_id == User.id, TalentPool.name.in_(talent_pool_list)),
                Candidate.user_id == user.id).distinct().count()
        if user_name and talent_pool_list is None:
            # Querying how many candidates have user added in his talent pools
            return common_query.filter(TalentPool.user_id == User.id, Candidate.id == TalentPoolCandidate.candidate_id,
                                       Candidate.user_id == user.id).distinct().count()
        if talent_pool_list and user_name is None:
            # Querying how many candidates user have added in his all talent pools
            return common_query.filter(and_(TalentPool.name.in_(talent_pool_list),
                                            TalentPool.domain_id == user.domain_id)).distinct().count()
        if talent_pool_list is None and user_name is None:
            # Querying how many candidates have been added in a domain's talent pools by all users
            return common_query.filter(TalentPool.domain_id == user.domain_id).distinct().count()
        return "Something went wrong cant find any imports"  # TODO Raise


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
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.TEXT)
    positions = db.Column(db.Integer, default=1, nullable=False)
    date_needed = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'), nullable=False)
    talent_pool_id = db.Column(db.Integer, db.ForeignKey('talent_pool.id'), nullable=False)
    search_params = db.Column(db.TEXT)
    is_hidden = db.Column(TINYINT, default='0', nullable=False)
    added_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow,
                             nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('talent_pipeline', cascade="all, delete-orphan"))
    talent_pool = db.relationship('TalentPool', backref=db.backref('talent_pipeline', cascade="all, delete-orphan"))

    def __repr__(self):
        return "TalentPipeline (id = {})".format(self.id)

    def get_id(self):
        return unicode(self.id)

    @classmethod
    @contract
    def get_own_or_domain_pipelines(cls, user_id, scope, page_number=None):
        """
        This returns list of Pipelines owned by a specific user or all in domain
        :param positive|None page_number: Page number for limiting number of rows returned
        :param positive user_id: User Id
        :param int scope: Weather owned or domain specific
        :rtype: list
        """
        if scope == OWNED:
            query_object = cls.query.join(User).filter(User.id == user_id, cls.is_hidden == 0)
        else:
            domain_id = User.get_domain_id(user_id)
            query_object = cls.query.join(User).filter(User.domain_id == domain_id, cls.is_hidden == 0)
        if page_number is None:
            return query_object.all()
        number_of_records = 10
        start = (page_number - 1) * number_of_records
        end = page_number * number_of_records
        return query_object[start:end]

    @classmethod
    def get_by_user_id_in_desc_order(cls, user_id):
        """
        Returns a list of TalentPipelines ordered by their creation time
        :type user_id:  int | long
        :rtype:  list[TalentPipeline]
        """
        return cls.query.filter_by(user_id=user_id).order_by(cls.added_time.desc()).all()

    def get_email_campaigns(self, page=1, per_page=20):
        from candidate_pool_service.common.models.email_campaign import EmailCampaign, EmailCampaignSmartlist
        from candidate_pool_service.common.models.smartlist import Smartlist
        return EmailCampaign.query.distinct(EmailCampaign.id).join(EmailCampaignSmartlist).join(Smartlist). \
            join(TalentPipeline).filter(TalentPipeline.id == self.id).paginate(page=page, per_page=per_page,
                                                                               error_out=False).items

    def get_email_campaigns_count(self):
        from candidate_pool_service.common.models.email_campaign import EmailCampaign, EmailCampaignSmartlist
        from candidate_pool_service.common.models.smartlist import Smartlist
        return EmailCampaign.query.distinct(EmailCampaign.id).join(EmailCampaignSmartlist).join(Smartlist).\
            join(TalentPipeline).filter(TalentPipeline.id == self.id).count()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self, include_stats=False, get_stats_function=None, include_growth=False, interval=None,
                get_growth_function=None, include_candidate_count=False, get_candidate_count=None,
                email_campaign_count=False):

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
            'is_hidden': self.is_hidden,
            'added_time': self.added_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }
        if email_campaign_count:
            talent_pipeline['total_email_campaigns'] = self.get_email_campaigns_count()
        if include_candidate_count and get_candidate_count:
            talent_pipeline['total_candidates'] = get_candidate_count(self, datetime.utcnow())
        if include_growth and interval and get_growth_function:
            talent_pipeline['growth'] = get_growth_function(self, int(interval))
        if include_stats and get_stats_function:
            # Include Last 30 days stats in response body
            to_date = datetime.utcnow() - timedelta(days=1)
            to_date = to_date.replace(hour=23, minute=59, second=59)
            from_date = to_date - timedelta(days=29)
            talent_pipeline['stats'] = [] if self.added_time.date() == datetime.utcnow().date() else \
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

    @classmethod
    @contract
    def get_by_domain_id_and_name(cls, domain_id, name):
        """
        Returns TalentPipelines against name in user's domain
        :param positive domain_id: User's Domain Id
        :param string name: TalentPipeline name
        :rtype: list
        """
        return cls.query.join(User).filter(cls.name == name, User.domain_id == domain_id, cls.is_hidden == 0).all()

    @classmethod
    @contract
    def pipelines_user_group(cls, user_id, page_number=None):
        """
        This returns list of Pipelines in user's group
        :param positive user_id: User Id
        :param positive|None page_number: Page number for limiting number of rows returned
        :rtype: list
        """
        from user import User    # To avoid circular dependency this has to be here
        user = User.query.filter(User.id == user_id).first()
        query_object = cls.query.join(User).filter(User.user_group_id == user.user_group_id, cls.is_hidden == 0)
        if page_number is None:
            return query_object.all()
        number_of_records = 10
        start = (page_number - 1) * number_of_records
        end = page_number * number_of_records
        return query_object[start:end]
