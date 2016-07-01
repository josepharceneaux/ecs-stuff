import datetime
import os
import time
import uuid

from flask import request
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash

from db import db
from ..models.event import Event
from candidate import CandidateSource
from associations import CandidateAreaOfInterest
from event_organizer import EventOrganizer
from misc import AreaOfInterest
from email_campaign import EmailCampaign
from ..error_handling import *
from ..redis_cache import redis_store
from ..utils.validators import is_number
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from ..error_codes import ErrorCodes


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column('Id', db.BIGINT, primary_key=True)
    domain_id = db.Column('domainId', db.Integer, db.ForeignKey('domain.Id'))
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(512))
    device_token = db.Column('deviceToken', db.String(64))
    expiration = db.Column(db.DateTime)
    mobile_version = db.Column('mobileVersion', db.String(10))
    default_culture_id = db.Column('defaultCultureId', db.Integer, db.ForeignKey('culture.Id'))
    phone = db.Column(db.String(50))
    get_started_data = db.Column('getStartedData', db.String(127))
    registration_key = db.Column(db.String(512))
    reset_password_key = db.Column(db.String(512))
    registration_id = db.Column(db.String(512))
    # name = db.Column(db.String(127))
    first_name = db.Column('firstName', db.String(255))
    last_name = db.Column('lastName', db.String(255))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.utcnow)
    updated_time = db.Column('updatedTime', db.DateTime, default=datetime.datetime.utcnow)
    password_reset_time = db.Column('passwordResetTime', db.DateTime, default=datetime.datetime.utcnow)
    dice_user_id = db.Column('diceUserId', db.Integer)
    user_group_id = db.Column('userGroupId', db.Integer, db.ForeignKey('user_group.Id', ondelete='CASCADE'))
    last_read_datetime = db.Column('lastReadDateTime', db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    thumbnail_url = db.Column('thumbnailUrl', db.TEXT)
    is_disabled = db.Column(TINYINT, default='0', nullable=False)
    locale = db.Column(db.String(10), default='en-US')
    # TODO: Set Nullable = False after setting user_group_id for existing data
    ats_enabled = db.Column(db.Boolean, default=False)

    # Relationships
    candidates = relationship('Candidate', backref='user')
    public_candidate_sharings = relationship('PublicCandidateSharing', backref='user')
    user_group = relationship('UserGroup', backref='user')
    user_phones = relationship('UserPhone', cascade='all,delete-orphan', passive_deletes=True,
                               backref='user')
    email_campaigns = relationship('EmailCampaign', backref='user')
    email_templates = relationship('UserEmailTemplate', backref='user', cascade='all, delete-orphan')
    push_campaigns = relationship('PushCampaign', backref='user', cascade='all,delete-orphan', passive_deletes=True, )
    user_credentials = db.relationship('UserSocialNetworkCredential', backref='user')
    events = db.relationship(Event, backref='user', lazy='dynamic',
                             cascade='all, delete-orphan', passive_deletes=True)
    event_organizers = db.relationship('EventOrganizer', backref='user', lazy='dynamic',
                                       cascade='all, delete-orphan', passive_deletes=True)
    venues = db.relationship('Venue', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan', passive_deletes=True)

    @staticmethod
    def generate_jw_token(expiration=600, user_id=None):
        secret_key_id = str(uuid.uuid4())[0:10]
        secret_key = os.urandom(24)
        redis_store.setex(secret_key_id, secret_key, expiration)
        s = Serializer(secret_key, expires_in=expiration)
        return secret_key_id, 'Bearer %s' % s.dumps({'user_id': user_id})

    @staticmethod
    def verify_jw_token(secret_key_id, token, allow_null_user=False):
        s = Serializer(redis_store.get(secret_key_id))
        try:
            data = s.loads(token)
        except SignatureExpired:
            raise UnauthorizedError(error_message="Your JSON web token has been expired")
        except BadSignature:
            raise UnauthorizedError(error_message="Your JSON web token is not valid")

        if data['user_id']:
            user = User.query.get(data['user_id'])
            if user:
                request.user = user
                return
        elif allow_null_user:
            request.user = None
            return

        raise UnauthorizedError(error_message="User %s doesn't exist in database" % data['user_id'])

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    @property
    def name(self):
        return (self.first_name or '') + ' ' + (self.last_name or '')

    def __repr__(self):
        return "<email (email=' %r')>" % self.email

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def all_users_of_domain(domain_id):
        """ Get user_ids of all users of a given domain_id
        :param int domain_id: id of a domain.
        :rtype: list[User]
        """
        return User.query.filter_by(domain_id=domain_id).all()

    @classmethod
    def get_domain_id(cls, _id):
        user = cls.query.filter_by(id=_id).first()
        return user.domain_id if user else None

    # ***** Below function to be used for testing only *****
    @staticmethod
    def add_test_user(session, password, domain_id, user_group_id):
        """
        Function creates a unique user for testing
        :rtype: User
        """
        user = User(email='{}@example.com'.format(uuid.uuid4().__str__()),
                    password=generate_password_hash(password, method='pbkdf2:sha512'),
                    domain_id=domain_id,
                    user_group_id=user_group_id,
                    expiration=None)
        session.add(user)
        session.commit()
        return user

    @staticmethod
    def get_by_email(email):
        """
        This method returns a user with specified email or None if not found.
        :param (str) email: user email address
        :rtype User | None
        """
        return User.query.filter_by(email=email).first()


class UserPhone(db.Model):
    __tablename__ = 'user_phone'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    phone_label_id = db.Column(db.Integer, db.ForeignKey('phone_label.Id', ondelete='CASCADE'))
    value = db.Column(db.String(50), nullable=False)

    # Relationship
    sms_campaigns = relationship('SmsCampaign', backref='user_phone')

    def __repr__(self):
        return "<UserPhone (value=' %r')>" % self.value

    @classmethod
    def get_by_user_id(cls, user_id):
        if not isinstance(user_id, (int, long)):
            raise InvalidUsage('Invalid user_id provided')
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_user_id_and_phone_label_id(cls, user_id, phone_label_id):
        if not isinstance(user_id, (int, long)):
            raise InvalidUsage('Invalid user_id provided')
        if not isinstance(phone_label_id, (int, long)):
            raise InvalidUsage('Invalid phone_label_id provided')
        return cls.query.filter_by(user_id=user_id, phone_label_id=phone_label_id).all()

    @classmethod
    def get_by_phone_value(cls, phone_value):
        if not isinstance(phone_value, basestring):
            raise InvalidUsage("phone_value is invalid")
        return cls.query.filter_by(value=phone_value).all()


class Domain(db.Model):
    __tablename__ = 'domain'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(50))
    usage_limitation = db.Column('UsageLimitation', db.Integer)
    organization_id = db.Column('OrganizationId', db.Integer)
    is_fair_check_on = db.Column('IsFairCheckOn', db.Boolean, default=False)
    is_active = db.Column('IsActive', db.Boolean, default=True)
    default_tracking_code = db.Column('DefaultTrackingCode', db.SmallInteger)
    default_culture_id = db.Column('DefaultCultureId', db.Integer, default=1)
    settings_json = db.Column('SettingsJson', db.Text)
    expiration = db.Column('Expiration', db.DateTime)
    added_time = db.Column('AddedTime', db.DateTime)
    default_from_name = db.Column('DefaultFromName', db.String(255))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)
    dice_company_id = db.Column('DiceCompanyId', db.Integer, index=True)
    is_disabled = db.Column(TINYINT, default='0', nullable=False)

    # Relationships
    users = relationship('User', backref='domain')
    candidate_sources = relationship('CandidateSource', backref='domain')
    areas_of_interest = relationship('AreaOfInterest', backref='domain')
    custom_fields = relationship('CustomField', backref='domain')

    def get_id(self):
        return unicode(self.id)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # ***** Below functions to be used for testing only *****
    @staticmethod
    def add_test_domain(session):
        """
        Function creates a unique domain + domain's UserGroup for testing
        :return:
        """
        domain = Domain(name='{}'.format(uuid.uuid4().__str__()[0:8]),
                        expiration='0000-00-00 00:00:00')
        session.add(domain)
        session.commit()
        return domain


