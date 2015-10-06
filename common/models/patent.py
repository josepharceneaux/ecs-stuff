import datetime
from db import db


class PatentDetail(db.Model):
    __tabelname__ = 'patent_detail'
    id = db.Column(db.BigInteger, primary_key=True)
    patent_id = db.Column('PatentId', db.BigInteger, db.ForeignKey('patent.id')) # TODO: add relationship
    issuing_authority = db.Column('IssuingAuthority', db.String(255))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<PatentDetail (patent_id=' %r')>" % self.patent_id


class PatentStatus(db.Model):
    __tablename__ = 'patent_status'
    id = db.Column(db.BigInteger, primary_key=True)
    description = db.Column('Description', db.String(1000))
    notes = db.Column('Notes', db.String(1000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    patent_milestones = db.relationship('PatentMilestone', backref='patent_status')

    def __repr__(self):
        return "<PatentStatus (id=' %r')>" % self.id


class PatentInventor(db.Model):
    __tablename__ = 'patent_inventor'
    id = db.Column(db.BigInteger, primary_key=True)
    patent_id = db.Column('PatentId', db.BigInteger, db.ForeignKey('patent.id')) # TODO: add relationship
    name = db.Column('Name', db.String(500))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<PatentInventor (patent_id=' %r')>" % self.patent_id


class PatentMilestone(db.Model):
    __tabelname__ = 'patent_milestone'
    id = db.Column(db.BigInteger, primary_key=True)
    patent_status_id = db.Column('StatusId', db.Integer, db.ForeignKey('patent_status.id'))
    issued_date = db.Column('IssuedDate', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<PatentMilestone (patent_status_id=' %r')>" % self.patent_status_id

