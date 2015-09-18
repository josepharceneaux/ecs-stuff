from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Client(Base):
    __tablename__ = 'client'
    client_id = Column(String(40), primary_key=True)
    client_secret = Column(String(55), nullable=False)

    # # Possible values are 'public' or 'confidential'
    # @property
    # def client_type(self):
    #     return 'confidential'
    #
    # @property
    # def allowed_grant_types(self):
    #     return ['password', 'refresh_token']
    #
    # @property
    # def default_scopes(self):
    #     return []
    #
    # @property
    # def default_redirect_uri(self):
    #     return ''


class Token(Base):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True)
    client_id = Column(
        String(40), ForeignKey('client.client_id'),
        nullable=False,
    )
    client = relationship('Client')

    user_id = Column(
        Integer, ForeignKey('user.id')
    )
    user = relationship('User')

    # currently only bearer is supported
    token_type = Column(String(40))

    access_token = Column(String(255), unique=True)
    refresh_token = Column(String(255), unique=True)
    expires = Column(DateTime)
    _scopes = Column(Text)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @classmethod
    def get_by_id(cls, id):
        assert id is not None
        return cls.query.filter(
            Token.id == id
        ).one()
