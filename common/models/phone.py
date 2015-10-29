import datetime
from db import db
from candidate import CandidatePhone

class PhoneLabel(db.Model):
    __tablename__ = 'phone_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(20))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidate_phones = db.relationship('CandidatePhone', backref='phone_label')
    user_phones = db.relationship('UserPhone', backref='phone_label')
    # reference_phones = db.relationship('ReferencePhone', backref='phone_label')

    def __repr__(self):
        return "<PhoneLabel (description=' %r')>" % self.description