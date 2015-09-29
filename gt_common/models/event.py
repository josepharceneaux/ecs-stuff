from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    vendor_event_id = Column(String(1000))
    event_title = Column(String(500))
    event_description = Column(String(1000))
    social_network_id = Column(Integer, ForeignKey('social_network.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    group_id = Column(String(100))
    group_url_name = Column(String(500))
    event_url = Column(String(500))
    event_address_line_1 = Column(String(300))
    event_address_line_2 = Column(String(300))
    event_city = Column(String(100))
    event_state = Column(String(100))
    event_zipcode = Column(Integer)
    event_country = Column(String(100))
    event_longitude = Column(Float)
    event_latitude = Column(Float)
    event_start_datetime = Column(DateTime)
    event_end_datetime = Column(DateTime)
    organizer_name = Column(String(200))
    organizer_email = Column(String(200))
    about_event_organizer = Column(String(1000))
    registration_instruction = Column(String(1000))
    event_cost = Column(String(20))
    event_currency = Column(String(20))
    event_timezone = Column(String(100))
    max_attendees = Column(Integer)

    def __ne__(self, other_event):
        return (self.vendor_event_id != other_event.vendor_event_id and
                self.user_id != other_event.user_id)

    def __eq__(self, other_event):
        return (self.vendor_event_id == other_event.vendor_event_id and
                self.user_id == other_event.user_id and
                self.organizer_name == other_event.organizername and
                self.event_address_line_1 == other_event.event_address_line_1 and
                self.event_start_datetime == other_event.event_start_datetime)

    @classmethod
    def get_by_user_and_vendor_id(cls, user_id, event_vendor_id):
        return cls.query.filter(
            and_(
                Event.user_id == user_id,
                Event.vendor_event_id == event_vendor_id
            )).first()

    @classmethod
    def get_by_user_id_vendor_id_start_date(cls, user_id, social_network_id, start_date):
        assert user_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                Event.user_id == user_id,
                Event.social_network_id == social_network_id,
                Event.event_start_datetime >= start_date
            )).all()

    @classmethod
    def get_by_user_id_social_network_id_vendor_event_id(cls, user_id,
                                                         social_network_id, vendor_event_id):
        assert social_network_id is not None
        assert vendor_event_id is not None
        assert user_id is not None
        return cls.query.filter(
            and_(
                Event.user_id == user_id,
                Event.social_network_id == social_network_id,
                Event.vendor_event_id == vendor_event_id
            )
        ).first()

