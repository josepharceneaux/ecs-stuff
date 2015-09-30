from sqlalchemy import Column, Integer, String
from base import ModelBase as Base


class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    code = Column(String(20))
    name = Column(String(100))

    def __repr__(self):
        return '<Country %r>' % (self.name)
