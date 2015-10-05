from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, Text
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Token(Base):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True)
    client_id = Column('client_id', String(40), ForeignKey('client.client_id'), nullable=False)
    client = relationship('Client')
    user_id = Column('user_id', Integer, ForeignKey('user.id'))
    user = relationship('User')

    # currently only bearer is supported
    token_type = Column('token_type', String(40))

    access_token = Column('access_token', String(255), unique=True)
    refresh_token = Column('refresh_token', String(255), unique=True)
    expires = Column('expires', DateTime)
    _scopes = Column('_scopes', Text)

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.query.filter(
            Token.user_id == user_id
        ).all()

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
