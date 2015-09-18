from sqlalchemy import Column, String
from base import ModelBase as Base

class Client(Base):
    __tablename__ = 'client'
    client_id = Column(String(40), primary_key=True)
    client_secret = Column(String(55), nullable=False)
