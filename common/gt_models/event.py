from sqlalchemy import Column, Integer, String, Float, DateTime, \
    ForeignKey, and_
from base import ModelBase as Base


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    socialNetworkEventId = Column(String(1000))
    title = Column(String(500))
    description = Column(String(1000))
    socialNetworkId = Column(Integer, ForeignKey('social_network.id'), nullable=False)
    userId = Column(Integer, ForeignKey('user.id'), nullable=False)
    organizerId = Column(Integer, ForeignKey('organizer.id'), nullable=False)
    venueId = Column(Integer, ForeignKey('venue.id'), nullable=False)
    groupId = Column(String(100))
    groupUrlName = Column(String(500))
    eventUrl = Column(String(500))
    startDatetime = Column(DateTime)
    endDatetime = Column(DateTime)
    registrationInstruction = Column(String(1000))
    cost = Column(Float)
    currency = Column(String(20))
    timezone = Column(String(100))
    maxAttendees = Column(Integer)
    ticketsId = Column(Integer, nullable=True)

    def __ne__(self, other_event):
        return (self.socialNetworkEventId != other_event.socialNetworkEventId and
                self.userId != other_event.userId)

    def __eq__(self, other_event):
        return (self.socialNetworkEventId == other_event.socialNetworkEventId and
                self.userId == other_event.userId and
                self.organizerId == other_event.organizerId and
                self.addressLine1 == other_event.addressLine1 and
                self.startDatetime == other_event.startDatetime)

    @classmethod
    def get_by_user_and_vendor_id(cls, user_id, social_network_event_id):
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.socialNetworkEventId == social_network_event_id
            )).first()

    @classmethod
    def get_by_user_and_event_id(cls, user_id, event_id):
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.id == event_id
            )).first()

    @classmethod
    def get_by_user_id_vendor_id_start_date(cls, user_id, social_network_id, start_date):
        assert user_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.socialNetworkId == social_network_id,
                Event.startDatetime >= start_date
            )).all()

    @classmethod
    def get_by_user_id_social_network_id_vendor_event_id(cls, user_id,
                                                         social_network_id, social_network_event_id):
        assert social_network_id is not None
        assert social_network_event_id is not None
        assert user_id is not None
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.socialNetworkId == social_network_id,
                Event.socialNetworkEventId == social_network_event_id
            )
        ).first()




