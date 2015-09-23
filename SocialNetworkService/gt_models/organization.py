from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Organization(Base):
    __tablename__ = 'organization'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    notes = Column(String(1000))

    domain = relationship('Domain', backref='organization')

    def __init__(self, name=None, notes=None):
        self.name = name
        self.notes = notes

    def __repr__(self):
        return '<Organization %r>' % (self.name)
