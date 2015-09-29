from sqlalchemy import Column, Integer, String, ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Organizer(Base):
    __tablename__ = 'organizer'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    name = Column(String(200))
    email = Column(String(200))
    about = Column(String(1000))

    event = relationship('Event', backref='organizer', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id is not None
        return cls.query.filter(Organizer.user_id == user_id).all()
