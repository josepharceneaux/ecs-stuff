"""
This module contains model classes that are related to push campaign service.

    - PushCampaign
        Used to handle campaign objects for Push Campaign Service

    - PushCampaignBlast
        Every time a campaign is sent, a blast is created which contains stats for that campaign.

    - PushCampaignSend
        When a campaign is sent to a candidate a send entry is created.

    - PushCampaignSmartlist
        Used to associate smartlist with a campaign

    - PushCampaignSendUrlConversion
        When a campaign is send to a candidate, a UrlConversion is created which is associated
        to a campaign send via this table

"""
from datetime import datetime
from contracts import contract

from db import db
from sqlalchemy.orm import relationship
from sqlalchemy import desc, extract, and_
from candidate import Candidate
from ..error_handling import InvalidUsage, NotFoundError
from ..utils.talentbot_utils import OWNED

__author__ = 'Zohaib Ijaz <mzohaib.qc@gmail.com>'


class PushCampaign(db.Model):
    """
    A push campaign has a title/name, body_text and information about campaign start,
    end, frequency etc.
    OneSignal is being used to actually send these campaigns to candidates.
    """
    __tablename__ = 'push_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    body_text = db.Column(db.String(1000))
    url = db.Column(db.String(255))
    scheduler_task_id = db.Column(db.String(50))
    added_datetime = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    frequency_id = db.Column(db.Integer, db.ForeignKey('frequency.id'))
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))

    # Relationships

    blasts = relationship('PushCampaignBlast', cascade='all, delete-orphan',
                          passive_deletes=True, backref='campaign', lazy='dynamic')

    smartlists = relationship('PushCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign', lazy='dynamic')

    def __repr__(self):
        return "<PushCampaign (body_text = %r)>" % self.body_text

    def to_json(self, include_fields=None):
        """
        This returns required fields when an push-campaign object is requested.
        :param list[str] | None include_fields: List of fields to include, or None for all.
        :rtype: dict[str, T]
        """
        return_dict = super(PushCampaign, self).to_json(include_fields=include_fields)
        if not include_fields or "smartlist_ids" in include_fields:
            return_dict["smartlist_ids"] = [campaign_smartlist.smartlist_id for campaign_smartlist in self.smartlists]
        return return_dict

    @classmethod
    def get_by_user_id(cls, user_id, page_number=None):
        """
        This method returns all PushCampaign objects that are owned by a user.
        :param page_number:
        :param user_id: User id
        :return: list of PushCampaign objects
        :rtype:  list[PushCampaign]
        """
        assert isinstance(user_id, (int, long)) and user_id > 0, 'User id is not valid integer'
        query_object = cls.query.filter_by(user_id=user_id)
        if page_number is None:
            return query_object.all()
        number_of_records = 10
        start = (page_number - 1) * number_of_records
        end = page_number * number_of_records
        return query_object[start:end]

    @classmethod
    def get_by_id_and_user_id(cls, _id, user_id):
        """
        Get a campaign object where unique id is `_id` and it is owned by user given by `user_id`.
        :param _id: campaign unique id
        :type _id: int | long
        :param user_id: user unique id
        :type user_id: int | long
        :return: instance of PushCampaign
        :rtype PushCampaign
        """
        assert isinstance(_id, (int, long)) and _id > 0, 'PushCampaign id is not valid integer'
        assert isinstance(user_id, (int, long)) and user_id > 0, 'User id is not valid integer'
        return cls.query.filter_by(id=_id, user_id=user_id).first()

    @classmethod
    @contract
    def get_by_domain_id_and_name(cls, domain_id, name):
        """
        Gets PushCampaign against campaign name
        :param positive domain_id: User's Domain Id
        :param string name: PushCampaign name
        :rtype: list
        """
        from user import User
        return cls.query.join(User).filter(cls.name == name, User.domain_id == domain_id).all()

    @classmethod
    @contract
    def get_by_domain_id(cls, domain_id, page_number=None):
        """
        Returns all PushCampaigns with same domain_id
        :param positive|None page_number: Page number for pagination purpose
        :param positive domain_id: Domain Id
        :rtype: list
        """
        from user import User
        query_object = cls.query.join(User).filter(User.domain_id == domain_id)
        if page_number is None:
            return query_object.all()
        number_of_records = 10
        start = (page_number - 1) * number_of_records
        end = page_number * number_of_records
        return query_object[start:end]

    @classmethod
    @contract
    def push_campaigns_in_user_group(cls, user_id):
        """
        This returns list of PushCampaigns in user's group
        :param positive user_id: User Id
        :rtype: list
        """
        from user import User    # To avoid circular dependency this has to be here
        user = User.query.filter(User.id == user_id).first()
        if user:
            if user.user_group_id:
                return cls.query.join(User).filter(User.user_group_id == user.user_group_id).all()
        raise NotFoundError

    @classmethod
    @contract
    def push_campaigns_in_talent_pool(cls, user_id, scope, talentpool_names=None, page_number=None):
        """
        Returns PushCampaigns in talent pool
        :param positive|None page_number: Page number for pagination purpose
        :param int scope: Number which determines weather user asking about all domain campaigns or only his campaigns
        :param positive user_id:
        :param list|None talentpool_names:
        :rtype: list
        """
        from smartlist import SmartlistCandidate    # To avoid circular dependency this has to be here
        from user import User    # To avoid circular dependency this has to be here
        smartlist_ids = SmartlistCandidate.get_smartlist_ids_in_talent_pools(user_id, talentpool_names)
        push_campaign_ids = PushCampaignSmartlist.query.with_entities(PushCampaignSmartlist.campaign_id).\
            filter(PushCampaignSmartlist.smartlist_id.in_(smartlist_ids)).all()
        push_campaign_ids = [email_campaign_id[0] for email_campaign_id in push_campaign_ids]
        scope_dependant_filter = cls.query.join(User).filter(cls.id.in_(push_campaign_ids), cls.user_id == user_id)\
            if scope == OWNED else cls.query.filter(cls.id.in_(push_campaign_ids))
        if page_number is None:
            return scope_dependant_filter.all()
        number_of_records = 10
        start = (page_number - 1) * number_of_records
        end = page_number * number_of_records
        return scope_dependant_filter[start:end]