class WebAuthGroup(db.Model):
    __tablename__ = 'web_auth_group'
    id = db.Column(db.BIGINT, primary_key=True)
    role = db.Column(db.String(255))
    description = db.Column(db.TEXT)

    def __repr__(self):
        return "<WebAuthGroup (id = {})>".format(self.id)


class WebAuthMembership(db.Model):
    __tablename__ = 'web_auth_membership'
    id = db.Column(db.BIGINT, primary_key=True)
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id'))
    group_id = db.Column(db.BIGINT, db.ForeignKey('web_auth_group.id'))

    # Relationship
    web_auth_group = relationship('WebAuthGroup', backref='web_auth_membership')
    user = relationship('User', backref='web_auth_membership')

    def __repr__(self):
        return "<WebAuthMembership (id = {})>".format(self.id)


class JobOpening(db.Model):
    __tablename__ = 'job_opening'
    id = db.Column('Id', db.BIGINT, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id'))
    job_code = db.Column('JobCode', db.String(100))
    description = db.Column('Description', db.String(500))
    title = db.Column('Title', db.String(150))
    added_time = db.Column('AddedTime', db.TIMESTAMP, default=time.time)

    def __repr__(self):
        return "<JobOpening (title=' %r')>" % self.title


class Client(db.Model):
    __tablename__ = 'client'
    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), nullable=False)
    client_name = db.Column(db.String(255))

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # Possible values are 'public' or 'confidential'
    @property
    def client_type(self):
        return 'confidential'

    @property
    def allowed_grant_types(self):
        return ['password', 'refresh_token']

    @property
    def default_scopes(self):
        return []

    @property
    def default_redirect_uri(self):
        return ''


