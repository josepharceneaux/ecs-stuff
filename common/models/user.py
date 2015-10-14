from db import db
from sqlalchemy.orm import relationship, backref
import time
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
    group_id = db.Column('groupId', db.Integer, db.ForeignKey('user_groups.id'))
    # TODO: Set Nullable = False after setting group_id for existing data

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
        # db.BigInteger, db.ForeignKey('user.id')
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
    def save(domain_id, role_name):
        """ Create a new Role record with the supplied domain_id and role_name.
        :param domain_id: domain id of a role.
        :param role_name: role name of a role.
        """
        role = DomainRole(roleName=role_name, domainId=domain_id)
        db.session.add(role)
        db.session.commit()
        return role.id

    @staticmethod
    def get_by_id(role_id):
        """ Get a role with supplied role_id.
        :param role_id: id of a role.
        """
        return DomainRole.query.get(role_id)

    @staticmethod
    def get_by_name(role_name):
        """ Get a role with supplied role_name.
        :param role_name: Name of a role.
        """
        return DomainRole.query.filter_by(roleName=role_name).first()

    @staticmethod
    def all():
        """ Get all roles_ids in database """
        all_roles = DomainRole.query.all() or []
        return dict(roles=[all_role.id for all_role in all_roles])

    @staticmethod
    def all_roles_of_domain(domain_id):
        """ Get all roles with names in database """
        all_roles_of_domain = DomainRole.query.filter_by(domainId=domain_id) or []
        return dict(roles=[{'id': domain_role.id, 'name': domain_role.roleName} for domain_role in all_roles_of_domain])


class UserScopedRoles(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(
        # db.BigInteger, db.ForeignKey('user.id'), nullable=False
        db.INTEGER, db.ForeignKey('user.id'), nullable=False
    )
    roleId = db.Column(
        db.Integer, db.ForeignKey('domain_role.id'), nullable=False
    )
    domainRole = db.relationship('DomainRole')

    @staticmethod
    def is_role_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def add_roles(user_id, roles_list):
        """ Add a role for user
        :param user_id: Id of a user
        :param roles_list: list of roleIds or roleNames
        """
        if User.query.get(user_id):
            for role in roles_list:
                if UserScopedRoles.is_role_number(role):
                    role_id = role
                else:
                    domain_role = DomainRole.get_by_name(role)
                    if domain_role:
                        role_id = domain_role.id
                    else:
                        role_id = None

                if role_id and DomainRole.query.get(role_id):
                    if not UserScopedRoles.query.filter((UserScopedRoles.userId == user_id) &
                                                                (UserScopedRoles.roleId == role_id)).first():
                        user_scoped_role = UserScopedRoles(userId=user_id, roleId=role_id)
                        db.session.add(user_scoped_role)
                    else:
                        raise Exception("Role: %s already exists for user: %s" % (role, user_id))
                else:
                    raise Exception("Role: %s doesn't exist" % role)
            db.session.commit()
        else:
            raise Exception("User %s doesn't exist" % user_id)

    @staticmethod
    def delete_roles(user_id, roles_list):
        """ Delete a role for user
        :param user_id: Id of a user
        :param roles_list: list of roleIds or roleNames
        """
        if User.query.get(user_id):
            for role in roles_list:
                if UserScopedRoles.is_role_number(role):
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
        :param user_id: Id of a user
        """
        user_scoped_roles = UserScopedRoles.query.filter_by(userId=user_id).all() or []
        return dict(roles=[user_scoped_role.roleId for user_scoped_role in user_scoped_roles])


class UserGroups(db.Model):
    __tablename__ = 'user_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(225), nullable=True)
    domain_id = db.Column(
        db.Integer, db.ForeignKey('domain.id'), nullable=False
    )
    domain = db.relationship('Domain')
    users = relationship('User', backref='user_groups')

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def save(domain_id, name, description=''):
        """ Create a new user group.
        :param name: Name of the user group
        :param domain_id: Domain Id of the user group.
        :param description: Description of the user group.
        """
        user_group = UserGroups(name=name, description=description, domain_id=domain_id)
        db.session.add(user_group)
        db.session.commit()
        return user_group.id

    @staticmethod
    def get_by_id(group_id):
        """ Get a user group with supplied group_id.
        :param group_id: id of a user group.
        """
        return UserGroups.query.get(group_id)

    @staticmethod
    def get_by_name(group_name):
        """ Get a user group with supplied group_name.
        :param group_name: Name of a user group.
        """
        return UserGroups.query.filter_by(name=group_name).first()

    @staticmethod
    def all():
        """ Get all groups_ids in database """
        all_user_groups = UserGroups.query.all() or []
        return dict(user_groups=[user_group.id for user_group in all_user_groups])

    @staticmethod
    def all_groups_of_domain(domain_id):
        """ Get all user_groups of with names in database """
        all_user_groups_of_domain = UserGroups.query.filter_by(domain_id=domain_id) or []
        return dict(user_groups=[{'id': user_group.id, 'name': user_group.name} for user_group in
                                 all_user_groups_of_domain])

    @staticmethod
    def all_users_of_group(group_id):
        """ Get all users of a group """
        all_users_of_group = User.query.filter_by(group_id=group_id) or []
        return dict(users=[{'id': user.id, 'lastName': user.last_name} for user in all_users_of_group])

    @staticmethod
    def delete_groups(domain_id, group_ids):
        if Domain.query.get(domain_id):
            for group_id in group_ids:
                group = UserGroups.query.get(group_id) or None
                if group and group.domain_id == domain_id:
                    db.session.delete(group)
                else:
                    raise Exception("Group %s doesn't exist or either it doesn't belong to Domain %s " % (group_id, domain_id))
            db.session.commit()
        else:
            raise Exception("Domain %s doesn't exist" % domain_id)

    @staticmethod
    def add_users_to_group(group_id, user_ids):
        if UserGroups.query.get(group_id):
            for user_id in user_ids:
                user = User.query.get(user_id) or None
                if user:
                    user.group_id = group_id
                    db.session.commit()
                else:
                    raise Exception("User: %s doesn't exist" % user_id)
        else:
            raise Exception("User group %s doesn't exist" % group_id)
