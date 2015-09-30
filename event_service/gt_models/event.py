from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    vendorEventId = Column(String(1000))
    eventTitle = Column(String(500))
    eventDescription = Column(String(1000))
    socialNetworkId = Column(Integer, ForeignKey('social_network.id'), nullable=False)
    userId = Column(Integer, ForeignKey('user.id'), nullable=False)
    groupId = Column(String(100))
    groupUrlName = Column(String(500))
    eventURL = Column(String(500))
    eventAddressLine1 = Column(String(300))
    eventAddressLine2 = Column(String(300))
    eventCity = Column(String(100))
    eventState = Column(String(100))
    eventZipCode = Column(Integer)
    eventCountry = Column(String(100))
    eventLongitude = Column(Float)
    eventLatitude = Column(Float)
    eventStartDateTime = Column(DateTime)
    eventEndDateTime = Column(DateTime)
    organizerName = Column(String(200))
    organizerEmail = Column(String(200))
    aboutEventOrganizer = Column(String(1000))
    registrationInstruction = Column(String(1000))
    eventCost = Column(String(20))
    eventCurrency = Column(String(20))
    eventTimeZone = Column(String(100))
    maxAttendees = Column(Integer)

    def __ne__(self, other_event):
        return (self.vendorEventId != other_event.vendorEventId and
                self.userId != other_event.userId)

    def __eq__(self, other_event):
        return (self.vendorEventId == other_event.vendorEventId and
                self.userId == other_event.userId and
                self.organizerName == other_event.organizername and
                self.eventAddressLine1 == other_event.eventAddressLine1 and
                self.eventStartDateTime == other_event.eventStartDateTime)

    @classmethod
    def get_by_user_and_vendor_id(cls, user_id, event_vendor_id):
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.vendorEventId == event_vendor_id
            )).first()

    @classmethod
    def get_by_user_id_vendor_id_start_date(cls, user_id, social_network_id, start_date):
        assert user_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.socialNetworkId == social_network_id,
                Event.eventStartDateTime >= start_date
            )).all()

    @classmethod
    def get_by_user_id_social_network_id_vendor_event_id(cls, user_id,
                                                         social_network_id, vendor_event_id):
        assert social_network_id is not None
        assert vendor_event_id is not None
        assert user_id is not None
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.socialNetworkId == social_network_id,
                Event.vendorEventId == vendor_event_id
            )
        ).first()

