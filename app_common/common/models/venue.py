from db import db


class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column('Id', db.Integer, primary_key=True)
    social_network_id = db.Column('SocialNetworkId', db.Integer,
                                  db.ForeignKey('social_network.id'), nullable=False)
    social_network_venue_id = db.Column('SocialNetworkVenueId', db.String(200))
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_line_1 = db.Column('AddressLine1', db.String(300))
    address_line_2 = db.Column('AddressLine2', db.String(300))
    city = db.Column('City', db.String(100))
    state = db.Column('State', db.String(100))
    zip_code = db.Column('ZipCode', db.String(10))
    country = db.Column(db.String(100))
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)

    events = db.relationship('Event', backref='venue', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id
        return cls.query.filter(Venue.user_id == user_id).all()

    @classmethod
    def get_by_user_id_venue_id(cls, user_id, venue_id):
        assert user_id and venue_id
        return cls.query.filter(Venue.user_id == user_id, Venue.id == venue_id).first()

    @classmethod
    def get_by_user_id_social_network_id_venue_id(cls, user_id, social_network_id, venue_id):
        assert user_id and venue_id and social_network_id
        return cls.query.filter(Venue.user_id == user_id,
                                Venue.id == venue_id,
                                Venue.social_network_id == social_network_id).first()

    @classmethod
    def get_by_user_id_and_social_network_venue_id(cls, user_id, social_network_venue_id):
        assert user_id and social_network_venue_id
        return cls.query.filter(Venue.user_id == user_id,
                                Venue.social_network_venue_id == social_network_venue_id).first()