class PushCampaignBlast(db.Model):
    """
    Every time a campaign is sent to some candidates, a blast entry is created which
    contains campaign's stats.
    """
    __tablename__ = 'push_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    campaign_id = db.Column(db.Integer, db.ForeignKey('push_campaign.id', ondelete='CASCADE'))
    updated_datetime = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    blast_sends = relationship('PushCampaignSend', cascade='all, delete-orphan',
                               passive_deletes=True, backref='blast', lazy='dynamic')

    def __repr__(self):
        return "<PushCampaignBlast (Sends: %s, Clicks: %s)>" % (self.sends, self.clicks)

    @classmethod
    @contract
    def top_performing_push_campaign(cls, datetime_value, user_id):
        """
        This method returns top performing push campaign
        :param int|long user_id: User Id
        :param string|datetime|None datetime_value: Year of campaign started or updated
        :rtype: type(z)
        """
        assert isinstance(datetime_value, (datetime, basestring)) or datetime_value is None, \
            "Invalid datetime value"
        assert isinstance(user_id, (int, long)) and user_id, "Invalid User Id"
        from user import User    # To avoid circular dependency this has to be here
        domain_id = User.get_domain_id(user_id)
        if isinstance(datetime_value, datetime):
            return cls.query.filter(cls.updated_datetime >= datetime_value). \
                filter(PushCampaign.id == cls.campaign_id).\
                filter(and_(PushCampaign.user_id == User.id, User.domain_id == domain_id)). \
                filter(cls.sends > 0).order_by(desc(cls.clicks/cls.sends)).first()
        if isinstance(datetime_value, basestring):
            return cls.query.filter(extract("year", cls.updated_datetime) == datetime_value). \
                filter(PushCampaign.id == cls.campaign_id).\
                filter(and_(PushCampaign.user_id == User.id, User.domain_id == domain_id)). \
                filter(cls.sends > 0). \
                order_by(desc(cls.clicks/cls.sends)).first()
        return cls.query.filter(PushCampaign.id == cls.campaign_id).\
            filter(and_(PushCampaign.user_id == User.id, User.domain_id == domain_id)).\
            filter(cls.sends > 0).order_by(desc(cls.clicks/cls.sends)).first()


