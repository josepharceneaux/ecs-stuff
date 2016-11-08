
__author__ = 'basit'

from datetime import datetime
from contracts import contract

from sqlalchemy.orm import relationship
from sqlalchemy import or_, desc, extract, and_

from db import db
from ..error_handling import InternalServerError, NotFoundError
from ..utils.datetime_utils import DatetimeUtils
from ..custom_contracts import define_custom_contracts
from ..constants import OWNED

define_custom_contracts()


class SmsCampaign(db.Model):
    __tablename__ = 'sms_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127))
    user_phone_id = db.Column(db.Integer, db.ForeignKey('user_phone.id', ondelete='CASCADE'))
    body_text = db.Column(db.Text)
    frequency_id = db.Column(db.Integer, db.ForeignKey('frequency.id', ondelete='CASCADE'))
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    scheduler_task_id = db.Column(db.String(255))
    added_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    blasts = relationship('SmsCampaignBlast', cascade='all, delete-orphan',
                          passive_deletes=True, lazy='dynamic', backref='campaign')
    smartlists = relationship('SmsCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign', lazy='dynamic')

    def __repr__(self):
        return "<SmsCampaign (id = %d, name = %s)>" % (self.id, self.name)

    def to_dict(self, include_fields=None):
        """
        This returns required fields when an sms-campaign object is requested.
        :param list[str] | None include_fields: List of fields to include, or None for all.
        :rtype: dict[str, T]
        """
        # TODO: include_fields param is required here but will be used in GET-1260
        return_dict = {"id": self.id,
                       "user_id": self.user_phone.user_id,
                       "name": self.name,
                       "frequency": self.frequency.name if self.frequency else None,
                       "start_datetime": DatetimeUtils.utc_isoformat(self.start_datetime) if self.start_datetime else None,
                       "end_datetime": DatetimeUtils.utc_isoformat(self.end_datetime) if self.end_datetime else None,
                       "added_datetime": DatetimeUtils.utc_isoformat(self.added_datetime) if self.added_datetime else None,
                       "body_text": self.body_text,
                       "smartlist_ids": [campaign_smartlist.smartlist_id for campaign_smartlist in self.smartlists],
                       "scheduler_task_id": self.scheduler_task_id}
        return return_dict

    @classmethod
    def get_by_user_phone_id(cls, user_phone_id):
        """
        This returns all the sms-campaigns for the given user_phone_id.
        :param user_phone_id: Id of user_phone record
        :type user_phone_id: int | long
        :return: list of all sms-campaigns
        :rtype: list
        """
        if not isinstance(user_phone_id, (int, long)):
            raise InternalServerError('Invalid user_phone_id given')
        return cls.query.filter(cls.user_phone_id == user_phone_id).all()

    @classmethod
    def get_by_domain_id(cls, domain_id):
        """
        This returns all the sms-campaigns for given domain id
        :param (int, long) domain_id: Id of user's domain
        :return: Query to get all sms-campaigns for given domain_id
        :rtype: sqlalchemy.orm.query.Query
        """
        if not isinstance(domain_id, (int, long)):
            raise InternalServerError('Invalid domain_id given. Valid value should be int greater than 0')
        from user import User, UserPhone  # This has to be here to avoid circular import
        return cls.query.join(UserPhone, cls.user_phone_id == UserPhone.id).\
            join(User, UserPhone.user_id == User.id).filter(User.domain_id == domain_id)

    @classmethod
    @contract()
    def get_by_user_id(cls, user_id):
        """
        Returns SmsCampaign list against a User Id
        :param positive user_id: User Id
        :rtype: list|None
        """
        from user import UserPhone  # To avoid circular import
        user_phones = UserPhone.get_by_user_id(user_id)
        if user_phones:
            user_phone_ids = [user_phone.id for user_phone in user_phones]
            return cls.query.filter(cls.user_phone_id.in_(user_phone_ids)).all()
        return None

    @classmethod
    @contract()
    def get_by_name(cls, user_id, name):
        """
        Gets SmsCampaign against campaign name
        :param positive user_id: User Id
        :param string name: SmsCampaign name
        :rtype: list
        """
        from user import User, UserPhone
        domain_id = User.get_domain_id(user_id)
        if domain_id:
            return cls.query.join(UserPhone, User).filter(cls.name == name, User.domain_id == domain_id).all()
        raise NotFoundError

    @classmethod
    @contract()
    def sms_campaign_user_group(cls, user_id):
        """
        Returns SmsCampaign list against user group Id
        :param positive user_id: User Id
        :rtype: list
        """
        from user import User, UserPhone
        user = User.query.filter(User.id == user_id).first()
        if user:
            if user.user_group_id:
                return cls.query.join(UserPhone, User).filter(User.user_group_id == user.user_group_id).distinct().all()
        raise NotFoundError

    @classmethod
    @contract()
    def sms_campaigns_in_talent_pool(cls, user_id, scope, talentpool_names=None):
        """
        Returns SmsCampaigns in talent pool
        :param int scope: Number which determines weather user asking about all domain campaigns or only his campaigns
        :param positive user_id:
        :param list|None talentpool_names:
        :rtype: list
        """
        from smartlist import SmartlistCandidate
        from user import User, UserPhone
        smartlist_ids = SmartlistCandidate.get_smartlist_ids_in_talent_pools(user_id, talentpool_names)
        sms_campaign_ids = SmsCampaignSmartlist.query.with_entities(SmsCampaignSmartlist.campaign_id).\
            filter(SmsCampaignSmartlist.smartlist_id.in_(smartlist_ids)).all()
        sms_campaign_ids = [sms_campaign_id[0] for sms_campaign_id in sms_campaign_ids]
        scope_dependant_filter = cls.query.join(UserPhone, User).filter(cls.id.in_(sms_campaign_ids),
                                                                        User.id == user_id)\
            if scope == OWNED else cls.query.filter(cls.id.in_(sms_campaign_ids))
        return scope_dependant_filter.all()


