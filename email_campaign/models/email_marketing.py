from common.models.db import db
from common.models.user import User
from common.models.misc import Frequency
from common.models.smart_list import SmartList
from sqlalchemy.orm import relationship, backref

import datetime

__author__ = 'jitesh'


class EmailCampaign(db.Model):
    __tablename__ = 'email_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(127), nullable=False)
    type = db.Column('Type', db.String(63))
    # Field('userId', 'reference user'),
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    # Field('isHidden', 'integer', length=1, default=0, readable=False, writable=False),
    is_hidden = db.Column('IsHidden', db.Boolean, default=False)
    # Field('emailSubject', length=127, label="Email subject", requires=IS_NOT_EMPTY()),
    email_subject = db.Column('emailSubject', db.String(127))
    # Field('emailFrom', length=127, label="From email", requires=IS_NOT_EMPTY()),
    email_from = db.Column('emailFrom', db.String(127))
    # Field('emailReplyTo', length=127, label="Reply-to email", requires=IS_NOT_EMPTY()),
    email_reply_to = db.Column('emailReplyTo', db.String(127))
    # Field('emailBodyHtml', 'text', length=65535, label="E-mail HTML body"),
    email_body_html = db.Column('EmailBodyHtml', db.Text(65535))
    # Field('emailBodyText', 'text', length=65535),
    email_body_text = db.Column('EmailBodyText', db.Text(65535))
    # Field('customHtml', 'text'),
    custom_html = db.Column('CustomHtml', db.Text)
    # Field('customUrlParamsJson', length=512, readable=True, writable=True),
    custom_url_params_json = db.Column('CustomUrlParamsJson', db.String(512))
    # Field('isEmailOpenTracking', 'integer', length=1, default=0),
    is_email_open_tracking = db.Column('isEmailOpenTracking', db.Boolean, default=False)
    # Field('isTrackHtmlClicks', 'integer', length=1, default=0),
    is_track_html_clicks = db.Column('isTrackHtmlClicks', db.Boolean, default=False)
    # Field('isTrackTextClicks', 'integer', length=1, default=0),
    is_track_text_clicks = db.Column('isTrackTextClicks', db.Boolean, default=False)
    # Field('isSubscription', 'integer', length=1, default=0),
    is_subscription = db.Column('isSubscription', db.Boolean, default=False)
    # Field('isPersonalizedToField', 'integer', length=1, default=0),
    is_personalized_to_field = db.Column('isPersonalizedToField', db.Boolean, default=False)
    # Field('addedTime', 'datetime', default=request.now, readable=False, writable=False),
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    # Field('sendTime', 'datetime', label="Send time", requires=IS_NOT_EMPTY()),
    send_time = db.Column('SendTime', db.DateTime)
    # Field('stopTime', 'datetime', label="Stop time", requires=IS_EMPTY_OR(IS_NOT_EMPTY())),
    stop_time = db.Column('StopTime', db.DateTime)
    # Field('frequencyId', db.frequency, label="Send frequency", requires=IS_NOT_EMPTY()),
    frequency_id = db.Column('frequencyId', db.Integer, db.ForeignKey('frequency.id'))
    frequency = relationship("Frequency", backref="frequency")
    # TODO: Field('schedulerTaskIds', 'list:integer'),
    # TODO: Field('emailClientId', 'reference email_client', required=False),
    # email_client_id = db.Column('EmailClientId', db.Integer, db.ForeignKey('email_client.id'))

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<EmailCampaign(name=' %r')>" % self.name


class EmailCampaignSmartList(db.Model):
    __tablename__ = 'email_campaign_smart_list'
    id = db.Column(db.Integer, primary_key=True)
    smart_list_id = db.Column('SmartListId', db.Integer, db.ForeignKey('smart_list.id'))
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id'))


class CandidateSubscriptionPreference(db.Model):
    __tablename__='candidate_subscription_preference'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id=db.column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    frequency_id=db.column('FrequencyId', db.Integer, db.ForeignKey('frequency.id'))
    # updated_time = db.column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

class EmailCampaignSend(db.Model):
    __tablename__='email_campaign_send'
    id=db.Column(db.Integer, primary_key=True)
    email_campaign_id = db.Column('EmailCampaignId', db.Integer)
    candidate_id = db.Column('CandidateId', db.Integer)
    sent_time = db.Column('SendTime', db.DateTime)
    ses_message_id = db.Column('sesMessageId', db.String(63))
    ses_request_id = db.Column('sesRequestId', db.String(63))
    is_ses_bounce = db.Column('isSesBounce', db.Boolean, default=False)
    is_ses_complaint = db.Column('isSesComplaint', db.Boolean, default=False)
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())


class EmailCampaignBlast(db.Model):
    __tablename__ = 'email_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id'))
    sends = db.Column('Sends', db.Integer, default=0)
    html_clicks = db.Column('HtmlClicks', db.Integer, default=0)
    text_clicks = db.Column('TextClicks', db.Integer, default=0)
    opens = db.Column(' Opens', db.Integer, default=0)
    bounces = db.Column('Bounces', db.Integer, default=0)
    complaints = db.Column('Complaints', db.Integer, default=0)
    sent_time = db.Column('SentTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

