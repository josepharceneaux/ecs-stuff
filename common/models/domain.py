import datetime
from sqlalchemy.orm import relationship
from db import db


class Domain(db.Model):
    __tablename__ = 'domain'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    usage_limitation = db.Column('usageLimitation', db.Integer)
    expiration = db.Column(db.DateTime)
    added_time = db.Column('addedTime', db.DateTime)
    organization_id = db.Column('organizationId', db.Integer)
    is_fair_check_on = db.Column('isFairCheckOn', db.Boolean, default=False)
    is_active = db.Column('isActive', db.Boolean, default=True)  # TODO: store as 0 or 1
    default_tracking_code = db.Column('defaultTrackingCode', db.SmallInteger)
    default_culture_id = db.Column('defaultCultureId', db.Integer, default=1)
    default_from_name = db.Column('defaultFromName', db.String(255))
    settings_json = db.Column('settingsJson', db.Text)
    updated_time = db.Column('updatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    users = relationship('User', backref='domain')
    candidate_sources = relationship('CandidateSource', backref='domain')
    areas_of_interest = relationship('AreaOfInterest', backref='domain')

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Domain %r>' % self.name

    def get_id(self):
        return unicode(self.id)
