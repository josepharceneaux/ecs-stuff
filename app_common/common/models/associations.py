import datetime
from db import db
from sqlalchemy.orm import relationship, backref


# All tables below are Association Tables. SQLAlchemy docs on Association Object:
# http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#association-object


class CandidateAreaOfInterest(db.Model):
    __tablename__ = 'candidate_area_of_interest'
    candidate_id = db.Column('CandidateId', db.BIGINT, db.ForeignKey('candidate.Id'), primary_key=True)
    area_of_interest_id = db.Column('AreaOfInterestId', db.Integer, db.ForeignKey('area_of_interest.Id'),
                                    primary_key=True)
    additional_notes = db.Column('AdditionalNotes', db.Text)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<CandidateAreaOfInterest (area_of_interest_id = %r)" % self.area_of_interest_id

    @classmethod
    def get_aoi(cls, candidate_id, aoi_id):
        """
        :type candidate_id:  int|long
        :type aoi_id:  int|long
        :rtype:  CandidateAreaOfInterest
        """
        return cls.query.filter_by(candidate_id=candidate_id, area_of_interest_id=aoi_id).first()


class ReferenceEmail(db.Model):
    __tablename__ = 'reference_email'
    reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.Id'), primary_key=True)
    email_label_id = db.Column('EmailLabelId', db.Integer, db.ForeignKey('email_label.Id'))
    is_default = db.Column('IsDefault', db.Boolean, nullable=True)
    value = db.Column('Value', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ReferenceEmail (reference_id=' %r')>" % self.reference_id

    @classmethod
    def get_by_reference_id(cls, reference_id):
        """
        :type reference_id:  int|long
        :rtype:  ReferenceEmail
        """
        return cls.query.filter_by(reference_id=reference_id).first()


class ReferencePhone(db.Model):
    __tablename__ = 'reference_phone'
    reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.Id'), primary_key=True)
    phone_label_id = db.Column('PhoneLabelId', db.Integer, db.ForeignKey('phone_label.Id'))
    is_default = db.Column('IsDefault', db.Boolean)
    value = db.Column('Value', db.String(50))
    extension = db.Column('Extension', db.String(10))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ReferencePhone (reference_id=' %r')>" % self.reference_id

    @classmethod
    def get_by_reference_id(cls, reference_id):
        """
        :type reference_id:  int|long
        :rtype:  ReferencePhone
        """
        return cls.query.filter_by(reference_id=reference_id).first()