
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Client(Base):
    __tablename__ = 'client'
    client_id = Column('client_id', String(40), primary_key=True)
    client_secret = Column('client_secret', String(55), nullable=False)
