__author__ = 'basit'

from db import db
from sqlalchemy.orm import relationship
import datetime


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


class SmsCampaignSend(db.Model):
    __tablename__ = 'sms_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_blast_id = db.Column('SmsCampaignBlastId', db.Integer, db.ForeignKey('sms_campaign_blast.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    sent_time = db.Column('SentTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<SmsCampaignSend (id = %r)>" % self.id


class SmsCampaignReply(db.Model):
    __tablename__ = 'sms_campaign_reply'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_blast_id = db.Column('SmsCampaignBlastId', db.Integer,
                                      db.ForeignKey('sms_campaign_blast.id'))
    reply_text = db.Column('SmsBodyText', db.Text)
    candidate_phone_id = db.Column('CandidatePhoneId', db.Integer,
                                   db.ForeignKey('candidate_phone.id'))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<SmsCampaignReply (id = %r)>" % self.id


# class SmsCampaignSmartList(db.Model):
#     __tablename__ = 'sms_campaign_smart_list'
#     id = db.Column(db.Integer, primary_key=True)
#     sms_blast_id = db.Column('smsBlastId', db.Integer, db.ForeignKey('sms_campaign_blast.id'))
#     candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
#     sent_time = db.Column('SentTime', db.DateTime)
#     updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
#
#     def __repr__(self):
#         return "<smsCampaignSend (id = %r)>" % self.id