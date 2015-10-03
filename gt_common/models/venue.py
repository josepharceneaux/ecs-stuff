from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Venue(Base):
    __tablename__ = 'venue'

    id = Column('id', Integer, primary_key=True)
    social_network_id = Column('socialNetworkId', Integer, ForeignKey('social_network.id'), nullable=False)
    social_network_venue_id = Column('socialNetworkVenueId', String(200))
    user_id = Column('userId', Integer, ForeignKey('user.id'), nullable=False)
    address_line1 = Column('addressLine1', String(300))
    address_line2 = Column('addressLine2', String(300))
    city = Column('city', String(100))
    state = Column('state', String(100))
    zipcode = Column('zipcode', String(20))
    country = Column('country', String(100))
    longitude = Column('longitude', Float)
    latitude = Column('latitude', Float)

    events = relationship('Event', backref='venue', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id is not None
        return cls.query.filter(Venue.user_id == user_id).all()

    @classmethod
    def get_by_user_id_venue_id(cls, user_id, venue_id):
        assert user_id is not None
        assert venue_id is not None
        return cls.query.filter(Venue.user_id == user_id, Venue.id == venue_id).first()

    @classmethod
    def get_by_user_id_social_network_id_venue_id(cls, user_id, social_network_id, venue_id):
        assert user_id is not None
        assert venue_id is not None
        assert social_network_id is not None
        return cls.query.filter(Venue.user_id == user_id,
                                Venue.id == venue_id,
                                Venue.social_network_id == social_network_id).first()
