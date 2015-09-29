
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Client(Base):
    __tablename__ = 'client'
    client_id = Column(String(40), primary_key=True)
    client_secret = Column(String(55), nullable=False)