class SmsCampaignBlast(db.Model):
    __tablename__ = 'sms_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('sms_campaign.id', ondelete='CASCADE'))
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    replies = db.Column(db.Integer, default=0)
    sent_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    blast_sends = relationship('SmsCampaignSend', cascade='all,delete-orphan',
                               passive_deletes=True, lazy='dynamic', backref='blast')
    blast_replies = relationship('SmsCampaignReply', cascade='all,delete-orphan',
                                 passive_deletes=True, lazy='dynamic', backref='blast')

    def __repr__(self):
        return "<SMSCampaignBlast (Sends: %s, Clicks: %s)>" % (self.sends, self.clicks)

    @classmethod
    @contract
    def top_performing_sms_campaign(cls, datetime_value, user_id):
        """
        This method returns top performing SMS campaign from a specific year
        :param int|long user_id: User Id
        :param datetime|string|None datetime_value: Year of campaign started or updated
        :rtype type(z)|None
        """
        from user import UserPhone, User
        domain_id = User.get_domain_id(user_id)
        user_ids_in_domain = User.query.with_entities(User.id).filter(User.domain_id == domain_id).all()
        user_ids_in_domain = [_id[0] for _id in user_ids_in_domain]
        user_phone_ids = UserPhone.query.with_entities(UserPhone.id).\
            filter(UserPhone.user_id.in_(user_ids_in_domain)).all()
        user_phone_ids = [_id[0] for _id in user_phone_ids]
        if domain_id and isinstance(datetime_value, datetime):
            return cls.query.filter(or_(cls.updated_time >= datetime_value,
                                        cls.sent_datetime >= datetime_value)).\
                filter(cls.sends > 0).\
                filter(SmsCampaign.id == cls.campaign_id, SmsCampaign.user_phone_id.in_(user_phone_ids)).\
                order_by(desc(cls.replies/cls.sends)).first()
        if domain_id and isinstance(datetime_value, basestring):
            return cls.query.filter(or_(extract("year", cls.updated_time) == datetime_value,
                                        extract("year", cls.sent_datetime) == datetime_value)). \
                filter(SmsCampaign.id == cls.campaign_id, cls.sends > 0). \
                filter(SmsCampaign.user_phone_id.in_(user_phone_ids)). \
                order_by(desc(cls.replies/cls.sends)).first()
        if domain_id and not datetime_value:
            return cls.query.filter(SmsCampaign.id == cls.campaign_id). \
                filter(SmsCampaign.user_phone_id.in_(user_phone_ids), cls.sends > 0). \
                order_by(desc(cls.replies/cls.sends)).first()
        return None


