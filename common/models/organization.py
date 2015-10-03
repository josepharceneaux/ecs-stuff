from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db import db


class Organization(db.Model):
    __tablename__ = 'organization'
    id = Column(Integer, primary_key=True)
    name = Column('name', String(255), unique=True)
    notes = Column('notes', String(1000))

    domain = relationship('Domain', backref='organization')

    def __init__(self, name=None, notes=None):
        self.name = name
        self.notes = notes

    def __repr__(self):
        return '<Organization %r>' % self.name
