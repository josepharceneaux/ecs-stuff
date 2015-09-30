from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    social_network_event_id = Column('socialNetworkEventId', String(1000))
    title = Column('title', String(500))
    description = Column('description', String(1000))
    social_network_id = Column(Integer, ForeignKey('social_network.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    organizer_id = Column(Integer, ForeignKey('organizer.id'), nullable=False)
    venue_id = Column(Integer, ForeignKey('venue.id'), nullable=False)
    group_id = Column('groupId', String(100))
    group_url_name = Column('groupUrlName', String(500))
    url = Column('url', String(500))
    start_datetime = Column('startDatetime', DateTime)
    end_datetime = Column('endDatetime', DateTime)
    registration_instruction = Column('registrationInstruction', String(1000))
    cost = Column('cost', Float)
    currency = Column('currency', String(20))
    timezone = Column('timezone', String(100))
    max_attendees = Column('maxAttendees', Integer)
    #TODO comment why do we need ticket_id. Also, why is it not a relation?
    tickets_id = Column('ticketsId', Integer, nullable=True)

    def __ne__(self, other_event):
        return (self.social_network_event_id != other_event.social_network_event_id and
                self.user_id != other_event.user_id)

    def __eq__(self, other_event):
        return (self.social_network_event_id == other_event.social_network_event_id and
                self.user_id == other_event.user_id and
                self.organizer_id == other_event.organizer_id and
                self.venue_id == other_event.venue_id and
                self.start_datetime == other_event.start_datetime)

    @classmethod
    def get_by_user_and_vendor_id(cls, user_id, social_network_event_id):
        return cls.query.filter(
            and_(
                Event.user_id == user_id,
                Event.social_network_event_id == social_network_event_id
            )).first()

    @classmethod
    def get_by_user_id_vendor_id_start_date(cls, user_id, social_network_id, start_date):
        assert user_id is not None
        assert social_network_id is not None
        return cls.query.filter(
            and_(
                Event.user_id == user_id,
                Event.social_network_id == social_network_id,
                Event.start_datetime >= start_date
            )).all()

    @classmethod
    def get_by_user_id_social_network_id_vendor_event_id(cls, user_id,
                                                         social_network_id, social_network_event_id):
        assert social_network_id is not None
        assert social_network_event_id is not None
        assert user_id is not None
        return cls.query.filter(
            and_(
                Event.user_id == user_id,
                Event.social_network_id == social_network_id,
                Event.social_network_event_id == social_network_event_id
            )
        ).first()

    @classmethod
    def get_by_user_and_event_id(cls, user_id, event_id):
        return cls.query.filter(
            and_(
                Event.userId == user_id,
                Event.id == event_id
            )).first()

