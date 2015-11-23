from db import db


class Event(db.Model):
    __tablename__ = 'event'

    id = db.Column(db.Integer, primary_key=True)
    social_network_event_id = db.Column('socialNetworkEventId', db.String(1000))
    title = db.Column(db.String(500))
    description = db.Column(db.String(1000))
    social_network_id = db.Column('socialNetworkId', db.Integer, db.ForeignKey('social_network.id'), nullable=False)
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'), nullable=False)
    organizer_id = db.Column('organizerId', db.Integer, db.ForeignKey('event_organizer.id'), nullable=False)
    venue_id = db.Column('venueId', db.Integer, db.ForeignKey('venue.id'), nullable=False)
    social_network_group_id = db.Column('socialNetworkGroupId', db.String(100))
    group_url_name = db.Column('groupUrlName', db.String(500))
    url = db.Column(db.String(500))
    start_datetime = db.Column('startDatetime', db.DateTime)
    end_datetime = db.Column('endDatetime', db.DateTime)
    registration_instruction = db.Column('registrationInstruction', db.String(1000))
    cost = db.Column(db.Float)
    currency = db.Column(db.String(20))
    timezone = db.Column(db.String(100))
    max_attendees = db.Column('maxAttendees', db.Integer)
    tickets_id = db.Column('ticketsId', db.Integer, nullable=True)

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
    def get_by_user_and_social_network_event_id(cls, user_id, social_network_event_id):
        assert user_id and social_network_event_id
        return cls.query.filter(
            db.and_(
                Event.user_id == user_id,
                Event.social_network_event_id == social_network_event_id
            )).first()

    @classmethod
    def get_by_user_id_vendor_id_start_date(cls, user_id, social_network_id, start_date):
        assert user_id and social_network_id and start_date
        return cls.query.filter(
            db.and_(
                Event.user_id == user_id,
                Event.social_network_id == social_network_id,
                Event.start_datetime >= start_date
            )).all()

    @classmethod
    def get_by_user_id_social_network_id_vendor_event_id(cls, user_id,
                                                         social_network_id,
                                                         social_network_event_id):
        assert social_network_id and social_network_event_id and user_id
        return cls.query.filter(
            db.and_(
                Event.user_id == user_id,
                Event.social_network_id == social_network_id,
                Event.social_network_event_id == social_network_event_id
            )
        ).first()

    @classmethod
    def get_by_user_id_event_id_social_network_event_id(cls, user_id,
                                                         _id, social_network_event_id):
        assert _id and social_network_event_id and user_id
        return cls.query.filter(
            db.and_(
                Event.user_id == user_id,
                Event.id == _id,
                Event.social_network_event_id == social_network_event_id
            )
        ).first()

    @classmethod
    def get_by_user_and_event_id(cls, user_id, event_id):
        assert user_id and event_id
        return cls.query.filter(
            db.and_(
                Event.user_id == user_id,
                Event.id == event_id
            )).first()

