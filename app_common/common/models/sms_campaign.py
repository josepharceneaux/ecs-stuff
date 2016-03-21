
__author__ = 'basit'

import datetime

from db import db
from sqlalchemy.orm import relationship
from ..error_handling import InvalidUsage
from ..datetime_utils import DatetimeUtils


class SmsCampaign(db.Model):
    __tablename__ = 'sms_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127))
    user_phone_id = db.Column(db.Integer, db.ForeignKey('user_phone.id', ondelete='CASCADE'))
    body_text = db.Column(db.Text)
    frequency_id = db.Column(db.Integer, db.ForeignKey('frequency.id', ondelete='CASCADE'))
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    added_datetime = db.Column(db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())
    scheduler_task_id = db.Column(db.String(255))

    # Relationships
    blasts = relationship('SmsCampaignBlast', cascade='all, delete-orphan',
                          passive_deletes=True, backref='campaign')
    smartlists = relationship('SmsCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign')

    def __repr__(self):
        return "<SmsCampaign (name = %r)>" % self.name

    def to_dict(self):
        """
        This returns required fields when an sms-campaign object is requested.
        :rtype: dict[str, T]
        """
        return_dict = {"id": self.id,
                       "user_id": self.user_phone.user_id,
                       "name": self.name,
                       "frequency": self.frequency.name if self.frequency else None,
                       "start_datetime": DatetimeUtils.utc_isoformat(self.start_datetime) if self.start_datetime else None,
                       "end_datetime": DatetimeUtils.utc_isoformat(self.end_datetime) if self.end_datetime else None,
                       "added_datetime": DatetimeUtils.utc_isoformat(self.added_datetime) if self.added_datetime else None,
                       "body_text": self.body_text,
                       "list_ids": [smartlist.id for smartlist in self.smartlists]}
        return return_dict

    @classmethod
    def get_by_user_phone_id(cls, user_phone_id):
        if not isinstance(user_phone_id, (int, long)):
            raise InvalidUsage('Invalid user_phone_id given')
        return cls.query.filter(cls.user_phone_id == user_phone_id).all()


class SmsCampaignBlast(db.Model):
    __tablename__ = 'sms_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('sms_campaign.id', ondelete='CASCADE'))
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    replies = db.Column(db.Integer, default=0)
    sent_datetime = db.Column(db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    blast_sends = relationship('SmsCampaignSend', cascade='all,delete-orphan',
                               passive_deletes=True, backref='blast')
    blast_replies = relationship('SmsCampaignReply', cascade='all,delete-orphan',
                                 passive_deletes=True, backref='blast')

    def __repr__(self):
        return "<SMSCampaignBlast (Sends: %s, Clicks: %s)>" % (self.sends, self.clicks)


class SmsCampaignSend(db.Model):
    __tablename__ = 'sms_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    blast_id = db.Column(db.Integer,  db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id'))
    sent_datetime = db.Column(db.DateTime)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

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
            raise InvalidUsage('Invalid candidate_id given')
        # dash in following query is to order in ascending order in terms of datetime
        # (i.e. latest campaign send record should appear first)
        return cls.query.order_by(-cls.sent_datetime).filter(
            cls.candidate_id == candidate_id).first()


class SmsCampaignReply(db.Model):
    __tablename__ = 'sms_campaign_reply'
    id = db.Column(db.Integer, primary_key=True)
    blast_id = db.Column(db.Integer, db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    body_text = db.Column(db.Text)
    candidate_phone_id = db.Column(db.BIGINT,
                                   db.ForeignKey('candidate_phone.Id', ondelete='CASCADE'))
    added_datetime = db.Column(db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<SmsCampaignReply(id = %r)>" % self.id

    @classmethod
    def get_by_candidate_phone_id(cls, candidate_phone_id):
        if not isinstance(candidate_phone_id, (int, long)):
            raise InvalidUsage('Invalid candidate_phone_id given')
        return cls.query.filter(cls.candidate_phone_id == candidate_phone_id).all()


class SmsCampaignSmartlist(db.Model):
    __tablename__ = 'sms_campaign_smartlist'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey("smart_list.Id", ondelete='CASCADE'),
                             nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("sms_campaign.id", ondelete='CASCADE'),
                            nullable=False)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

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
