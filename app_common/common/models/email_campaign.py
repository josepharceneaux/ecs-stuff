import datetime

from sqlalchemy import desc
from sqlalchemy.orm import relationship

from db import db
from ..error_handling import (ResourceNotFound, ForbiddenError)

__author__ = 'jitesh'


class EmailCampaign(db.Model):
    __tablename__ = 'email_campaign'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    name = db.Column('Name', db.String(127), nullable=False)
    type = db.Column('Type', db.String(63))
    is_hidden = db.Column('IsHidden', db.Boolean, default=False)
    email_subject = db.Column('emailSubject', db.String(127))
    email_from = db.Column('emailFrom', db.String(127))
    email_reply_to = db.Column('emailReplyTo', db.String(127))
    is_email_open_tracking = db.Column('isEmailOpenTracking', db.Boolean, default=True)
    is_track_html_clicks = db.Column('isTrackHtmlClicks', db.Boolean, default=True)
    is_track_text_clicks = db.Column('isTrackTextClicks', db.Boolean, default=True)
    email_body_html = db.Column('EmailBodyHtml', db.Text(65535))
    email_body_text = db.Column('EmailBodyText', db.Text(65535))
    is_personalized_to_field = db.Column('isPersonalizedToField', db.Boolean, default=False)
    frequency_id = db.Column('frequencyId', db.Integer, db.ForeignKey('frequency.id'))
    send_datetime = db.Column('SendTime', db.DateTime)
    stop_datetime = db.Column('StopTime', db.DateTime)
    scheduler_task_id = db.Column('SchedulerTaskIds', db.String(255))
    custom_html = db.Column('CustomHtml', db.Text)
    custom_url_params_json = db.Column('CustomUrlParamsJson', db.String(512))
    is_subscription = db.Column('isSubscription', db.Boolean, default=False)
    added_datetime = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    email_client_id = db.Column('EmailClientId', db.Integer, db.ForeignKey('email_client.id'))

    # Relationships
    frequency = relationship("Frequency", backref="frequency")
    blasts = relationship('EmailCampaignBlast', cascade='all, delete-orphan',
                          passive_deletes=True, backref='campaign')
    sends = relationship('EmailCampaignSend', cascade='all, delete-orphan',
                         passive_deletes=True, backref='campaign')
    smartlists = relationship('EmailCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign')

    def to_dict(self):
        """
        This returns required fields when an email-campaign object is requested.
        :rtype: dict[str, T]
        """
        return {"id": self.id,
                "user_id": self.user_id,
                "name": self.name,
                "frequency": self.frequency.name if self.frequency else None,
                "subject": self.email_subject,
                "from": self.email_from,
                "reply_to": self.email_reply_to,
                "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
                "end_datetime": self.stop_datetime.isoformat() if self.stop_datetime else None,
                "added_datetime": self.added_datetime.isoformat() if self.added_datetime else None,
                "list_ids": EmailCampaignSmartlist.get_smartlists_of_campaign(self.id,
                                                                              smartlist_ids_only=True)}

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<EmailCampaign(name=' %r')>" % self.name


