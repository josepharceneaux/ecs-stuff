import datetime

from sqlalchemy import desc
from sqlalchemy.orm import relationship

from db import db
from ..utils.datetime_utils import DatetimeUtils
from ..error_handling import (ResourceNotFound, ForbiddenError)

__author__ = 'jitesh'


class EmailCampaign(db.Model):
    __tablename__ = 'email_campaign'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    name = db.Column('Name', db.String(127), nullable=False)
    type = db.Column('Type', db.String(63))
    is_hidden = db.Column('IsHidden', db.Boolean, default=False)
    subject = db.Column('emailSubject', db.String(127))
    _from = db.Column('emailFrom', db.String(127))
    reply_to = db.Column('emailReplyTo', db.String(127))
    is_email_open_tracking = db.Column('isEmailOpenTracking', db.Boolean, default=True)
    is_track_html_clicks = db.Column('isTrackHtmlClicks', db.Boolean, default=True)
    is_track_text_clicks = db.Column('isTrackTextClicks', db.Boolean, default=True)
    # body_html and body_text are deferred fields because they could be huge.  Should really be stored in S3.
    body_html = db.deferred(db.Column('EmailBodyHtml', db.Text(65535)), group='email_body')
    body_text = db.deferred(db.Column('EmailBodyText', db.Text(65535)), group='email_body')
    is_personalized_to_field = db.Column('isPersonalizedToField', db.Boolean, default=False)
    frequency_id = db.Column('frequencyId', db.Integer, db.ForeignKey('frequency.id'))
    start_datetime = db.Column('SendTime', db.DateTime)
    end_datetime = db.Column('StopTime', db.DateTime)
    scheduler_task_id = db.Column('SchedulerTaskIds', db.String(255))
    custom_html = db.Column('CustomHtml', db.Text)
    custom_url_params_json = db.Column('CustomUrlParamsJson', db.String(512))
    is_subscription = db.Column('isSubscription', db.Boolean, default=False)
    added_datetime = db.Column('addedTime', db.DateTime, default=datetime.datetime.utcnow)
    email_client_id = db.Column('EmailClientId', db.Integer, db.ForeignKey('email_client.id'))

    # Relationships
    frequency = relationship("Frequency", backref="frequency")
    blasts = relationship('EmailCampaignBlast', lazy='dynamic', cascade='all, delete-orphan',
                          passive_deletes=True, backref='campaign')
    sends = relationship('EmailCampaignSend', cascade='all, delete-orphan',
                         passive_deletes=True, lazy='dynamic', backref='campaign')
    smartlists = relationship('EmailCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign')

    def to_dict(self, include_fields=None):
        """
        This returns required fields when an email-campaign object is requested.
        :param list[str] | None include_fields: List of fields to include, or None for all.
        :rtype: dict[str, T]
        """
        return_dict = {"id": self.id,
                       "user_id": self.user_id,
                       "name": self.name,
                       "frequency": self.frequency.name if self.frequency else None,
                       "subject": self.subject,
                       "from": self._from,
                       "reply_to": self.reply_to,
                       "start_datetime": DatetimeUtils.utc_isoformat(self.start_datetime) if self.start_datetime else None,
                       "end_datetime": DatetimeUtils.utc_isoformat(self.end_datetime) if self.end_datetime else None,
                       "added_datetime": DatetimeUtils.utc_isoformat(self.added_datetime) if self.added_datetime else None,
                       # Conditionally include body_text and body_html because they are deferred fields
                       "body_html": self.body_html if (include_fields and 'body_html' in include_fields) else None,
                       "body_text": self.body_text if (include_fields and 'body_text' in include_fields) else None,
                       "is_hidden": self.is_hidden,
                       "list_ids": EmailCampaignSmartlist.get_smartlists_of_campaign(self.id,
                                                                                     smartlist_ids_only=True)}

        # Only include the fields that are supposed to be included
        if include_fields:
            return {key: return_dict[key] for key in include_fields if key in return_dict}

        return return_dict

    def get_id(self):
        return unicode(self.id)

    @classmethod
    def get_by_domain_id(cls, domain_id):
        assert domain_id, 'domain_id not given'
        from user import User  # This has to be here to avoid circular import
        return cls.query.join(User).filter(User.domain_id == domain_id)

    def __repr__(self):
        return "<EmailCampaign(name=' %r')>" % self.name


