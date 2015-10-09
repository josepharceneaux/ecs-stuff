from db import db
#from auth_service.oauth import logger
# from auth_service.oauth.modules.handy_functions import is_number
import datetime
import logging
import candidate
import domain
import organizer
from candidate import CandidateSource
from candidate import CandidateAreaOfInterest
from misc import AreaOfInterest

logger = logging.getLogger(__file__)


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

    # Relationships
    candidates = db.relationship('Candidate', backref='user')
    public_candidate_sharings = db.relationship('PublicCandidateSharing', backref='user')
    user_credentials = db.relationship('UserCredentials', backref='user')
    events = db.relationship('Event', backref='user', lazy='dynamic')
    organizers = db.relationship('Organizer', backref='user', lazy='dynamic')
    venues = db.relationship('Venue', backref='user', lazy='dynamic')

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
        return self.first_name + ' ' + self.last_name

    def __repr__(self):
        return "<email (email=' %r')>" % self.email



class JobOpening(db.Model):
    __tablename__ = 'job_opening'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    job_code = db.Column('JobCode', db.String(100))
    description = db.Column('Description', db.String(500))
    title = db.Column('Title', db.String(150))
    added_time = db.Column('AddedTime', db.TIMESTAMP, default=datetime.datetime.now())

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
    user = db.relationship('User', backref='tokens')

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
    def add_roles(user_id, roles_list):
        """ Add a role for user
        :param user_id: Id of a user
        :param roles_list: list of roleIds or roleNames
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

                if role_id and DomainRole.query.get(role_id):
                    if not UserScopedRoles.query.filter((UserScopedRoles.userId == user_id) &
                                                                (UserScopedRoles.roleId == role_id)).first():
                        user_scoped_role = UserScopedRoles(userId=user_id, roleId=role_id)
                        db.session.add(user_scoped_role)
                    else:
                        logger.info("Role: %s already exists for user: %s" % (role, user_id))
                        raise Exception("Role: %s already exists for user: %s" % (role, user_id))
                else:
                    logger.info("Role: %s doesn't exist" % role)
                    raise Exception("Role: %s doesn't exist" % role)
            db.session.commit()
        else:
            logger.info("User %s doesn't exist" % user_id)
            raise Exception("User %s doesn't exist" % user_id)

    @staticmethod
    def delete_roles(user_id, roles_list):
        """ Delete a role for user
        :param user_id: Id of a user
        :param roles_list: list of roleIds or roleNames
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
                    logger.info("User %s doesn't have any role %s" % (user_id, role_id))
                    raise Exception("User %s doesn't have any role %s" % (user_id, role_id))
            db.session.commit()
        else:
            logger.info("User %s doesn't exist" % user_id)
            raise Exception("User %s doesn't exist" % user_id)

    @staticmethod
    def get_all_roles_of_user(user_id):
        """ Get all roles for a user
        :param user_id: Id of a user
        """
        user_scoped_roles = UserScopedRoles.query.filter_by(userId=user_id).all() or []
        return dict(roles=[user_scoped_role.roleId for user_scoped_role in user_scoped_roles])


class UserCredentials(db.Model):
    """
    This represents database table that holds user's credentials of a
    social network.
    """
    __tablename__ = 'user_credentials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'), nullable=False)
    social_network_id = db.Column('socialNetworkId', db.Integer, db.ForeignKey('social_network.id'), nullable=False)
    refresh_token = db.Column('refreshToken', db.String(1000))
    webhook = db.Column(db.String(200))
    member_id = db.Column('memberId', db.String(100))
    access_token = db.Column('accessToken', db.String(1000))
    social_network = db.relationship("SocialNetwork")

    @classmethod
    def get_all_credentials(cls, social_network_id=None):
        if social_network_id is None:
            return cls.query.all()
        else:
            return cls.get_user_credentials_of_social_network(social_network_id)

    @classmethod
    def get_user_credentials_of_social_network(cls, social_network_id):
        assert social_network_id is not None

        return cls.query.filter(
            UserCredentials.social_network_id == social_network_id
        ).all()

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id is not None
        return cls.query.filter(
            UserCredentials.user_id == user_id
        ).all()

    @classmethod
    def get_by_user_and_social_network_id(cls, user_id, social_network_id):
        assert user_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            db.and_(
                UserCredentials.user_id == user_id,
                UserCredentials.social_network_id == social_network_id
            )
        ).first()

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
        assert webhook_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            db.and_(
                UserCredentials.webhook == webhook_id,
                UserCredentials.social_network_id == social_network_id
            )
        ).one()
