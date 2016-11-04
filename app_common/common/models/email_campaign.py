from datetime import datetime

from contracts import contract
from sqlalchemy.orm import relationship
from sqlalchemy import or_, desc, extract, and_

from db import db
from ..utils.datetime_utils import DatetimeUtils
from ..utils.validators import (raise_if_not_instance_of,
                                raise_if_not_positive_int_or_long)
from ..error_handling import (ResourceNotFound, ForbiddenError, InternalServerError, InvalidUsage, NotFoundError)

__author__ = 'jitesh'


class EmailCampaign(db.Model):
    __tablename__ = 'email_campaign'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    name = db.Column('Name', db.String(127), nullable=False)
    type = db.Column('Type', db.String(63))
    is_hidden = db.Column('IsHidden', db.Boolean, default=False)
    subject = db.Column('emailSubject', db.String(127))
    description = db.Column('Description', db.Text(65535))
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
    added_datetime = db.Column('addedTime', db.DateTime, default=datetime.utcnow)
    email_client_id = db.Column('EmailClientId', db.Integer, db.ForeignKey('email_client.id'))
    email_client_credentials_id = db.Column('EmailClientCredentialsId', db.Integer,
                                            db.ForeignKey('email_client_credentials.id'))

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
        from smartlist import Smartlist
        smart_lists = Smartlist.query.join(EmailCampaignSmartlist).filter(EmailCampaignSmartlist.campaign_id == self.id).all()
        talent_pipelines = [{"id": smart_list.talent_pipeline.id, "name": smart_list.talent_pipeline.name}
                            for smart_list in smart_lists if smart_list.talent_pipeline]

        talent_pipelines = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in talent_pipelines)]

        return_dict = {"id": self.id,
                       "user_id": self.user_id,
                       "name": self.name,
                       "frequency": self.frequency.name if self.frequency else None,
                       "subject": self.subject,
                       "description": self.description,
                       "from": self._from,
                       "reply_to": self.reply_to,
                       "start_datetime": DatetimeUtils.utc_isoformat(self.start_datetime) if self.start_datetime else None,
                       "end_datetime": DatetimeUtils.utc_isoformat(self.end_datetime) if self.end_datetime else None,
                       "added_datetime": DatetimeUtils.utc_isoformat(self.added_datetime) if self.added_datetime else None,
                       # Conditionally include body_text and body_html because they are deferred fields
                       "body_html": self.body_html if (include_fields and 'body_html' in include_fields) else None,
                       "body_text": self.body_text if (include_fields and 'body_text' in include_fields) else None,
                       "is_hidden": self.is_hidden,
                       "talent_pipelines": talent_pipelines,
                       "list_ids": [smart_list.id for smart_list in smart_lists],
                       "email_client_credentials_id": self.email_client_credentials_id}

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
        return cls.query.join(User).filter(User.domain_id == domain_id, cls.is_hidden == 0)

    @classmethod
    def get_by_domain_id_and_filter_by_name(cls, domain_id, search_keyword, sort_by, sort_type, is_hidden):
        assert domain_id, 'domain_id not given'
        from user import User  # This has to be here to avoid circular import
        if sort_by == 'name':
            sort_by_object = EmailCampaign.name
        else:
            sort_by_object = EmailCampaign.added_datetime

        if sort_type == 'ASC':
            sort_by_object = sort_by_object.asc()
        else:
            sort_by_object = sort_by_object.desc()

        is_hidden = True if is_hidden else False
        return cls.query.join(User).filter(User.domain_id == domain_id, cls.name.ilike(
                '%' + search_keyword + '%'), cls.is_hidden == is_hidden).order_by(sort_by_object)

    @classmethod
    @contract()
    def get_by_user_id(cls, user_id):
        """
        Returns EmailCampaigns against a User Id
        :param positive user_id: User Id
        :rtype: list
        """
        return cls.query.filter(cls.user_id == user_id, cls.is_hidden == 0).all()

    @classmethod
    @contract()
    def get_by_name(cls, user_id, name):
        """
        Gets EmailCampaign against campaign name
        :param positive user_id:
        :param string name:
        :rtype: list
        """
        from user import User
        domain_id = User.get_domain_id(user_id)
        if domain_id:
            return cls.query.join(User).filter(cls.name == name, User.domain_id == domain_id, cls.is_hidden == 0).all()
        raise NotFoundError

    def __repr__(self):
        return "<EmailCampaign(name=' %r')>" % self.name


