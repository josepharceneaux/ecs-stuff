from sqlalchemy import PrimaryKeyConstraint
from db import db
import time


# All tables below are Association Tables. SQLAlchemy docs on Association Object:
# http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#association-object

class ReferencePhone(db.Model):
    __tablename__ = 'reference_phone'
    id = db.Column(db.Integer, primary_key=True)
    candidate_reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.id'), primary_key=True) # Multi key?
    phone_label_id = db.Column('PhoneLabelId', db.Integer, db.ForeignKey('phone_label.id'))
    is_default = db.Column('IsDefault', db.Boolean)
    value = db.Column('Value', db.String(50))
    extension = db.Column('Extension', db.String(10))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<ReferencePhone (reference_id=' %r')>" % self.candidate_reference_id

