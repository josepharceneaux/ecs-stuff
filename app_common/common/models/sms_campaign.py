__author__ = 'basit'

import datetime

from sqlalchemy.orm import relationship

from db import db
from ..error_handling import InternalServerError
from ..utils.datetime_utils import DatetimeUtils


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
    added_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    # Relationships
    blasts = relationship('SmsCampaignBlast', cascade='all, delete-orphan',
                          passive_deletes=True, lazy='dynamic', backref='campaign')
    smartlists = relationship('SmsCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign')

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
                       "list_ids": [campaign_smartlist.smartlist_id for campaign_smartlist in self.smartlists],
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


class SmsCampaignBlast(db.Model):
    __tablename__ = 'sms_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('sms_campaign.id', ondelete='CASCADE'))
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    replies = db.Column(db.Integer, default=0)
    sent_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    # Relationships
    blast_sends = relationship('SmsCampaignSend', cascade='all,delete-orphan',
                               passive_deletes=True, lazy='dynamic', backref='blast')
    blast_replies = relationship('SmsCampaignReply', cascade='all,delete-orphan',
                                 passive_deletes=True, lazy='dynamic', backref='blast')

    def __repr__(self):
        return "<SMSCampaignBlast (Sends: %s, Clicks: %s)>" % (self.sends, self.clicks)


class SmsCampaignSend(db.Model):
    __tablename__ = 'sms_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    blast_id = db.Column(db.Integer,  db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id'))
    sent_datetime = db.Column(db.DateTime)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

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
    added_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)

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
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

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
