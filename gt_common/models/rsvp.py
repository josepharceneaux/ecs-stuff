from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_
from base import ModelBase as Base


class RSVP(Base):
    __tablename__ = 'rsvp'
    id = Column(Integer, primary_key=True)
    social_network_rsvp_id = Column('socialNetworkRsvpId', String(500))
    candidate_id = Column('candidateId', Integer, ForeignKey("candidate.id"), nullable=False)
    event_id = Column('eventId', Integer, ForeignKey("event.id"), nullable=False)
    social_network_id = Column('socialNetworkId', Integer, ForeignKey("social_network.id"), nullable=False)
    rsvp_status = Column('status', String(20))
    rsvp_datetime = Column('datetime', DateTime)
    payment_status = Column('paymentStatus', String(20))

    def __repr__(self):
        return '<RSVP %s>' % self.social_network_rsvp_id

    @classmethod
    def get_by_vendor_rsvp_id_candidate_id_vendor_id_time(cls, vendor_rsvp_id,
                                                          candidate_id,
                                                          social_network_id,
                                                          added_time):
        assert vendor_rsvp_id is not None
        assert candidate_id is not None
        assert social_network_id is not None

        return cls.query.filter(
            and_(
                RSVP.social_network_rsvp_id == vendor_rsvp_id,
                RSVP.candidate_id == candidate_id,
                RSVP.social_network_id == social_network_id,
                RSVP.rsvp_datetime == added_time,
            )
        ).first()

    @classmethod
    def get_by_vendor_rsvp_id_candidate_id_vendor_id_event_id(cls,
                                                              vendor_rsvp_id,
                                                              candidate_id,
                                                              social_network_id,
                                                              event_id):
        assert vendor_rsvp_id is not None
        assert candidate_id is not None
        assert social_network_id is not None
        assert event_id is not None

        return cls.query.filter(
            and_(
                RSVP.social_network_rsvp_id == vendor_rsvp_id,
                RSVP.candidate_id == candidate_id,
                RSVP.social_network_id == social_network_id,
                RSVP.event_id == event_id
            )
        ).first()


class CandidateEventRSVP(Base):
    __tablename__ = 'candidate_event_rsvp'

    id = Column(Integer, primary_key=True)
    candidate_id = Column('candidateId', Integer, ForeignKey('candidate.id'), nullable=False)
    event_id = Column('eventId', Integer, ForeignKey('event.id'), nullable=False)
    rsvp_id = Column('rsvpId', Integer, ForeignKey('rsvp.id'), nullable=False)

    def __repr__(self):
        return '<CandidateEventRSVP %r %r %r>' % (self.candidate_id, self.event_id, self.rsvpStatus)

    @classmethod
    def get_by_id_of_candidate_event_rsvp(cls, candidate_id, event_id, rsvp_id):
        assert candidate_id is not None
        assert event_id is not None
        assert rsvp_id is not None

        return cls.query.filter(
            and_(
                CandidateEventRSVP.candidate_id == candidate_id,
                CandidateEventRSVP.event_id == event_id,
                CandidateEventRSVP.rsvp_id == rsvp_id,
            )
        ).first()
