from db import db
from rsvp import RSVP
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from ..error_handling import InvalidUsage, ForbiddenError


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    social_network_event_id = db.Column('socialNetworkEventId', db.String(1000))
    title = db.Column(db.String(500))
    description = db.Column(db.String(1000))
    social_network_id = db.Column('socialNetworkId', db.Integer, db.ForeignKey('social_network.Id'), nullable=False)
    user_id = db.Column('userId', db.BIGINT, db.ForeignKey('user.Id'), nullable=False)
    is_deleted_from_vendor = db.Column('isDeletedFromVendor', TINYINT, default='0', nullable=False)
    organizer_id = db.Column('organizerId', db.Integer, db.ForeignKey('event_organizer.id'), nullable=True)
    venue_id = db.Column('venueId', db.Integer, db.ForeignKey('venue.Id'), nullable=True)
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
    added_datetime = db.Column('addedDateTime', db.DateTime, default=datetime.utcnow)
    updated_datetime = db.Column('updatedDateTime', db.TIMESTAMP, default=datetime.utcnow)

    # Relationship
    rsvps = relationship('RSVP', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, backref='event')

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
    def get_by_domain_id(cls, domain_id):
        """
        This returns Query object for all the events in user's domain(given domain_id)
        :param int|long domain_id: Id of domain of user
        """
        assert domain_id, 'domain_id is required param'
        from user import User  # This has to be here to avoid circular import
        return cls.query.join(User).filter(User.domain_id == domain_id)

    @classmethod
    def get_by_event_id_and_domain_id(cls, event_id, domain_id):
        """
        This searches given event_id in given domain_id of user
        """
        assert event_id and domain_id
        from user import User  # This has to be here to avoid circular import
        return cls.query.filter_by(id=event_id).join(User).filter(User.domain_id == domain_id).first()

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

    @classmethod
    def get_events_query(cls, user, search=None, social_network_id=None, sort_by='start_datetime',
                         sort_type='desc', user_id=None):
        """
        This method return query object for events after applying all filters
        :param type(t) user: user object
        :param string | None search: search query, based on title
        :param int | long | None social_network_id: social network id, if want to get events of a specific vendor
        :param string sort_by: on which field you want to order
        :param string sort_type: acs or desc, sort order
        :param int| long | None user_id: events' owner user id, None for all event in domain
        :return: returns a query object
        """
        from user import User  # This has to be here to avoid circular import
        from candidate import SocialNetwork
        sort_types = ('asc', 'desc')
        if sort_by not in ('start_datetime', 'title'):
            raise InvalidUsage('Value of sort_by parameter is not valid')

        if sort_type.lower() not in sort_types:
            raise InvalidUsage('Value of sort_type parameter is not valid. Valid values are %s'
                               % list(sort_types))

        eventbrite = SocialNetwork.get_by_name('Eventbrite')
        meetup = SocialNetwork.get_by_name('Meetup')
        if social_network_id and social_network_id not in [eventbrite.id, meetup.id]:
            raise InvalidUsage('Invalid social_network_id provided. Given: %s, Expected: %s'
                               % (social_network_id, [eventbrite.id, meetup.id]))

        if user_id and User.get_domain_id(user_id) != user.domain_id:
                raise ForbiddenError("Not authorized to access users' events outside of your domain")

        query = Event.get_by_domain_id(user.domain_id)
        if social_network_id:
            query = query.filter(Event.social_network_id == social_network_id)
        if user_id:
            query = query.filter(Event.user_id == user_id)
        if search:
            query = query.filter(Event.title.ilike('%' + search + '%'))
        if sort_by == 'title':
            query = query.order_by(getattr(Event.title, sort_type)())
        else:
            query = query.order_by(getattr(Event.start_datetime, sort_type)())
        return query


class MeetupGroup(db.Model):
    __tablename__ = 'meetup_group'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.BIGINT, unique=True)
    user_id = db.Column('userId', db.BIGINT, db.ForeignKey('user.Id'), nullable=False)
    name = db.Column(db.String(500))
    url_name = db.Column(db.String(500))
    description = db.Column(db.String(1000))
    visibility = db.Column(db.String(20))
    country = db.Column(db.String(20))
    state = db.Column(db.String(20))
    city = db.Column(db.String(30))
    timezone = db.Column(db.String(100))
    created_datetime = db.Column(db.DateTime)
    added_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_datetime = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    @classmethod
    def get_by_group_id(cls, group_id):
        """
        :param string | int group_id: group unique id
        :return: first matching group record
        """
        return cls.query.filter_by(group_id=group_id).first()

    @classmethod
    def get_by_user_id_and_group_id(cls, user_id, group_id):
        """
        Search a group by user_id and group unique id
        :param int user_id: user id
        :param string | int group_id:
        :return: returns a group record
        """
        return cls.query.filter_by(user_id=user_id, group_id=group_id).first()