class PushCampaignSend(db.Model):
    """
    When a campaign is sent to a candidate, a send entry is created which contains
    information like candidate_id, send datetime and associated campaign.
    """
    __tablename__ = 'push_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'))
    sent_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    blast_id = db.Column(db.Integer, db.ForeignKey("push_campaign_blast.id", ondelete='CASCADE'),
                         nullable=False)

    # Relationships
    push_campaign_sends_url_conversions = relationship('PushCampaignSendUrlConversion',
                                                       cascade='all,delete-orphan',
                                                       passive_deletes=True,
                                                       backref='send')

    def __repr__(self):
        return "<PushCampaignSend (candidate_id: %s,  sent_datetime: %s)>" \
               % (self.candidate_id, self.sent_datetime)


class PushCampaignSmartlist(db.Model):
    """
    PushCampaignSmartlist associates a smartlist to a push campaign.
    """
    __tablename__ = 'push_campaign_smartlist'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey("smart_list.Id", ondelete='CASCADE'),
                             nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("push_campaign.id", ondelete='CASCADE'), nullable=False)
    updated_datetime = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return '<PushCampaignSmartlist (id = %s, smartlist_id: %s)>' % (self.id, self.smartlist_id)

    @classmethod
    def get_by_campaign_id(cls, campaign_id):
        """
        Get all records that are associated with a specific campaign.
        :param campaign_id: push campaign unique id
        :type campaign_id: int | long
        :rtype:  list[PushCampaignSmartlist]
        """
        assert isinstance(campaign_id, (int, long)) and campaign_id > 0, \
            'PushCampaign Id should be a valid positive number'
        return cls.query.filter_by(campaign_id=campaign_id).all()

    @classmethod
    def get_by_campaign_id_and_smartlist_id(cls, campaign_id, smartlist_id):
        assert isinstance(campaign_id, (int, long)) and campaign_id > 0, \
            'PushCampaign Id should be a valid positive number'
        assert isinstance(smartlist_id, (int, long)) and smartlist_id > 0, \
            'Smartlist Id should be a valid positive number'
        return cls.query.filter_by(campaign_id=campaign_id,
                                   smartlist_id=smartlist_id).first()


class PushCampaignSendUrlConversion(db.Model):
    """
    PushCampaignSendUrlConversion associates push campaign send to UrlConversion object.
    """
    __tablename__ = 'push_campaign_send_url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    send_id = db.Column(db.Integer,
                        db.ForeignKey("push_campaign_send.id", ondelete='CASCADE'),
                        nullable=False)
    url_conversion_id = db.Column(db.Integer,
                                  db.ForeignKey("url_conversion.Id", ondelete='CASCADE'),
                                  nullable=False)

    def __repr__(self):
        return '<PushCampaignSendUrlConversion (id = %s , send_id = %s)>' % (self.id, self.send_id)

    @classmethod
    def get_by_send_id_and_url_conversion_id(cls, send_id, url_conversion_id):
        assert send_id, 'No send_id given'
        assert url_conversion_id, 'No url_conversion_id given'
        return cls.query.filter(
            send_id=send_id,
            url_conversion_id=url_conversion_id
        ).first()

    @classmethod
    def get_by_campaign_send_id(cls, send_id):
        assert send_id, 'No send_id given'
        return cls.query.filter_by(send_id=send_id).first()