class EmailCampaignSmartlist(db.Model):
    __tablename__ = 'email_campaign_smart_list'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column('SmartListId', db.Integer,
                             db.ForeignKey('smart_list.Id', ondelete='CASCADE'))
    campaign_id = db.Column('EmailCampaignId', db.Integer,
                            db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def get_smartlists_of_campaign(cls, campaign_id, smartlist_ids_only=False):
        # TODO--assert on params
        records = cls.query.filter_by(campaign_id=campaign_id).all()
        if smartlist_ids_only:
            return [row.smartlist_id for row in records]
        return records


class EmailCampaignBlast(db.Model):
    __tablename__ = 'email_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    sends = db.Column('Sends', db.Integer, default=0)
    html_clicks = db.Column('HtmlClicks', db.Integer, default=0)
    text_clicks = db.Column('TextClicks', db.Integer, default=0)
    opens = db.Column('Opens', db.Integer, default=0)
    bounces = db.Column('Bounces', db.Integer, default=0)
    complaints = db.Column('Complaints', db.Integer, default=0)
    sent_datetime = db.Column('SentTime', db.DateTime)
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    blast_sends = relationship('EmailCampaignSend', cascade='all, delete-orphan',
                               passive_deletes=True, backref='blast', lazy='dynamic')

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

    def __repr__(self):
        return "<EmailCampaignBlast (Sends: %s, Opens: %s)>" % (self.sends, self.opens)


class EmailCampaignSend(db.Model):
    __tablename__ = 'email_campaign_send'
    id = db.Column('Id', db.Integer, primary_key=True)
    campaign_id = db.Column('EmailCampaignId', db.Integer, db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    blast_id = db.Column('EmailCampaignBlastId', db.Integer, db.ForeignKey('email_campaign_blast.id', ondelete='CASCADE'))
    candidate_id = db.Column('CandidateId', db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'))
    sent_datetime = db.Column('SentTime', db.DateTime)
    ses_message_id = db.Column('sesMessageId', db.String(63))
    ses_request_id = db.Column('sesRequestId', db.String(63))
    is_ses_bounce = db.Column('isSesBounce', db.Boolean, default=False)
    is_ses_complaint = db.Column('isSesComplaint', db.Boolean, default=False)
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.utcnow)
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

    @classmethod
    def get_by_amazon_ses_message_id(cls, message_id):
        """
        Get send email object from given SES message id.
        :param message_id: Simple Email Service (SES) unique message id
        :type message_id: str
        :return: EmailCampaignSend object
        """
        assert isinstance(message_id, basestring) and message_id, 'message_id should have a valid value.'
        return cls.query.filter_by(ses_message_id=message_id).first()


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


class UserEmailTemplate(db.Model):
    __tablename__ = 'user_email_template'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id'), index=True)
    type = db.Column('Type', db.Integer, server_default=db.text("'0'"))
    name = db.Column('Name', db.String(255), nullable=False)
    body_html = db.Column('EmailBodyHtml', db.Text)
    body_text = db.Column('EmailBodyText', db.Text)
    template_folder_id = db.Column('EmailTemplateFolderId', db.Integer, db.ForeignKey('email_template_folder.id',
                                                                                      ondelete=u'SET NULL'), index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, server_default=db.text("'0'"))
    updated_datetime = db.Column('UpdatedTime', db.DateTime, nullable=False, server_default=db.text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    # Relationships
    template_folder = relationship(u'EmailTemplateFolder', backref=db.backref('user_email_template',
                                                                              cascade="all, delete-orphan"))

    @classmethod
    def get_by_id(cls, template_id):
        """
        :type template_id:  int | long
        :return: UserEmailTemplate
        """
        return cls.query.get(template_id)

    @classmethod
    def get_by_name(cls, template_name):
        return cls.query.filter_by(name=template_name).first()


class EmailTemplateFolder(db.Model):
    __tablename__ = 'email_template_folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    parent_id = db.Column('ParentId', db.Integer,  db.ForeignKey('email_template_folder.id', ondelete='CASCADE'),
                          index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, server_default=db.text("'0'"))
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'), index=True)
    updated_time = db.Column('UpdatedTime', db.DateTime, nullable=False,
                             server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    domain = relationship('Domain', backref=db.backref('email_template_folder', cascade="all, delete-orphan"))
    parent = relationship('EmailTemplateFolder', remote_side=[id], backref=db.backref('email_template_folder',
                                                                                      cascade="all, delete-orphan"))

    @classmethod
    def get_by_id(cls, folder_id):
        """
        :type folder_id:  int | long
        :return: EmailTemplateFolder
        """
        return cls.query.get(folder_id)

    @classmethod
    def get_by_name_and_domain_id(cls, folder_name, domain_id):
        """
        Method to get email template folder based on folder name and domain id.
        :type folder_name:  string
        :type domain_id:  int | long
        :rtype:  EmailTemplateFolder
        """
        assert folder_name, "folder_name not provided"
        assert domain_id, "domain_id not provided"
        return cls.query.filter_by(name=folder_name, domain_id=domain_id).first()
