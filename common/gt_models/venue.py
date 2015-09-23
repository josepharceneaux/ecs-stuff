from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Venue(Base):
    __tablename__ = 'venue'

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('user.id'), nullable=False)
    addressLine1 = Column(String(300))
    addressLine2 = Column(String(300))
    city = Column(String(100))
    state = Column(String(100))
    zipcode = Column(Integer)
    country = Column(String(100))
    longitude = Column(Float)
    latitude = Column(Float)

    events = relationship('Event', backref='venue', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id is not None
        return cls.query.filter(Venue.userId == user_id).all()
