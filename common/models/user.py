from db import db
from sqlalchemy.orm import relationship, backref
import time
from common.utils.validators import is_number
import datetime

from candidate import CandidateSource
from associations import CandidateAreaOfInterest
from misc import AreaOfInterest


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column('domainId', db.Integer, db.ForeignKey('domain.id'))
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(512))
    device_token = db.Column('deviceToken', db.String(64))
    expiration = db.Column(db.DateTime)
    mobile_version = db.Column('mobileVersion', db.String(10))
    default_culture_id = db.Column('defaultCultureId', db.Integer, db.ForeignKey('culture.id'))
    phone = db.Column(db.String(50))
    get_started_data = db.Column('getStartedData', db.String(127))
    registration_key = db.Column(db.String(512))
    reset_password_key = db.Column(db.String(512))
    registration_id = db.Column(db.String(512))
    # name = db.Column(db.String(127))
    first_name = db.Column('firstName', db.String(255))
    last_name = db.Column('lastName', db.String(255))
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('updatedTime', db.DateTime)
    dice_user_id = db.Column('diceUserId', db.Integer)
    user_group_id = db.Column('userGroupId', db.Integer, db.ForeignKey('user_group.id'))
    # TODO: Set Nullable = False after setting user_group_id for existing data

    # Relationships
    candidates = relationship('Candidate', backref='user')
    public_candidate_sharings = relationship('PublicCandidateSharing', backref='user')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<email (email=' %r')>" % self.email


class Domain(db.Model):
    __tablename__ = 'domain'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    usage_limitation = db.Column('usageLimitation', db.Integer)
    expiration = db.Column(db.DateTime)
    added_time = db.Column('addedTime', db.DateTime)
    organization_id = db.Column('organizationId', db.Integer)
    is_fair_check_on = db.Column('isFairCheckOn', db.Boolean, default=False)
    is_active = db.Column('isActive', db.Boolean, default=True)  # TODO: store as 0 or 1
    default_tracking_code = db.Column('defaultTrackingCode', db.SmallInteger)
    default_culture_id = db.Column('defaultCultureId', db.Integer, default=1)
    default_from_name = db.Column('defaultFromName', db.String(255))
    settings_json = db.Column('settingsJson', db.Text)
    updated_time = db.Column('updatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    users = relationship('User', backref='domain')
    candidate_sources = relationship('CandidateSource', backref='domain')
    areas_of_interest = relationship('AreaOfInterest', backref='domain')

    def get_id(self):
        return unicode(self.id)


class WebAuthGroup(db.Model):
    __tablename__ = 'web_auth_group'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column('role', db.String(255))
    description = db.Column('description', db.TEXT)


class WebAuthMembership(db.Model):
    __tablename__ = 'web_auth_membership'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.String(255), db.ForeignKey('user.id'))
    group_id = db.Column('group_id', db.TEXT, db.ForeignKey('web_auth_group.id'))

    web_auth_group = relationship('WebAuthGroup', backref='web_auth_membership')
    user = relationship('User', backref='web_auth_membership')


