from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db import db
import domain

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(255), unique=True)
    notes = db.Column('notes', db.String(1000))

    domain = db.relationship('Domain', backref='organization')

    def __init__(self, name=None, notes=None):
        self.name = name
        self.notes = notes

    def __repr__(self):
        return '<Organization %r>' % self.name