class EmailCampaignSmartlist(db.Model):
    __tablename__ = 'email_campaign_smart_list'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column('SmartListId', db.Integer,
                             db.ForeignKey('smart_list.Id', ondelete='CASCADE'))
    campaign_id = db.Column('EmailCampaignId', db.Integer,
                            db.ForeignKey('email_campaign.Id', ondelete='CASCADE'))
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_smartlists_of_campaign(cls, campaign_id, smartlist_ids_only=False):
        """
        Get smartlists associated with the given campaign.
        :param campaign_id: Id of campaign for with smartlists are to be retrieved
        :param smartlist_ids_only: True if only ids are to be returned
        :type campaign_id: int | long
        :type smartlist_ids_only: bool
        :rtype list
        """
        raise_if_not_positive_int_or_long(campaign_id)
        raise_if_not_instance_of(smartlist_ids_only, bool)
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
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.utcnow)

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

    @classmethod
    def get_by_send(cls, send_obj):
        """
        This method takes EmailCampaignSend object as input and returns associated EmailCampaignBlast object.
        It first tries to retrieve blast from backref. If that is None, then get blast by matching sent_datetime
        :param EmailCampaignSend send_obj: campaign send object
        :rtype EmailCampaignBlast | None
        """
        assert isinstance(send_obj, EmailCampaignSend), 'send_obj must be EmailCampaignSend instance, found: %s, type: %s' % (send_obj, type(send_obj))
        blast = send_obj.blast
        if isinstance(blast, EmailCampaignBlast):
            return blast
        # if blast_id is not there, match by sent_datetime as we are doing in web2py app:
        # https://github.com/Veechi/Talent-Web/blob/master/web2py/applications/web/controllers/campaign.py#L63
        return cls.query.filter_by(sent_datetime=send_obj.sent_datetime).first()

    def __repr__(self):
        return "<EmailCampaignBlast (Sends: %s, Opens: %s)>" % (self.sends, self.opens)

    @classmethod
    @contract
    def top_performing_email_campaign(cls, datetime_value, user_id):
        """
        This method returns top performing email campaign from a specific datetime
        :param int|long user_id: User Id
        :param string|datetime|None datetime_value: date during campaign started or updated
        :rtype: type(z)
        """
        assert isinstance(datetime_value, (datetime, basestring)) or datetime_value is None,\
            "Invalid datetime value"
        assert isinstance(user_id, (int, long)) and user_id, "Invalid User Id"
        from .user import User
        domain_id = User.get_domain_id(user_id)
        if isinstance(datetime_value, datetime):
            return cls.query.filter(or_(cls.updated_datetime >= datetime_value,
                                        cls.sent_datetime >= datetime_value)). \
                filter(EmailCampaign.id == cls.campaign_id, EmailCampaign.is_hidden == 0). \
                filter(cls.sends > 0).filter(and_(EmailCampaign.user_id == User.id, User.domain_id == domain_id)). \
                order_by(desc(cls.opens/cls.sends)).first()
        if isinstance(datetime_value, basestring):
            return cls.query.filter(or_(extract("year", cls.updated_datetime) == datetime_value,
                                        extract("year", cls.sent_datetime) == datetime_value)). \
                filter(EmailCampaign.id == cls.campaign_id, EmailCampaign.is_hidden == 0). \
                filter(and_(EmailCampaign.user_id == User.id, User.domain_id == domain_id)). \
                filter(cls.sends > 0). \
                order_by(desc(cls.opens/cls.sends)).first()
        return cls.query.filter(EmailCampaign.id == cls.campaign_id, EmailCampaign.is_hidden == 0).\
            filter(and_(EmailCampaign.user_id == User.id, User.domain_id == domain_id)).\
            filter(cls.sends > 0).order_by(desc(cls.opens/cls.sends)).first()


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
    updated_datetime = db.Column('UpdatedTime', db.DateTime, default=datetime.utcnow)
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

    @classmethod
    def get_already_emailed_candidates(cls, campaign):
        """
        Get candidates to whom email for specified campaign has already been sent.
        :param campaign: Valid campaign object.
        :return: Ids of candidates to whom email for specified campaign has already being sent.
        """
        if not isinstance(campaign, EmailCampaign):
            raise InternalServerError(error_message='Must provide valid EmailCampaign object.')

        already_emailed_candidates = cls.query.with_entities(
            cls.candidate_id).filter_by(campaign_id=campaign.id).all()
        emailed_candidate_ids = [row.candidate_id for row in already_emailed_candidates]
        return emailed_candidate_ids


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
    type = db.Column('Type', db.Integer, default=0)
    name = db.Column('Name', db.String(255), nullable=False)
    body_html = db.Column('EmailBodyHtml', db.Text)
    body_text = db.Column('EmailBodyText', db.Text)
    template_folder_id = db.Column('EmailTemplateFolderId', db.Integer,
                                   db.ForeignKey('email_template_folder.id', ondelete=u'SET NULL'), index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, default=0)
    updated_datetime = db.Column('UpdatedTime', db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    template_folder = relationship(u'EmailTemplateFolder', backref=db.backref('user_email_template',
                                                                              cascade="all, delete-orphan"))

    @classmethod
    def get_by_name(cls, template_name):
        """
        This filters email-templates for given name and returns first object
        :param string template_name: Name of email-template
        :rtype: UserEmailTemplate
        """
        return cls.query.filter_by(name=template_name.strip()).first()

    @classmethod
    def query_by_domain_id(cls, domain_id):
        """
        This returns query object to get email-templates in given domain_id.
        :param int|long domain_id: Id of domain of user
        :rtype: sqlalchemy.orm.query.Query
        """
        assert domain_id, 'domain_id not given'
        from user import User  # This has to be here to avoid circular import
        return cls.query.join(User).filter(User.domain_id == domain_id)

    @classmethod
    def get_valid_email_template(cls, email_template_id, user):
        """
        This validates given email_template_id is int or long greater than 0.
        It raises Invalid Usage error in case of invalid email_template_id.
        It raises ResourceNotFound error if requested template is not found in database.
        It raises Forbidden error if requested template template does not belong to user's domain.
        It returns EmailTemplate object if above validation does not raise any error.
        :param int|long email_template_id: Id of email-template
        :param User user: User object of logged-in user
        :rtype: UserEmailTemplate
        """
        raise_if_not_positive_int_or_long(email_template_id)
        # Get email-template object from database
        email_template = cls.get_by_id(email_template_id)
        if not email_template:
            raise ResourceNotFound('Email template(id:%d) not found' % email_template_id)
        # Verify owned by same domain
        template_owner_user = email_template.user
        if template_owner_user.domain_id != user.domain_id:
            raise ForbiddenError('Email template(id:%d) is not owned by domain(id:%d)'
                                 % (email_template_id, user.domain_id))
        return email_template


class EmailTemplateFolder(db.Model):
    __tablename__ = 'email_template_folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    parent_id = db.Column('ParentId', db.Integer,  db.ForeignKey('email_template_folder.id', ondelete='CASCADE'),
                          index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, default=0)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'), index=True)
    updated_datetime = db.Column('UpdatedTime', db.DateTime, nullable=False, default=datetime.utcnow)

    domain = relationship('Domain', backref=db.backref('email_template_folder', cascade="all, delete-orphan"))
    parent = relationship('EmailTemplateFolder', remote_side=[id], backref=db.backref('email_template_folder',
                                                                                      cascade="all, delete-orphan"))

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

    @classmethod
    def get_valid_template_folder(cls, template_folder_id, user):
        """
        This validates given template_folder_id is int or long greater than 0.
        It raises Invalid Usage error in case of invalid template_folder_id.
        It raises ResourceNotFound error if requested folder is not found in database.
        It raises Forbidden error if requested template folder does not belong to user's domain.
        It returns EmailTemplateFolder object if above validation does not raise any error.
        :param int|long template_folder_id: Id of email-template-folder
        :param User user: User object of logged-in user
        :rtype: EmailTemplateFolder
        """
        raise_if_not_positive_int_or_long(template_folder_id)
        # Get template-folder object from database
        template_folder = cls.get_by_id(template_folder_id)
        if not template_folder:
            raise ResourceNotFound('Email template folder(id:%s) not found' % template_folder_id)
        # Verify owned by same domain
        if not template_folder.domain_id == user.domain_id:
            raise ForbiddenError("Email template folder(id:%d) is not owned by user(id:%d)'s domain(id:%d)"
                                 % (template_folder_id, user.id, user.domain_id))
        return template_folder


