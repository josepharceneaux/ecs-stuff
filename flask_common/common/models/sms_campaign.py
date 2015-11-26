__author__ = 'basit'

import datetime
from db import db
from sqlalchemy.orm import relationship


class SmsCampaign(db.Model):
    __tablename__ = 'sms_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(127))
    user_phone_id = db.Column('UserPhoneId', db.Integer, db.ForeignKey('user_phone.id'))
    sms_body_text = db.Column('SmsBodyText', db.Text)
    frequency_id = db.Column('FrequencyId', db.Integer, db.ForeignKey('frequency.id'))
    send_time = db.Column('SendTime', db.DateTime)
    stop_time = db.Column('StopTime', db.DateTime)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
    # scheduler_task_ids = db.Column('SchedulerTaskIds', db.String(255))

    # Relationships
    sms_campaign_blasts = relationship('SmsCampaignBlast', backref='sms_campaign')

    def __repr__(self):
        return "<SmsCampaign (name = %r)>" % self.name

    @classmethod
    def get_by_user_phone_id(cls, user_phone_id):
        assert user_phone_id
        return cls.query.filter(
            db.and_(
                cls.user_phone_id == user_phone_id,
            )
        ).all()


class SmsCampaignBlast(db.Model):
    __tablename__ = 'sms_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_id = db.Column('smsCampaignId', db.Integer, db.ForeignKey('sms_campaign.id'))
    sends = db.Column('Sends', db.Integer, default=0)
    clicks = db.Column('Clicks', db.Integer, default=0)
    replies = db.Column('Replies', db.Integer, default=0)
    sent_time = db.Column('SentTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    sms_campaign_sends = relationship('SmsCampaignSend', backref='sms_campaign_blast')
    sms_campaign_replies = relationship('SmsCampaignReply', backref='sms_campaign_blast')

    def __repr__(self):
        return "<SmsCampaignBlast (id = %r)>" % self.id

    @classmethod
    def get_by_campaign_id(cls, campaign_id):
        assert campaign_id
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_id == campaign_id,
            )
        ).first()


class SmsCampaignSend(db.Model):
    __tablename__ = 'sms_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_blast_id = db.Column('SmsCampaignBlastId', db.Integer, db.ForeignKey('sms_campaign_blast.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    sent_time = db.Column('SentTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<SmsCampaignSend (id = %r)>" % self.id

    @classmethod
    def get_by_blast_id_and_candidate_id(cls, campaign_blast_id, candidate_id):
        assert campaign_blast_id and candidate_id
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_blast_id == campaign_blast_id,
                cls.candidate_id == candidate_id,
            )
        ).first()

    @classmethod
    def get_by_candidate_id(cls, candidate_id):
        assert candidate_id
        return cls.query.order_by(-cls.sent_time).filter(
            db.and_(
                cls.candidate_id == candidate_id,
            )
        ).first()

    @classmethod
    def get_by_campaign_id(cls, campaign_blast_id):
        assert campaign_blast_id
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_blast_id == campaign_blast_id,
            )
        ).all()


class SmsCampaignReply(db.Model):
    __tablename__ = 'sms_campaign_reply'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_blast_id = db.Column('SmsCampaignBlastId', db.Integer,
                                      db.ForeignKey('sms_campaign_blast.id'))
    reply_body_text = db.Column('SmsBodyText', db.Text)
    candidate_phone_id = db.Column('CandidatePhoneId', db.Integer,
                                   db.ForeignKey('candidate_phone.id'))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<SmsCampaignReply (id = %r)>" % self.id

    @classmethod
    def get_by_blast_id_and_candidate_phone_id(cls, campaign_blast_id, candidate_phone_id):
        assert campaign_blast_id and candidate_phone_id
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_blast_id == campaign_blast_id,
                cls.candidate_phone_id == candidate_phone_id
            )
        ).first()

class SmsCampaignSmartList(db.Model):
    __tablename__ = 'sms_campaign_smart_list'
    id = db.Column(db.Integer, primary_key=True)
    smart_list_id = db.Column('SmartListId', db.Integer, db.ForeignKey("smart_list.id"), nullable=False)
    sms_campaign_id = db.Column('SmsCampaignId', db.Integer, db.ForeignKey("sms_campaign.id"), nullable=False)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return '<SmsCampaignSmartList (id = %r)>' % self.id

    @classmethod
    def get_by_campaign_id(cls, campaign_id):
        assert campaign_id
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_id == campaign_id,
            )
        ).all()


class SmsCampaignSendUrlConversion(db.Model):
    __tablename__ = 'sms_campaign_send_url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_send_id = db.Column('SmsCampaignSendId', db.Integer,
                                     db.ForeignKey("sms_campaign_send.id"), nullable=False)
    url_conversion_id = db.Column('UrlConversionId', db.Integer,
                                  db.ForeignKey("url_conversion.id"), nullable=False)

    def __repr__(self):
        return '<SmsCampaignSendUrlConversion (id = %r)>' % self.id

    @classmethod
    def get_by_campaign_sned_id_and_url_conversion_id(cls,
                                                      campaign_send_id,
                                                      url_conversion_id):
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_send_id == campaign_send_id,
                cls.url_conversion_id == url_conversion_id
            )
        ).first()
