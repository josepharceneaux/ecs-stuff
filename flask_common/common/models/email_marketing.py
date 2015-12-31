from db import db
from sqlalchemy.orm import relationship

import datetime

__author__ = 'jitesh'


class EmailCampaign(db.Model):
    __tablename__ = 'email_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(127), nullable=False)
    type = db.Column('Type', db.String(63))
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    is_hidden = db.Column('IsHidden', db.Boolean, default=False)
    email_subject = db.Column('emailSubject', db.String(127))
    email_from = db.Column('emailFrom', db.String(127))
    email_reply_to = db.Column('emailReplyTo', db.String(127))
    email_body_html = db.Column('EmailBodyHtml', db.Text(65535))
    email_body_text = db.Column('EmailBodyText', db.Text(65535))
    custom_html = db.Column('CustomHtml', db.Text)
    custom_url_params_json = db.Column('CustomUrlParamsJson', db.String(512))
    is_email_open_tracking = db.Column('isEmailOpenTracking', db.Boolean, default=False)
    is_track_html_clicks = db.Column('isTrackHtmlClicks', db.Boolean, default=False)
    is_track_text_clicks = db.Column('isTrackTextClicks', db.Boolean, default=False)
    is_subscription = db.Column('isSubscription', db.Boolean, default=False)
    is_personalized_to_field = db.Column('isPersonalizedToField', db.Boolean, default=False)
    scheduler_task_id = db.Column('SchedulerTaskIds', db.String(255))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    send_time = db.Column('SendTime', db.DateTime)
    stop_time = db.Column('StopTime', db.DateTime)
    frequency_id = db.Column('frequencyId', db.Integer, db.ForeignKey('frequency.id'))
    frequency = relationship("Frequency", backref="frequency")
    email_client_id = db.Column('EmailClientId', db.Integer, db.ForeignKey('email_client.id'))

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<EmailCampaign(name=' %r')>" % self.name


class EmailCampaignSmartList(db.Model):
    __tablename__ = 'email_campaign_smart_list'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column('SmartListId', db.Integer, db.ForeignKey('smart_list.id', ondelete='CASCADE'))
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id', ondelete='CASCADE'))

    @classmethod
    def get_smartlists_of_campaign(cls, campaign_id, smartlist_ids_only=False):
        records = cls.query.filter(EmailCampaignSmartList.email_campaign_id == campaign_id).all()
        if smartlist_ids_only:
            return [row.smartlist_id for row in records]
        return records


class EmailCampaignSend(db.Model):
    __tablename__ = 'email_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id', ondelete='CASCADE'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'))
    sent_time = db.Column('SentTime', db.DateTime)
    ses_message_id = db.Column('sesMessageId', db.String(63))
    ses_request_id = db.Column('sesRequestId', db.String(63))
    is_ses_bounce = db.Column('isSesBounce', db.Boolean, default=False)
    is_ses_complaint = db.Column('isSesComplaint', db.Boolean, default=False)
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())


class EmailCampaignBlast(db.Model):
    __tablename__ = 'email_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    email_campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.id', ondelete='CASCADE'))
    sends = db.Column('Sends', db.Integer, default=0)
    html_clicks = db.Column('HtmlClicks', db.Integer, default=0)
    text_clicks = db.Column('TextClicks', db.Integer, default=0)
    opens = db.Column('Opens', db.Integer, default=0)
    bounces = db.Column('Bounces', db.Integer, default=0)
    complaints = db.Column('Complaints', db.Integer, default=0)
    sent_time = db.Column('SentTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())


class EmailClient(db.Model):
    __tablename__ = 'email_client'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    # Relationships
    email_campaigns = relationship('EmailCampaign', backref='email_client')

    def __repr__(self):
        return "<EmailClient (name = %r)>" % self.name


class UrlConversion(db.Model):
    __tablename__ = 'url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    source_url = db.Column('sourceUrl', db.String(512))  # Ours
    destination_url = db.Column('destinationUrl', db.String(512))  # Theirs
    hit_count = db.Column('hitCount', db.Integer, default=0)
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    last_hit_time = db.Column('lastHitTime', db.DateTime)


class EmailCampaignSendUrlConversion(db.Model):
    __tablename__ = 'email_campaign_send_url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    email_campaign_send_id = db.Column('emailCampaignSendId', db.Integer, db.ForeignKey('email_campaign_send.id', ondelete='CASCADE'))
    url_conversion_id = db.Column('urlConversionId', db.Integer, db.ForeignKey('url_conversion.id', ondelete='CASCADE'))
    type = db.Column('type', db.Integer, default=0)  # 0 = TRACKING, 1 = TEXT, 2 = HTML