class EmailClientCredentials(db.Model):
    __tablename__ = 'email_client_credentials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    host = db.Column('host', db.String(50), nullable=False)
    port = db.Column('port', db.String(5))
    name = db.Column('name', db.String(20), nullable=False)
    email = db.Column('email', db.String(60), nullable=False)
    password = db.Column('password', db.String(512), nullable=False)
    updated_datetime = db.Column('updated_datetime', db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    email_campaign = relationship('EmailCampaign', cascade='all, delete-orphan',
                                  passive_deletes=True, backref='email_client_credentials')

    email_conversations = relationship('EmailConversations', lazy='dynamic', cascade='all, delete-orphan',
                                       passive_deletes=True, backref='email_client_credentials')

    CLIENT_TYPES = {'incoming': 'incoming',
                    'outgoing': 'outgoing'}
    OUTGOING = ('smtp',)
    INCOMING = ('imap', 'pop')

    def __repr__(self):
        return "<EmailClientCredentials (id:%s)>" % self.id

    @classmethod
    def get_by_user_id_host_and_email(cls, user_id, host, email):
        """
        Method to get email_client_credentials objects for given params.
        :type user_id:  int | long
        :type host:  string
        :type email:  string
        :rtype:  list
        """
        assert user_id, "user_id not provided"
        assert host, "host not provided"
        assert email, "email not provided"
        return cls.filter_by_keywords(user_id=user_id, host=host, email=email)

    @classmethod
    def get_by_user_id_and_filter_by_name(cls, user_id, search_keyword):
        """
        This gets email-client-credentials for given user_id and search_keyword.
        Valid values of "search_keyword" are 'incoming' or 'outgoing'.
        :type user_id:  int | long
        :type search_keyword:  string
        :rtype: list
        """
        assert isinstance(user_id, (int, long)) and user_id, 'user_id not given'
        assert isinstance(search_keyword, basestring) and search_keyword, 'search_keyword not given'
        search_keyword = search_keyword.strip()
        if search_keyword not in cls.CLIENT_TYPES:
            raise InvalidUsage('Invalid value of param `type` provided')
        client_types = getattr(cls, search_keyword.upper())
        conditions = []
        for client_type in client_types:
            conditions.append(cls.host.ilike('%{}%'.format(client_type)))
        return cls.query.filter(or_(*conditions), cls.user_id == user_id).all()

    @classmethod
    def get_by_client_type(cls, client_type):
        """
        This gets email-client-credentials for given client type.
        Valid values of parameter are 'incoming' or 'outgoing'.
        :type client_type:  string
        :rtype: list
        """
        assert isinstance(client_type, basestring) and client_type, 'client_type not given'
        client_type = client_type.strip()
        if client_type not in cls.CLIENT_TYPES:
            raise InvalidUsage('Invalid value of param `client_type` provided')
        conditions = []
        for client_type in cls.INCOMING:
            conditions.append(cls.host.ilike('%{}%'.format(client_type)))
        return cls.query.filter(or_(*conditions)).all()


class EmailConversations(db.Model):
    __tablename__ = 'email_conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    candidate_id = db.Column('candidate_id', db.BIGINT, db.ForeignKey('candidate.Id', ondelete='CASCADE'))
    email_client_credentials_id = db.Column('email_client_credentials_id', db.Integer,
                                            db.ForeignKey('email_client_credentials.id', ondelete='CASCADE'))
    mailbox = db.Column('mailbox', db.String(10), nullable=False)
    subject = db.Column('subject', db.String(100), nullable=False)
    body = db.Column('body', db.String(1000), nullable=False)
    email_received_datetime = db.Column('email_received_datetime', db.DateTime, nullable=False)
    updated_datetime = db.Column('updated_datetime', db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "<EmailConversations (id:%s)>" % self.id

    def to_dict(self):
        """
        This creates response to return when an EmailConversation's object is requested.
        Response looks like
            {
                  "email_conversations":
                        [
                            {
                              "body": "Qui in non amet maiores alias excepturi id.",
                              "user_id": 1,
                              "updated_datetime": "2016-10-15 13:05:44",
                              "email_received_datetime": "2016-10-03 05:41:09",
                              "mailbox": "inbox",
                              "email_client_credentials": {
                                "id": 1,
                                "name": "Gmail"
                              },
                              "candidate_id": 362350,
                              "id": 1,
                              "subject": "377cc739-8e73-4a42-9d1b-114a75328280-test_email_campaign"
                            }
                        ]
            }
        :rtype: dict
        """
        email_conversation = self.get_by_id(self.id)
        return_dict = email_conversation.to_json()
        del return_dict['email_client_credentials_id']
        email_client_credentials = {"id": self.email_client_credentials.id,
                                    "name": self.email_client_credentials.name}
        return_dict.update({'email_client_credentials': email_client_credentials})
        return return_dict
