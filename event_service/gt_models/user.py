from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    domainId = Column(Integer, ForeignKey('domain.id'), nullable=False)
    email = Column(String(60), unique=True)
    firstName = Column(String(255))
    lastName = Column(String(255))
    deviceToken = Column(String(64))
    password = Column(String(512))
    expiration = Column(DateTime)
    mobileVersion = Column(String(255))
    addedTime = Column(DateTime)
    defaultCultureId = Column(Integer, ForeignKey('culture.id'), nullable=False)
    phone = Column(String(50))
    getStartedData = Column(String(128))
    registration_key = Column(String(512))
    reset_password_key = Column(String(512))
    registration_id = Column(String(512))
    diceUserId = Column(Integer)

    user_credentials = relationship('UserCredentials', backref='user')
    candidate = relationship('Candidate', backref='user')
    events = relationship('Event', backref='user')

    def __repr__(self):
        return '<User %r>' % (self.email)


class UserCredentials(Base):
    __tablename__ = 'user_credentials'
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('user.id'), nullable=False)
    socialNetworkId = Column(Integer, ForeignKey('social_network.id'), nullable=False)
    refreshToken = Column(String(1000))
    webhook = Column(String(200))
    memberId = Column(String(100))
    accessToken = Column(String(1000))
    socialNetwork = relationship("SocialNetwork", primaryjoin='UserCredentials.socialNetworkId == SocialNetwork.id')

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
            UserCredentials.socialNetworkId == social_network_id
        ).all()

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id is not None
        return cls.query.filter(
            UserCredentials.userId == user_id
        ).all()

    @classmethod
    def get_by_user_and_social_network(cls, user_id, social_network_id):
        assert user_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                UserCredentials.userId == user_id,
                UserCredentials.socialNetworkId == social_network_id
            )
        ).first()

    @classmethod
    def update_auth_token(cls, user_id, social_network_id, access_token):
        success = False
        user = cls.get_by_user_and_social_network(user_id, social_network_id)
        if user:
            user.update(accessToken=access_token)
            success = True
        return success

    @classmethod
    def get_by_webhook_id_and_social_network(cls, webhook_id, social_network_id):
        assert webhook_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                UserCredentials.webhook == webhook_id,
                UserCredentials.socialNetworkId == social_network_id
            )
        ).first()
