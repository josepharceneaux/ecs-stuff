from datetime import datetime
import time
from db import db
import event
import venue


class SocialNetwork(db.Model):
    __tablename__ = 'social_network'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))
    url = db.Column('url', db.String(255))
    api_url = db.Column('apiUrl', db.String(255))
    client_key = db.Column('clientKey', db.String(500))
    secret_key = db.Column('secretKey', db.String(500))
    redirect_uri = db.Column('redirectUri', db.String(255))
    auth_url = db.Column('authUrl', db.String(200))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.now())

    # Relationships
    candidate_social_networks = db.relationship('CandidateSocialNetwork', backref='social_network')
    events = db.relationship("Event", backref='social_network', lazy='dynamic')
    user_credentials = db.relationship("UserSocialNetworkCredential")
    venues = db.relationship('Venue', backref='social_network', lazy='dynamic')

    def __repr__(self):
        return '<SocialNetwork %r>' % self.name

    @classmethod
    def get_by_name(cls, name):
        assert name is not None
        return cls.query.filter(
            SocialNetwork.name == name.strip()
        ).one()

    @classmethod
    def get_by_id(cls, id):
        assert id is not None
        return cls.query.filter(
            SocialNetwork.id == id
        ).one()

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_all_except_ids(cls, ids):
        assert isinstance(ids, list)
        if ids:
            return cls.query.filter(
                db.not_(
                    SocialNetwork.id.in_(
                        ids
                    )
                )
            ).all()
        else:
            # Didn't input 'ids' it means we we need list of all, the following
            # probably help us avoid the expensive in_ with empty sequence
            SocialNetwork.get_all()

    @classmethod
    def get_by_ids(cls, ids):
        assert isinstance(ids, list)
        return cls.query.filter(
            SocialNetwork.id.in_(
                ids
            )
        ).all()
