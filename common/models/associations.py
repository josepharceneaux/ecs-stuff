from db import db
import datetime


# All tables below are Association Tables. SQLAlchemy docs on Association Object:
# http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#association-object


class CandidateAreaOfInterest(db.Model):
    __tablename__ = 'candidate_area_of_interest'
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'), primary_key=True)
    area_of_interest_id = db.Column('AreaOfInterestId', db.Integer, db.ForeignKey('area_of_interest.id'), primary_key=True)
    additional_notes = db.Column('AdditionalNotes', db.Text)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


class ReferenceEmail(db.Model):
    __tablename__ = 'reference_email'
    id = db.Column(db.Integer, primary_key=True)
    candidate_reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.id'))
    email_label_id = db.Column('EmailLabelId', db.Integer, db.ForeignKey('email_label.id'))
    is_default = db.Column('IsDefault', db.Boolean)
    value = db.Column('Value', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<ReferenceEmail (reference_id=' %r')>" % self.candidate_reference_id


class ReferencePhone(db.Model):
    __tablename__ = 'reference_phone'
    id = db.Column(db.Integer, primary_key=True)
    candidate_reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.id'), primary_key=True) # Multi key?
    phone_label_id = db.Column('PhoneLabelId', db.Integer, db.ForeignKey('phone_label.id'))
    is_default = db.Column('IsDefault', db.Boolean)
    value = db.Column('Value', db.String(50))
    extension = db.Column('Extension', db.String(10))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<ReferencePhone (reference_id=' %r')>" % self.candidate_reference_id
