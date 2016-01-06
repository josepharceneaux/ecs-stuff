from db import db
from sqlalchemy.orm import relationship, backref
import time
import datetime


class EmailCampaign(db.Model):
    __tablename__ = 'email_campaign'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    name = db.Column('Name', db.String(127))
    added_time = db.Column('AddedTime', db.DateTime)
    type = db.Column('Type', db.String(63))
    is_hidden = db.Column('IsHidden', db.SmallInteger, default=False)
    email_subject = db.Column('emailSubject', db.String(127))
    email_from = db.Column('emailFrom', db.String(127))
    email_reply_to = db.Column('emailReplyTo', db.String(127))
    email_first_name_merge_tag = db.Column('emailFirstNameMergeTag', db.String(255))
    is_email_open_tracking = db.Column('isEmailOpenTracking', db.SmallInteger, default=False)
    is_track_html_clicks = db.Column('isTrackHtmlClicks', db.SmallInteger, default=False)
    is_track_text_clicks = db.Column('isTrackTextClicks', db.SmallInteger, default=False)
    email_body_html = db.Column('EmailBodyHtml', db.Text)
    email_body_text = db.Column('EmailBodyText', db.Text)
    is_personalized_to_field = db.Column('isPersonalizedToField', db.SmallInteger, default=False)
    frequency_id = db.Column('frequencyId', db.Integer, db.ForeignKey('frequency.id'))
    send_time = db.Column('SendTime', db.DateTime)
    stop_time = db.Column('StopTime', db.DateTime)
    email_last_name_merge_tag = db.Column('emailLastNameMergeTag', db.String(255))
    scheduler_task_ids = db.Column('SchedulerTaskIds', db.String(255))
    custom_html = db.Column('CustomHtml', db.Text)
    custom_url_params_json = db.Column('CustomUrlParamsJson', db.String(512))
    is_subscription = db.Column('isSubscription', db.SmallInteger, default=False)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
    email_client_id = db.Column('EmailClientId', db.Integer, db.ForeignKey('email_client.id'))

    # Relationships
    email_campaign_sends = relationship('EmailCampaignSend', backref='email_campaign')
    email_campaign_blasts = relationship('EmailCampaignBlast', backref='email_campaign')

    def __repr__(self):
        return "<EmailCampaign (name = %r)>" % self.name


class EmailCampaignBlast(db.Model):
    __tablename__ = 'email_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id'))
    sends = db.Column('Sends', db.Integer, default=0)
    html_clicks = db.Column('HtmlClicks', db.Integer, default=0)
    text_clicks = db.Column('TextClicks', db.Integer, default=0)
    opens = db.Column('Opends', db.Integer, default=0)
    bounces = db.Column('Bounces', db.Integer, default=0)
    complaints = db.Column('Complaints', db.Integer, default=0)
    sent_time = db.Column('SentTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<EmailCampaignBlast (id = %r)>" % self.id


class EmailCampaignSend(db.Model):
    __tablename__ = 'email_campaign_send'
    id =  db.Column(db.Integer, primary_key=True)
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    sent_time = db.Column('SentTime', db.DateTime)
    ses_message_id = db.Column('sesMessageId', db.String(63))
    ses_request_id = db.Column('sesRequestId', db.String(63))
    is_ses_bounce = db.Column('isSesBounce', db.SmallInteger, default=False)
    is_ses_complaint = db.Column('isSesComplaint', db.SmallInteger, default=False)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<EmailCampaignSend (id = %r)>" % self.id


class EmailClient(db.Model):
    __tablename__ = 'email_client'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return "<EmailClient (name = %r)>" % self.name