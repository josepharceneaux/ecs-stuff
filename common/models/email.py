import time
from db import db
from candidate import CandidateEmail


class EmailLabel(db.Model):
    __tablename__ = 'email_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_emails = db.relationship('CandidateEmail', backref='email_label')
    reference_emails = db.relationship('ReferenceEmail', backref='email_label')

    def __repr__(self):
        return "<EmailLabel (description=' %r')>" % self.description