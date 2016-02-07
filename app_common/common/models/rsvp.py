from db import db


class RSVP(db.Model):
    __tablename__ = 'rsvp'
    id = db.Column(db.Integer, primary_key=True)
    social_network_rsvp_id = db.Column('socialNetworkRsvpId', db.String(500))
    candidate_id = db.Column('candidateId', db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    event_id = db.Column('eventId', db.Integer, db.ForeignKey("event.id"), nullable=False)
    social_network_id = db.Column('socialNetworkId', db.Integer, db.ForeignKey("social_network.id"), nullable=False)
    status = db.Column('status', db.String(20))
    datetime = db.Column('datetime', db.DateTime)
    payment_status = db.Column('paymentStatus', db.String(20))

    def __repr__(self):
        return '<RSVP %s>' % self.social_network_rsvp_id

    @classmethod
    def get_by_vendor_rsvp_id_candidate_id_vendor_id_time(cls, vendor_rsvp_id,
                                                          candidate_id,
                                                          social_network_id,
                                                          added_time):
        assert vendor_rsvp_id and candidate_id and social_network_id
        return cls.query.filter(
            db.and_(
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
        assert vendor_rsvp_id and candidate_id and social_network_id and event_id
        return cls.query.filter(
            db.and_(
                RSVP.social_network_rsvp_id == vendor_rsvp_id,
                RSVP.candidate_id == candidate_id,
                RSVP.social_network_id == social_network_id,
                RSVP.event_id == event_id
            )
        ).first()

    @classmethod
    def get_by_social_network_rsvp_id_and_social_network_id(cls,
                                                              social_network_rsvp_id,
                                                              social_network_id,
                                                              ):
        assert social_network_id and social_network_rsvp_id
        return cls.query.filter(
            db.and_(
                RSVP.social_network_rsvp_id == social_network_rsvp_id,
                RSVP.social_network_id == social_network_id
            )
        ).first()
