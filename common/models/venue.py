from db import db


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column('id', db.Integer, primary_key=True)
    social_network_id = db.Column('socialNetworkId', db.Integer,
                                  db.ForeignKey('social_network.id'), nullable=False)
    social_network_venue_id = db.Column('socialNetworkVenueId', db.String(200))
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_line1 = db.Column('addressLine1', db.String(300))
    address_line2 = db.Column('addressLine2', db.String(300))
    city = db.Column('city', db.String(100))
    state = db.Column('state', db.String(100))
    zipcode = db.Column('zipcode', db.Integer)
    country = db.Column('country', db.String(100))
    longitude = db.Column('longitude', db.Float)
    latitude = db.Column('latitude', db.Float)

    events = db.relationship('Event', backref='venue', lazy='dynamic')

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
    @classmethod
    def get_by_user_id_and_social_network_venue_id(cls, user_id, social_network_venue_id):
        assert user_id is not None
        assert social_network_venue_id is not None
        return cls.query.filter(Venue.user_id == user_id,
                                Venue.social_network_venue_id == social_network_venue_id).first()

