from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class SocialNetwork(Base):
    __tablename__ = 'social_network'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    url = Column(String(255))
    apiUrl = Column(String(255))
    clientKey = Column(String(500))
    secretKey = Column(String(500))
    redirectUri = Column(String(255))
    authUrl = Column(String(200))

    events = relationship("Event", backref='social_network_event')
    user_credentials = relationship("UserCredentials", backref='social_network')

    def __repr__(self):
        return '<SocialNetwork %r>' % self.name

    @classmethod
    def get_by_name(cls, name):
        assert name is not None
        return cls.query.filter(
            SocialNetwork.name == name.strip()
        ).one()

    @classmethod
    def get_by_id(cls, id):
        assert id is not None
        return cls.query.filter(
            SocialNetwork.id == id
        ).one()
