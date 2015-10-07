from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db import db
import domain
import user


class Culture(db.Model):
    __tablename__ = 'culture'
    id = Column(Integer, primary_key=True)
    description = Column('description', String(50))
    code = Column('code', String(5), unique=True, nullable=False)
    domain = relationship('Domain', backref='culture')
    user = relationship('User', backref='culture')

    def __init__(self, description=None, code=None):
        self.description = description
        self.code = code

    def __repr__(self):
        return '<Culture %r>' % self.description

    @classmethod
    def get_by_code(cls, code):
        return cls.query.filter(
            Culture.code == code.strip().lower()
        ).one()