class EmailCampaignSmartlist(db.Model):
    __tablename__ = 'email_campaign_smart_list'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column('SmartListId', db.Integer,
                             db.ForeignKey('smart_list.Id', ondelete='CASCADE'))
    campaign_id = db.Column('EmailCampaignId', db.Integer,
                            db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

    @classmethod
    def get_smartlists_of_campaign(cls, campaign_id, smartlist_ids_only=False):
        records = cls.query.filter_by(campaign_id=campaign_id).all()
        if smartlist_ids_only:
            return [row.smartlist_id for row in records]
        return records


class EmailCampaignBlast(db.Model):
    __tablename__ = 'email_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column('EmailCampaignId', db.Integer,
                                  db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    sends = db.Column('Sends', db.Integer, default=0)
    html_clicks = db.Column('HtmlClicks', db.Integer, default=0)
    text_clicks = db.Column('TextClicks', db.Integer, default=0)
    opens = db.Column('Opens', db.Integer, default=0)
    bounces = db.Column('Bounces', db.Integer, default=0)
    complaints = db.Column('Complaints', db.Integer, default=0)
    sent_datetime = db.Column('SentTime', db.DateTime)
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.get(_id)

    @classmethod
    def get_latest_blast_by_campaign_id(cls, campaign_id):
        """
        Method to get latest email campaign blast for campaign whose id is
        provided. Returns on the basis of most recent sent_datetime.
        :type campaign_id:  int | long
        :rtype:  EmailCampaignBlast
        """
        assert campaign_id, "campaign_id not provided"
        return cls.query.filter(
            cls.campaign_id == campaign_id).order_by(desc(cls.sent_datetime)).first()


class EmailCampaignSend(db.Model):
    __tablename__ = 'email_campaign_send'
    id = db.Column('Id', db.Integer, primary_key=True)
    campaign_id = db.Column('EmailCampaignId', db.Integer,
                                  db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    candidate_id = db.Column('CandidateId', db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'))
    sent_datetime = db.Column('SentTime', db.DateTime)
    ses_message_id = db.Column('sesMessageId', db.String(63))
    ses_request_id = db.Column('sesRequestId', db.String(63))
    is_ses_bounce = db.Column('isSesBounce', db.Boolean, default=False)
    is_ses_complaint = db.Column('isSesComplaint', db.Boolean, default=False)
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())
    email_campaign = relationship('EmailCampaign', backref="email_campaign")

    # Relationships
    url_conversions = relationship('EmailCampaignSendUrlConversion',
                                   cascade='all,delete-orphan',
                                   passive_deletes=True,
                                   backref='send')

    @classmethod
    def get_valid_send_object(cls, send_id, requested_campaign_id):
        """
        This returns the send object for given id.
        If record is not found, it raises ResourceNotFound error.
        If send object is not associated with given campaign_id, it raises ForbiddenError
        :param send_id: id of email_campaign_send object
        :param requested_campaign_id: id of email-campaign object
        :type send_id: int | long
        :type requested_campaign_id: int | long
        :return: email_campaign_send object
        :rtype: EmailCampaignSend
        """
        assert send_id, 'id of email-campaign-send obj not given'
        assert requested_campaign_id, 'id of email-campaign obj not given'
        send_obj = EmailCampaignSend.get_by_id(send_id)
        if not send_obj:
            raise ResourceNotFound("Send object(id:%s) for email-campaign(id:%s) does not "
                                   "exist in database."
                                   % (send_id, requested_campaign_id))
        if not send_obj.campaign_id == requested_campaign_id:
            raise ForbiddenError("Send object(id:%s) is not associated with email-campaign(id:%s)."
                                 % (send_id, requested_campaign_id))
        return send_obj


class EmailClient(db.Model):
    __tablename__ = 'email_client'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return "<EmailClient (name = %r)>" % self.name

    @classmethod
    def get_id_by_name(cls, name):
        return cls.query.filter_by(name=name).first().id


class EmailCampaignSendUrlConversion(db.Model):
    __tablename__ = 'email_campaign_send_url_conversion'
    id = db.Column('Id', db.Integer, primary_key=True)
    email_campaign_send_id = db.Column('EmailCampaignSendId', db.Integer,
                                       db.ForeignKey('email_campaign_send.Id', ondelete='CASCADE'))
    url_conversion_id = db.Column('UrlConversionId', db.Integer,
                                  db.ForeignKey('url_conversion.Id', ondelete='CASCADE'))
    type = db.Column(db.Integer, default=0)  # 0 = TRACKING, 1 = TEXT, 2 = HTML

    # Relationships
    email_campaign_send = relationship('EmailCampaignSend', backref="email_campaign_send")