class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(40), db.ForeignKey('client.client_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'), nullable=False)
    token_type = db.Column(db.String(40))
    access_token = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), unique=True, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)
    _scopes = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint("client_id", "user_id", name="client_user_key"),
    )

    # Relationships
    user = db.relationship('User', backref=db.backref('token', cascade="all, delete-orphan"))
    client = db.relationship('Client', backref=db.backref('token', cascade="all, delete-orphan"))

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @property
    def scopes(self):
        return self._scopes.split() if self._scopes else []

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Filter Token based on user_id and return token from db
        :param user_id: User id whose token is required
        :return: Token object matched with access_token
        """
        assert user_id, "user_id is None"
        return cls.query.filter(cls.user_id == user_id).first()

    @staticmethod
    def get_token(access_token):
        """
        Filter Token based on access_token and return token object from db
        :param access_token: User access_token
        :return: Token object matched with access_token
        """
        assert access_token, "access_token is empty"
        return Token.query.filter_by(access_token=access_token).first()


class DomainRole(db.Model):
    __tablename__ = 'domain_role'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(255), nullable=False, unique=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'), nullable=True)

    domain = db.relationship('Domain', backref=db.backref('domain_role', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<DomainRole (id = {})>".format(self.id)

    class Roles(object):
        """
        Class entails constants that point to available user-role names
        """
        # Candidate Resources
        CAN_ADD_CANDIDATES = "CAN_ADD_CANDIDATES"
        CAN_GET_CANDIDATES = "CAN_GET_CANDIDATES"
        CAN_EDIT_CANDIDATES = "CAN_EDIT_CANDIDATES"
        CAN_DELETE_CANDIDATES = "CAN_DELETE_CANDIDATES"

        # User Roles
        CAN_GET_USER_ROLES = "CAN_GET_USER_ROLES"
        CAN_ADD_USER_ROLES = "CAN_ADD_USER_ROLES"
        CAN_DELETE_USER_ROLES = "CAN_DELETE_USER_ROLES"

        # User Groups
        CAN_GET_GROUP_USERS = "CAN_GET_GROUP_USERS"
        CAN_ADD_GROUP_USERS = "CAN_ADD_GROUP_USERS"

        # User Resources
        CAN_ADD_USERS = "CAN_ADD_USERS"
        CAN_GET_USERS = "CAN_GET_USERS"
        CAN_EDIT_USERS = "CAN_EDIT_USERS"
        CAN_DELETE_USERS = "CAN_DELETE_USERS"

        # Domain
        CAN_GET_DOMAINS = "CAN_GET_DOMAINS"
        CAN_ADD_DOMAINS = "CAN_ADD_DOMAINS"
        CAN_DELETE_DOMAINS = "CAN_DELETE_DOMAINS"
        CAN_EDIT_DOMAINS = "CAN_EDIT_DOMAINS"

        # Domain Roles
        CAN_ADD_DOMAIN_ROLES = "CAN_ADD_DOMAIN_ROLES"
        CAN_GET_DOMAIN_ROLES = "CAN_GET_DOMAIN_ROLES"
        CAN_EDIT_DOMAIN_ROLES = "CAN_EDIT_DOMAIN_ROLES"
        CAN_DELETE_DOMAIN_ROLES = "CAN_DELETE_DOMAIN_ROLES"

        # Domain Groups
        CAN_GET_DOMAIN_GROUPS = "CAN_GET_DOMAIN_GROUPS"
        CAN_ADD_DOMAIN_GROUPS = "CAN_ADD_DOMAIN_GROUPS"
        CAN_EDIT_DOMAIN_GROUPS = "CAN_EDIT_DOMAIN_GROUPS"
        CAN_DELETE_DOMAIN_GROUPS = "CAN_DELETE_DOMAIN_GROUPS"

        # Talent Pipelines
        CAN_ADD_TALENT_PIPELINES = "CAN_ADD_TALENT_PIPELINES"
        CAN_GET_TALENT_PIPELINES = "CAN_GET_TALENT_PIPELINES"
        CAN_EDIT_TALENT_PIPELINES = "CAN_EDIT_TALENT_PIPELINES"
        CAN_DELETE_TALENT_PIPELINES = "CAN_DELETE_TALENT_PIPELINES"

        # Talent Pools' Resources
        CAN_ADD_TALENT_POOLS = "CAN_ADD_TALENT_POOLS"
        CAN_GET_TALENT_POOLS = "CAN_GET_TALENT_POOLS"
        CAN_EDIT_TALENT_POOLS = "CAN_EDIT_TALENT_POOLS"
        CAN_DELETE_TALENT_POOLS = "CAN_DELETE_TALENT_POOLS"
        CAN_GET_TALENT_PIPELINES_OF_TALENT_POOLS = "CAN_GET_TALENT_PIPELINES_OF_TALENT_POOLS"

        # Talent Pool Group
        CAN_GET_TALENT_POOLS_OF_GROUP = "CAN_GET_TALENT_POOLS_OF_GROUP"
        CAN_DELETE_TALENT_POOLS_FROM_GROUP = "CAN_DELETE_TALENT_POOLS_FROM_GROUP"
        CAN_ADD_TALENT_POOLS_TO_GROUP = "CAN_ADD_TALENT_POOLS_TO_GROUP"

        # Candidate from Talent Pool
        CAN_GET_CANDIDATES_FROM_TALENT_POOL = "CAN_GET_CANDIDATES_FROM_TALENT_POOL"
        CAN_ADD_CANDIDATES_TO_TALENT_POOL = "CAN_ADD_CANDIDATES_TO_TALENT_POOL"
        CAN_DELETE_CANDIDATES_FROM_TALENT_POOL = "CAN_DELETE_CANDIDATES_FROM_TALENT_POOL"

        # Talent Pipeline Candidates
        CAN_GET_TALENT_PIPELINE_CANDIDATES = "CAN_GET_TALENT_PIPELINE_CANDIDATES"

        # Smart List
        CAN_ADD_SMART_LISTS_STATS = "CAN_ADD_SMART_LISTS_STATS"
        CAN_GET_SMART_LISTS_STATS = "CAN_GET_SMART_LISTS_STATS"
        CAN_EDIT_SMART_LISTS_STATS = "CAN_EDIT_SMART_LISTS_STATS"
        CAN_DELETE_SMART_LISTS_STATS = "CAN_DELETE_SMART_LISTS_STATS"

        # Talent Pipelines' Stats
        CAN_ADD_TALENT_PIPELINES_STATS = "CAN_ADD_TALENT_PIPELINES_STATS"
        CAN_GET_TALENT_PIPELINES_STATS = "CAN_GET_TALENT_PIPELINES_STATS"
        CAN_DELETE_TALENT_PIPELINES_STATS = "CAN_DELETE_TALENT_PIPELINES_STATS"

        # Talent Pipeline Smart lists
        CAN_ADD_TALENT_PIPELINE_SMART_LISTS = "CAN_ADD_TALENT_PIPELINE_SMART_LISTS"
        CAN_GET_TALENT_PIPELINE_SMART_LISTS = "CAN_GET_TALENT_PIPELINE_SMART_LISTS"
        CAN_EDIT_TALENT_PIPELINE_SMART_LISTS = "CAN_EDIT_TALENT_PIPELINE_SMART_LISTS"
        CAN_DELETE_TALENT_PIPELINE_SMART_LISTS = "CAN_DELETE_TALENT_PIPELINE_SMART_LISTS"

        # Admin Roles
        CAN_EDIT_OTHER_DOMAIN_INFO = "CAN_EDIT_OTHER_DOMAIN_INFO"

        # Email Template Roles
        CAN_CREATE_EMAIL_TEMPLATE = "CAN_CREATE_EMAIL_TEMPLATE"
        CAN_GET_EMAIL_TEMPLATE = "CAN_GET_EMAIL_TEMPLATE"
        CAN_UPDATE_EMAIL_TEMPLATE = "CAN_UPDATE_EMAIL_TEMPLATE"
        CAN_DELETE_EMAIL_TEMPLATE = "CAN_DELETE_EMAIL_TEMPLATE"

        # Email Template Folder Roles
        CAN_CREATE_EMAIL_TEMPLATE_FOLDER = "CAN_CREATE_EMAIL_TEMPLATE_FOLDER"
        CAN_DELETE_EMAIL_TEMPLATE_FOLDER = "CAN_DELETE_EMAIL_TEMPLATE_FOLDER"

        CAN_IMPERSONATE_USERS = "CAN_IMPERSONATE_USERS"

        # Scheduler Admin Role
        CAN_GET_ALL_SCHEDULER_JOBS = "CAN_GET_ALL_SCHEDULER_JOBS"

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def save(role_name, domain_id=None):
        """
        Create a new Role record with the supplied domain_id and role_name. If domain_id is provided then role
        would be domain specific otherwise it would be general
        :param int | None domain_id: domain id of a role.
        :param basestring role_name: role name of a role.
        :rtype: int
        """
        role = DomainRole(role_name=role_name, domain_id=domain_id)
        db.session.add(role)
        db.session.commit()
        return role.id

    @staticmethod
    def get_by_id(role_id):
        """ Get a role with supplied role_id.
        :param int role_id: id of a role.
        :rtype: DomainRole
        """
        return DomainRole.query.get(role_id)

    @staticmethod
    def get_by_name(role_name):
        """ Get a role with supplied role_name.
        :param str role_name: Name of a role.
        :rtype: DomainRole
        """
        return DomainRole.query.filter_by(role_name=role_name).first()

    @staticmethod
    def get_by_names(role_names):
        """ Get a role with supplied role_name.
        :param list[str] role_names: List of role names.
        :rtype: list[DomainRole]
        """
        return DomainRole.query.filter(DomainRole.role_name.in_(role_names)).all()

    @staticmethod
    def all():
        """
        Get all roles_ids in database
        :rtype: list[DomainRole]
        """
        return DomainRole.query.all()

    @staticmethod
    def all_roles_of_domain(domain_id):
        """ Get all roles with names for a given domain_id
        :param int domain_id: id of a domain.
        :rtype: list[DomainRole]
        """
        return DomainRole.query.filter_by(domain_id=domain_id).all()


class UserScopedRoles(db.Model):
    __tablename__ = 'user_scoped_roles'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'), nullable=False)
    role_id = db.Column('RoleId', db.Integer, db.ForeignKey('domain_role.id', ondelete='CASCADE'), nullable=False)
    domain_role = db.relationship('DomainRole', backref=db.backref('user_scoped_roles', cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('user_scoped_roles', cascade="all, delete-orphan"))

    def __repr__(self):
        return "<UserScopedRoles (id = {})>".format(self.id)

    @staticmethod
    def add_roles(user, roles_list):
        """ Add a role for user
        :param User user: user object
        :param list[int | str] roles_list: list of role_ids or role_names or both
        :rtype: None
        """
        if user:
            for role in roles_list:
                if is_number(role):
                    role_id = int(role)
                else:
                    domain_role = DomainRole.get_by_name(role)
                    if domain_role:
                        role_id = domain_role.id
                    else:
                        raise InvalidUsage(error_message="Role: %s doesn't exist" % role)
                domain_role = DomainRole.query.get(role_id)
                if domain_role and (not domain_role.domain_id or domain_role.domain_id == user.domain_id):
                    if not UserScopedRoles.query.filter((UserScopedRoles.user_id == user.id) &
                                                                (UserScopedRoles.role_id == role_id)).first():
                        user_scoped_role = UserScopedRoles(user_id=user.id, role_id=role_id)
                        db.session.add(user_scoped_role)
                    else:
                        raise InvalidUsage(error_message="Role: %s already exists for user: %s" % (role, user.id),
                                           error_code=ErrorCodes.ROLE_ALREADY_EXISTS)
                else:
                    raise InvalidUsage(
                        error_message="Role: %s doesn't exist or it belongs to a different domain" % role)
            db.session.commit()
        else:
            raise InvalidUsage(error_message="User %s doesn't exist" % user.id)

    @staticmethod
    def delete_roles(user, roles_list):
        """ Delete a role for user
        :param User user: user object
        :param list[int | str] roles_list: list of role_ids or role_names or both
        :rtype: None
        """
        for role in roles_list:
            if is_number(role):
                role_id = int(role)
            else:
                domain_role = DomainRole.get_by_name(role)
                if domain_role:
                    role_id = domain_role.id
                else:
                    raise InvalidUsage(error_message="Domain role %s doesn't exist" % role)

            user_scoped_role = UserScopedRoles.query.filter((UserScopedRoles.user_id == user.id)
                                                            & (UserScopedRoles.role_id == role_id)).first()
            if user_scoped_role:
                db.session.delete(user_scoped_role)
            else:
                raise InvalidUsage(error_message="User %s doesn't have any role %s or " % (user.id, role_id))
        db.session.commit()

    @staticmethod
    def get_all_roles_of_user(user_id):
        """ Get all roles for a user
        :param int user_id: Id of a user
        :rtype: list[UserScopedRoles]
        """
        return UserScopedRoles.query.filter_by(user_id=user_id).all()


class UserGroup(db.Model):
    __tablename__ = 'user_group'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(255), nullable=False)
    description = db.Column('Description', db.String(225), nullable=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'),
                          nullable=False)

    domain = db.relationship('Domain', backref=db.backref('user_group', cascade="all, delete-orphan"))

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_by_id(user_group_id):
        """ Get a user group with supplied user_group_id.
        :param int user_group_id: id of a user group.
        :rtype: UserGroup
        """
        return UserGroup.query.get(user_group_id)

    @staticmethod
    def get_by_name(group_name):
        """ Get a user group with supplied group_name.
        :param str group_name: Name of a user group.
        :rtype: UserGroup
        """
        return UserGroup.query.filter_by(name=group_name).first()

    @staticmethod
    def all():
        """
        Get all groups_ids in database
        :rtype: list[UserGroup]
        """
        return UserGroup.query.all()

    @staticmethod
    def add_groups(groups, domain_id):
        """ Add new user groups.
        :param list[dict] groups: List of the user groups
        :param int domain_id: Domain Id of the user groups
        :return: An array consisting of all UserGroup objects which have been added to a domain successfully
        :rtype: list[UserGroup]
        """
        user_groups = []
        for group in groups:
            if not isinstance(group, dict):
                raise InvalidUsage(error_message="Request body is not properly formatted")
            name = group.get('name') or 'default'
            description = group.get('description')
            already_existing_group = UserGroup.query.filter_by(name=name, domain_id=domain_id).first()
            if not already_existing_group:
                user_group = UserGroup(name=name, description=description, domain_id=domain_id)
            else:
                raise InvalidUsage(error_message="Group '%s' already exists in same domain so it cannot be "
                                                 "added again" % name)
            db.session.add(user_group)
            user_groups.append(user_group)
        db.session.commit()
        return user_groups

    @staticmethod
    def all_groups_of_domain(domain_id):
        """ Get all user_groups of with names in database
        :param int domain_id: id of a domain.
        :rtype: list[UserGroup]
        """
        return UserGroup.query.filter_by(domain_id=domain_id).all()

    @staticmethod
    def all_users_of_group(group_id):
        """ Get all users of a group
        :param int group_id: group id of a user groups
        :rtype: list[User]
        """
        return User.query.filter_by(user_group_id=group_id).all()

    @staticmethod
    def delete_groups(domain_id, groups):
        """ Delete few or all groups of a domain
        :param int domain_id: id of a domain
        :param list[int | str] groups: list of names or ids of user groups
        :rtype: None
        """
        if Domain.query.get(domain_id):
            for group in groups:
                if not isinstance(group, basestring) and not isinstance(group, (int, long)):
                    raise InvalidUsage(error_message="Request body is not properly formatted")
                if is_number(group):
                    group_id = group
                else:
                    user_group = UserGroup.query.filter_by(name=group, domain_id=domain_id).first()
                    if user_group:
                        group_id = user_group.id
                    else:
                        group_id = None

                group = UserGroup.query.filter_by(id=group_id, domain_id=domain_id).first() or group_id
                if group:
                    db.session.delete(group)
                else:
                    raise InvalidUsage(error_message="Group %s doesn't exist or either it doesn't belong to "
                                                     "Domain %s " % (group_id, domain_id))
            db.session.commit()
        else:
            raise InvalidUsage(error_message="Domain %s doesn't exist" % domain_id)

    @staticmethod
    def add_users_to_group(user_group, user_ids):
        """
        :param UserGroup user_group: user group
        :param list[int] user_ids: list of ids of users
        :rtype: None
        """
        for user_id in user_ids:
            assert is_number(user_id)
            user = User.query.get(user_id) or None
            if user and user.domain_id == user_group.domain_id:
                if user.user_group_id == user_group.id:
                    raise InvalidUsage("User %s already belongs to user group %s" % (user_id, user_group.id))
                else:
                    user.user_group_id = user_group.id
            else:
                raise InvalidUsage(error_message="User: %s doesn't exist or either it doesn't belong to same Domain "
                                                 "%s as user group" % (user_id, user_group.domain_id))
        db.session.commit()


class UserSocialNetworkCredential(db.Model):
    """ This represents database table that holds user's credentials of a social network. """
    __tablename__ = 'user_social_network_credential'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'), nullable=False)
    social_network_id = db.Column('SocialNetworkId', db.Integer,
                                  db.ForeignKey('social_network.Id', ondelete='CASCADE'), nullable=False)
    refresh_token = db.Column('RefreshToken', db.String(1000))
    webhook = db.Column(db.String(200))
    member_id = db.Column('MemberId', db.String(100))
    access_token = db.Column('AccessToken', db.String(1000))
    social_network = db.relationship("SocialNetwork", backref=db.backref(
        'user_social_network_credential', cascade="all, delete-orphan"))

    @classmethod
    def get_all_credentials(cls, social_network_id=None):
        if not social_network_id:
            return cls.query.all()
        else:
            return cls.get_user_credentials_of_social_network(social_network_id)

    @classmethod
    def get_user_credentials_of_social_network(cls, social_network_id):
        assert social_network_id
        return cls.query.filter(cls.social_network_id == social_network_id).all()

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id
        return cls.query.filter(cls.user_id == user_id).all()

    @classmethod
    def get_by_user_and_social_network_id(cls, user_id, social_network_id):
        assert user_id and social_network_id
        return cls.query.filter(
            db.and_(cls.user_id == user_id, cls.social_network_id == social_network_id)).first()

    @classmethod
    def update_auth_token(cls, user_id, social_network_id, access_token):
        # TODO improve this method
        success = False
        user = cls.get_by_user_and_social_network(user_id, social_network_id)
        if user:
            user.update(access_token=access_token)
            success = True
        return success

    @classmethod
    def get_by_webhook_id_and_social_network_id(cls, webhook_id, social_network_id):
        assert webhook_id and social_network_id
        return cls.query.filter(
            db.and_(cls.webhook == webhook_id, cls.social_network_id == social_network_id)).one()
