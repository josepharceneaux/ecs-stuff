from db import db
import datetime
from sqlalchemy.orm import relationship
import time

from candidate import CandidateMilitaryService


class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.Integer, primary_key=True)
    added_time = db.Column('addedTime', db.DateTime, default=datetime.datetime.now())
    source_table = db.Column('sourceTable', db.String(127))
    source_id = db.Column('sourceID', db.Integer)
    type = db.Column('type', db.Integer)
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'))
    params = db.Column(db.Text)

    @classmethod
    def get_by_user_id_params_type_source_id(cls, user_id, params, type, source_id):
        assert user_id
        return cls.query.filter(
            db.and_(
                Activity.user_id == user_id,
                Activity.params == params,
                Activity.type == type,
                Activity.source_id == source_id,
            )
        ).first()


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
    # domain = relationship('Domain', backref='culture')
    user = relationship('User', backref='culture')

    def __repr__(self):
        return "<Culture (description=' %r')>" % self.description

    @classmethod
    def get_by_code(cls, code):
        return cls.query.filter(
            Culture.code == code.strip().lower()
        ).one()


class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(500), unique=True)
    notes = db.Column('Notes', db.String(1000))
    updated_time = db.Column('updatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    # domains = db.relationship('Domain', backref='organization')

    def __init__(self, name=None, notes=None):
        self.name = name
        self.notes = notes

    def __repr__(self):
        return "<Organization (name=' %r')>" % self.name


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<Product (name=' %r')>" % self.name

    @classmethod
    def get_by_name(cls, vendor_name):
        assert vendor_name
        return cls.query.filter(
            db.and_(
                Product.name == vendor_name
            )
        ).first()


class Country(db.Model):
    __tablename__ = 'country'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100), nullable=False)
    code = db.Column('Code', db.String(20), nullable=False)

    # Relationships
    candidate_military_services = relationship('CandidateMilitaryService', backref='country')
    patent_details = relationship('PatentDetail', backref='country')
    candidate_addresses = relationship('CandidateAddress', backref='country')
    candidate_educations = relationship('CandidateEducation', backref='country')
    candidate_experiences = relationship('CandidateExperience', backref='country')
    states = relationship('State', backref='country')

    def __repr__(self):
        return "<Country (name=' %r')>" % self.name


# Even though the table name is major I'm keeping the model class singular.
class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100), nullable=False)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def serialize(self):
        return {
            'id': self.id,
        }

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
    zip_codes = relationship('ZipCode', backref='city')

    def __repr__(self):
        return "<City (name=' %r')>" % self.name


class ZipCode(db.Model):
    __tablename__ = 'zipcode'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column('Code', db.String(31))
    city_id = db.Column('CityId', db.Integer, db.ForeignKey('city.id'))
    coordinates = db.Column('Coordinates', db.String(127))

    def __repr__(self):
        return "<Zipcode (code=' %r')>" % self.code


class CustomField(db.Model):
    __tablename__ = 'custom_field'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.id'))
    name = db.Column('Name', db.String(255))
    type = db.Column('Type', db.String(127))
    category_id = db.Column('CategoryId', db.Integer)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationship
    candidate_custom_fields = relationship('CandidateCustomField', backref='custom_field')

    def __repr__(self):
        return "<CustomField (name = %r)>" % self.name


class UserEmailTemplate(db.Model):
    __tablename__ = 'user_email_template'

    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.ForeignKey(u'user.id'), index=True)
    type = db.Column('Type', db.Integer, server_default=db.text("'0'"))
    name = db.Column('Name', db.String(255), nullable=False)
    email_body_html = db.Column('EmailBodyHtml', db.Text)
    email_body_text = db.Column('EmailBodyText', db.Text)
    email_template_folder_id = db.Column('EmailTemplateFolderId', db.ForeignKey(u'email_template_folder.id', ondelete=u'SET NULL'), index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, server_default=db.text("'0'"))
    updated_time = db.Column('UpdatedTime', db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    email_template_folder = relationship(u'EmailTemplateFolder', backref=db.backref('user_email_template',
                                                                                    cascade="all, delete-orphan"))
    user = relationship(u'User', backref=db.backref('user_email_template', cascade="all, delete-orphan"))


class EmailTemplateFolder(db.Model):
    __tablename__ = 'email_template_folder'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    parent_id = db.Column('ParentId', db.ForeignKey(u'email_template_folder.id', ondelete=u'CASCADE'), index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, server_default=db.text("'0'"))
    domain_id = db.Column('DomainId', db.ForeignKey(u'domain.id', ondelete=u'CASCADE'), index=True)
    updated_time = db.Column('UpdatedTime', db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    domain = relationship(u'Domain', backref=db.backref('email_template_folder', cascade="all, delete-orphan"))
    parent = relationship(u'EmailTemplateFolder', remote_side=[id], backref=db.backref('email_template_folder',
                                                                                       cascade="all, delete-orphan"))