class SmsCampaignSend(db.Model):
    __tablename__ = 'sms_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    blast_id = db.Column(db.Integer,  db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id'))
    sent_datetime = db.Column(db.DateTime)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    url_conversions = relationship('SmsCampaignSendUrlConversion',
                                   cascade='all,delete-orphan',
                                   passive_deletes=True,
                                   backref='send')

    def __repr__(self):
        return "<SmsCampaignSend (id = %r)>" % self.id

    @classmethod
    def get_latest_campaign_by_candidate_id(cls, candidate_id):
        if not isinstance(candidate_id, (int, long)):
            raise InternalServerError('Invalid candidate_id given')
        # dash in following query is to order in ascending order in terms of datetime
        # (i.e. latest campaign send record should appear first)
        return cls.query.order_by(-cls.sent_datetime).filter(
            cls.candidate_id == candidate_id).first()

    @classmethod
    def get_by_blast_ids(cls, blast_ids):
        """
        This returns the query object to get all send objects for given blast_ids
        :param list[int|long] blast_ids: List of blast_ids
        :rtype: sqlalchemy.orm.query.Query
        """
        if not isinstance(blast_ids, list):
            raise InternalServerError('blast_ids must be a list')
        return cls.query.filter(cls.blast_id.in_(blast_ids))


class SmsCampaignReply(db.Model):
    __tablename__ = 'sms_campaign_reply'
    id = db.Column(db.Integer, primary_key=True)
    blast_id = db.Column(db.Integer, db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    body_text = db.Column(db.Text)
    candidate_phone_id = db.Column(db.BIGINT,
                                   db.ForeignKey('candidate_phone.Id', ondelete='CASCADE'))
    added_datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<SmsCampaignReply(id = %r)>" % self.id

    @classmethod
    def get_by_candidate_phone_id(cls, candidate_phone_id):
        if not isinstance(candidate_phone_id, (int, long)):
            raise InternalServerError('Invalid candidate_phone_id given')
        return cls.query.filter(cls.candidate_phone_id == candidate_phone_id).all()

    @classmethod
    def get_by_blast_ids(cls, blast_ids):
        """
        This returns the query object to get all sms-campaign-reply objects for given blast_ids
        :param list[int|long] blast_ids: List of blast_ids
        :rtype: sqlalchemy.orm.query.Query
        """
        if not isinstance(blast_ids, list):
            raise InternalServerError('blast_ids must be a list')
        return cls.query.filter(cls.blast_id.in_(blast_ids))


class SmsCampaignSmartlist(db.Model):
    __tablename__ = 'sms_campaign_smartlist'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey("smart_list.Id", ondelete='CASCADE'),
                             nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("sms_campaign.id", ondelete='CASCADE'),
                            nullable=False)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return '<SmsCampaignSmartlist(id = %r)>' % self.id


class SmsCampaignSendUrlConversion(db.Model):
    __tablename__ = 'sms_campaign_send_url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    send_id = db.Column(db.Integer,
                        db.ForeignKey("sms_campaign_send.id", ondelete='CASCADE'),
                        nullable=False)
    url_conversion_id = db.Column(db.Integer,
                                  db.ForeignKey("url_conversion.Id", ondelete='CASCADE'),
                                  nullable=False)

    def __repr__(self):
        return '<SmsCampaignSendUrlConversion(id = %r)>' % self.id
