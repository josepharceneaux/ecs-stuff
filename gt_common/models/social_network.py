from sqlalchemy import Column, Integer, String, not_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class SocialNetwork(Base):
    __tablename__ = 'social_network'
    id = Column(Integer, primary_key=True)
    name = Column('name', String(100))
    url = Column('url', String(255))
    api_url = Column('apiUrl', String(255))
    client_key = Column('clientKey', String(500))
    secret_key = Column('secretKey', String(500))
    redirect_uri = Column('redirectUri', String(255))
    auth_url = Column('authUrl', String(200))

    events = relationship("Event", backref='social_network')
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

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_all_except_ids(cls, ids):
        assert isinstance(ids, list)
        if ids:
            return cls.query.filter(
                not_(
                    SocialNetwork.id.in_(
                        ids
                    )
                )
            ).all()
        else:
            # Didn't input 'ids' it means we we need list of all, the following
            # probably help us avoid the expensive in_ with empty sequence
            SocialNetwork.get_all()

    @classmethod
    def get_by_ids(cls, ids):
        assert isinstance(ids, list)
        return cls.query.filter(
            SocialNetwork.id.in_(
                ids
            )
        ).all()
