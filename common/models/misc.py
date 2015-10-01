from db import db
from sqlalchemy.orm import relationship
import time


class AreaOfInterest(db.Model):
    __tablename__ = 'area_of_interest'
    id = db.Column(db.BigInteger, primary_key=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.id'))
    description = db.Column('Description', db.String(255))
    parent_id = db.Column('ParentId', db.BigInteger, db.ForeignKey('area_of_interest.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<AreaOfInterest (parent_id=' %r')>" % self.parent_id


class Culture(db.Model):
    __tablename__ = 'culture'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50))
    code = db.Column(db.String(5), unique=True)

    # Relationships
    candidates = relationship('Candidate', backref='culture')

    def __repr__(self):
        return "<Culture (description=' %r')>" % self.description


class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(500), unique=True)
    notes = db.Column('Notes', db.String(1000))

    def __repr__(self):
        return "<Organization (name=' %r')>" % self.name


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.DateTime, default=time.time())

    def __repr__(self):
        return "<Product (name=' %r')>" % self.name


class Country(db.Model):
    __tablename__ = 'country'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100), nullable=False)
    code = db.Column('Code', db.String(20), nullable=False)

    # Relationships
    candidate_military_services = relationship('CandidateMilitartyService', backref='country')
    patent_details = relationship('PatentDetail', backref='country')
    candidate_addresses = relationship('CandidateAddress', backref='country')
    candidate_educations = relationship('CandidateEducation', backref='country')
    candidate_experiences = relationship('CandidateExperience', backref='country')
    states = relationship('State', backref='country')

    def __repr__(self):
        return "<Country (name=' %r')>" % self.name


class State(db.Model):
    __tablename__ = 'state'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(255))
    alpha_code = db.Column('AlphaCode', db.String(31))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    abbreviation = db.Column('Abbreviation', db.String(255))

    # Relationships
    cities = relationship('City', backref='state')

    def __repr__(self):
        return "<State (name=' %r')>" % self.name


class City(db.Model):
    __tablename__ = 'city'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(255))
    state_id = db.Column('StateId', db.Integer, db.ForeignKey('state.id'))
    postal_code = db.Column('PostalCode', db.String(63))
    latitude_radians = db.Column('LatitudeRadians', db.Float)
    longitude_radians = db.Column('LongitudeRadians', db.Float)
    alternate_names = db.Column('AlternateNames', db.Text)
    coordinates = db.Column('Coordinates', db.String(127))

    # Relationships
    zipcodes = relationship('Zipcode', backref='city')

    def __repr__(self):
        return "<City (name=' %r')>" % self.name


class Zipcode(db.Model):
    __tablename__ = 'zipcode'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column('Code', db.String(31))
    city_id = db.Column('CityId', db.Integer, db.ForeignKey('city.id'))
    coordinates = db.Column('Coordinates', db.String(127))

    def __repr__(self):
        return "<Zipcode (code=' %r')>" % self.code