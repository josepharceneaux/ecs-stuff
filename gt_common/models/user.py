from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    domain_id = Column('domainId', Integer, ForeignKey('domain.id'), nullable=False)
    email = Column(String(60), unique=True)
    first_name = Column('firstName', String(255))
    last_name = Column('lastName', String(255))
    device_token = Column('deviceToken', String(64))
    password = Column('password', String(512))
    expiration = Column('expiration', DateTime)
    mobile_version = Column('mobileVersion', String(255))
    added_time = Column('addedTime', DateTime)
    default_culture_id = Column('defaultCultureId', Integer, ForeignKey('culture.id'), nullable=False)
    phone = Column('phone', String(50))
    get_started_data = Column('getStartedData', String(128))
    registration_key = Column(String(512))
    reset_password_key = Column(String(512))
    registration_id = Column(String(512))
    dice_user_id = Column('diceUserId', Integer)

    user_credentials = relationship('UserCredentials', backref='user')
    candidates = relationship('Candidate', backref='user', lazy='dynamic')
    events = relationship('Event', backref='user', lazy='dynamic')
    organizers = relationship('Organizer', backref='user', lazy='dynamic')
    venues = relationship('Venue', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.email

    @property
    def name(self):
        return self.first_name + ' ' + self.last_name


class UserCredentials(Base):
    __tablename__ = 'user_credentials'
    id = Column(Integer, primary_key=True)
    user_id = Column('userId', Integer, ForeignKey('user.id'), nullable=False)
    social_network_id = Column('socialNetworkId', Integer, ForeignKey('social_network.id'), nullable=False)
    refresh_token = Column('refreshToken', String(1000))
    webhook = Column(String(200))
    member_id = Column('memberId', String(100))
    access_token = Column('accessToken', String(1000))
    social_network = relationship("SocialNetwork")

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
            and_(
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
    def get_by_webhook_id_and_social_network(cls, webhook_id, social_network_id):
        assert webhook_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                UserCredentials.webhook == webhook_id,
                UserCredentials.social_network_id == social_network_id
            )
        ).first()