class JobOpening(db.Model):
    __tablename__ = 'job_opening'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    job_code = db.Column('JobCode', db.String(100))
    description = db.Column('Description', db.String(500))
    title = db.Column('Title', db.String(150))
    added_time = db.Column('AddedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<JobOpening (title=' %r')>" % self.title


class Client(db.Model):
    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), nullable=False)

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
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    user_id = db.Column(
        db.INTEGER, db.ForeignKey('user.id')
    )
    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class DomainRole(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    roleName = db.Column(db.String(255), nullable=False, unique=True)

    domainId = db.Column(
        db.Integer, db.ForeignKey('domain.id')
    )
    domain = db.relationship('Domain')

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def save(role_name, domain_id=None):
        """ Create a new Role record with the supplied domain_id and role_name.
        :param int domain_id: domain id of a role.
        :param str role_name: role name of a role.
        """
        role = DomainRole(roleName=role_name, domainId=domain_id)
        db.session.add(role)
        db.session.commit()
        return role.id

    @staticmethod
    def get_by_id(role_id):
        """ Get a role with supplied role_id.
        :param int role_id: id of a role.
        """
        return DomainRole.query.get(role_id)

    @staticmethod
    def get_by_name(role_name):
        """ Get a role with supplied role_name.
        :param str role_name: Name of a role.
        """
        return DomainRole.query.filter_by(roleName=role_name).first()

    @staticmethod
    def all():
        """ Get all roles_ids in database """
        return DomainRole.query.all() or []

    @staticmethod
    def all_roles_of_domain(domain_id):
        """ Get all roles with names for a given domain_id
        :param int domain_id: id of a domain.
        """
        return DomainRole.query.filter_by(domainId=domain_id) or []


class UserScopedRoles(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(
        db.INTEGER, db.ForeignKey('user.id'), nullable=False
    )
    roleId = db.Column(
        db.Integer, db.ForeignKey('domain_role.id'), nullable=False
    )
    domainRole = db.relationship('DomainRole')

    @staticmethod
    def add_roles(user_id, roles_list):
        """ Add a role for user
        :param int user_id: Id of a user
        :param list[int | str] roles_list: list of roleIds or roleNames or both
        """
        user = User.query.get(user_id)
        if user:
            for role in roles_list:
                if is_number(role):
                    role_id = role
                else:
                    domain_role = DomainRole.get_by_name(role)
                    if domain_role:
                        role_id = domain_role.id
                    else:
                        raise Exception("Role: %s doesn't exist or" % role)
                domain_role = DomainRole.query.get(role_id)
                if role_id and domain_role and (not domain_role.domainId or domain_role.domainId == user.domain_id):
                    if not UserScopedRoles.query.filter((UserScopedRoles.userId == user_id) &
                                                                (UserScopedRoles.roleId == role_id)).first():
                        user_scoped_role = UserScopedRoles(userId=user_id, roleId=role_id)
                        db.session.add(user_scoped_role)
                    else:
                        raise Exception("Role: %s already exists for user: %s" % (role, user_id))
                else:
                    raise Exception("Role: %s doesn't exist or it belongs to a different domain" % role)
            db.session.commit()
        else:
            raise Exception("User %s doesn't exist" % user_id)

    @staticmethod
    def delete_roles(user_id, roles_list):
        """ Delete a role for user
        :param int user_id: Id of a user
        :param list[int | str] roles_list: list of roleIds or roleNames or both
        """
        if User.query.get(user_id):
            for role in roles_list:
                if is_number(role):
                    role_id = role
                else:
                    domain_role = DomainRole.get_by_name(role)
                    if domain_role:
                        role_id = domain_role.id
                    else:
                        role_id = None

                user_scoped_role = UserScopedRoles.query.filter((UserScopedRoles.userId == user_id)
                                                                & (UserScopedRoles.roleId == role_id)).first()
                if user_scoped_role:
                    db.session.delete(user_scoped_role)
                else:
                    raise Exception("User %s doesn't have any role %s" % (user_id, role_id))
            db.session.commit()
        else:
            raise Exception("User %s doesn't exist" % user_id)

    @staticmethod
    def get_all_roles_of_user(user_id):
        """ Get all roles for a user
        :param int user_id: Id of a user
        """
        return UserScopedRoles.query.filter_by(userId=user_id).all() or []


class UserGroup(db.Model):
    __tablename__ = 'user_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(225), nullable=True)
    domain_id = db.Column(
        db.Integer, db.ForeignKey('domain.id'), nullable=False
    )
    domain = db.relationship('Domain')
    users = relationship('User', backref='user_group')

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_by_id(user_group_id):
        """ Get a user group with supplied user_group_id.
        :param int user_group_id: id of a user group.
        """
        return UserGroup.query.get(user_group_id)

    @staticmethod
    def get_by_name(group_name):
        """ Get a user group with supplied group_name.
        :param str group_name: Name of a user group.
        """
        return UserGroup.query.filter_by(name=group_name).first()

    @staticmethod
    def all():
        """ Get all groups_ids in database """
        return UserGroup.query.all() or []

    @staticmethod
    def add_groups(groups, domain_id):
        """ Add new user groups.
        :param list[dict] groups: List of the user groups
        :param int domain_id: Domain Id of the user groups.
        """
        for group in groups:
            name = group.get('group_name')
            description = group.get('group_description')
            group_domain_id = group.get('domain_id') or domain_id
            already_existing_group = UserGroup.query.filter_by(name=name).first() or None
            if not already_existing_group or already_existing_group.domain_id != group_domain_id:
                user_group = UserGroup(name=name, description=description, domain_id=group_domain_id)
            else:
                raise Exception("Group '%s' already exists in same domain so it cannot be added again" % name)
            db.session.add(user_group)
        db.session.commit()

    @staticmethod
    def all_groups_of_domain(domain_id):
        """ Get all user_groups of with names in database
        :param int domain_id: id of a domain.
        """
        return UserGroup.query.filter_by(domain_id=domain_id) or []

    @staticmethod
    def all_users_of_group(group_id):
        """ Get all users of a group
        :param int group_id: group id of a user groups
        """
        return User.query.filter_by(user_group_id=group_id) or []

    @staticmethod
    def delete_groups(domain_id, groups):
        """ Delete few or all groups of a domain
        :param int domain_id: id of a domain
        :param list[int | str] groups: list of names or ids of user groups
        """
        if Domain.query.get(domain_id):
            for group in groups:
                if is_number(group):
                    group_id = group
                else:
                    user_group = UserGroup.query.filter_by(name=group).first()
                    if user_group:
                        group_id = user_group.id
                    else:
                        group_id = None

                group = UserGroup.query.get(group_id) or None if group_id else None
                if group and group.domain_id == domain_id:
                    db.session.delete(group)
                else:
                    raise Exception("Group %s doesn't exist or either it doesn't belong to Domain %s " % (group_id, domain_id))
            db.session.commit()
        else:
            raise Exception("Domain %s doesn't exist" % domain_id)

    @staticmethod
    def add_users_to_group(group_id, user_ids):
        """
        :param int group_id: id of a user group
        :param list[int] user_ids: list of ids of users
        """
        user_group = UserGroup.query.get(group_id)
        if user_group:
            for user_id in user_ids:
                user = User.query.get(user_id) or None
                if user and user.domain_id == user_group.domain_id:
                    user.user_group_id = group_id
                else:
                    raise Exception("User: %s doesn't exist or either it doesn't belong to same Domain %s as user group"
                                    % (user_id, user_group.domain_id))
            db.session.commit()
        else:
            raise Exception("User group %s doesn't exist" % group_id)
