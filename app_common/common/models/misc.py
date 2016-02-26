from sqlalchemy import and_
from db import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import DOUBLE
from ..error_handling import InvalidUsage
import datetime
import time
from candidate import CandidateMilitaryService
from sms_campaign import SmsCampaign
from push_campaign import PushCampaign
from ..utils.scheduler_utils import SchedulerUtils


class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column('Id', db.Integer, primary_key=True)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    type = db.Column('Type', db.Integer)
    source_table = db.Column('SourceTable', db.String(127))
    source_id = db.Column('SourceId', db.Integer)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id'))
    params = db.Column('Params', db.Text)

    def __repr__(self):
        return "<Activity: (id = {})>".format(self.id)

    @classmethod
    def get_by_user_id_params_type_source_id(cls, user_id, params, type, source_id):
        return cls.query.filter(
            db.and_(
                Activity.user_id == user_id,
                Activity.params == params,
                Activity.type == type,
                Activity.source_id == source_id,
            )).first()

    @classmethod
    def get_by_user_id_type_source_id(cls, user_id, type_, source_id):
        assert user_id
        return cls.query.filter_by(user_id=user_id, type=type_, source_id=source_id).first()



class AreaOfInterest(db.Model):
    __tablename__ = 'area_of_interest'
    id = db.Column('Id', db.Integer, primary_key=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id'))
    name = db.Column('Description', db.String(255))
    parent_id = db.Column('ParentId', db.Integer, db.ForeignKey('area_of_interest.Id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<AreaOfInterest (name='%r')>" % self.name

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def get_area_of_interest(cls, domain_id, name):
        return cls.query.filter(db.and_(
            AreaOfInterest.domain_id == domain_id,
            AreaOfInterest.name == name
        )).first()

    @classmethod
    def get_domain_areas_of_interest(cls, domain_id):
        """
        :rtype: list[AreaOfInterest]
        """
        return cls.query.filter(AreaOfInterest.domain_id == domain_id).all()


class Culture(db.Model):
    __tablename__ = 'culture'
    id = db.Column('Id', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50))
    code = db.Column('Code', db.String(5), unique=True)

    # Relationships
    candidates = relationship('Candidate', backref='culture')
    # domain = relationship('Domain', backref='culture')
    user = relationship('User', backref='culture')

    def __repr__(self):
        return "<Culture (description=' %r')>" % self.description

    @classmethod
    def get_by_code(cls, code):
        return cls.query.filter(Culture.code == code.strip().lower()).one()


class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(255), unique=True)
    notes = db.Column('Notes', db.String(255))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    # domains = db.relationship('Domain', backref='organization')

    def __init__(self, name=None, notes=None):
        self.name = name
        self.notes = notes

    def __repr__(self):
        return "<Organization (name=' %r')>" % self.name


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<Product (name=' %r')>" % self.name

    @classmethod
    def get_by_name(cls, vendor_name):
        assert vendor_name
        return cls.query.filter(db.and_(Product.name == vendor_name)).first()


class Country(db.Model):
    __tablename__ = 'country'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100), nullable=False)
    code = db.Column('Code', db.String(20), nullable=False)

    # Relationships
    candidate_military_services = relationship('CandidateMilitaryService', backref='country')
    candidate_addresses = relationship('CandidateAddress', backref='country')
    candidate_educations = relationship('CandidateEducation', backref='country')
    candidate_experiences = relationship('CandidateExperience', backref='country')
    states = relationship('State', backref='country')

    def __repr__(self):
        return "<Country (name=' %r')>" % self.name

    @classmethod
    def country_id_from_name_or_code(cls, name_or_code):
        country_row = cls.query.filter(db.or_(Country.name == name_or_code,
                                              Country.code == name_or_code)).first()
        return country_row.id if country_row else None


    @classmethod
    def country_name_from_country_id(cls, country_id):
        if not country_id:
            return 'United States'

        country = cls.query.filter(Country.id == country_id).first()
        if country:
            return country.name
        else:
            return 'United States'


# Even though the table name is majors I'm keeping the model class singular.
class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100), nullable=False)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def serialize(self):
        return {'id': self.id}


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
    latitude_radians = db.Column('LatitudeRadians', DOUBLE)
    longitude_radians = db.Column('LongitudeRadians', DOUBLE)
    alternate_names = db.Column('AlternateNames', db.Text)
    coordinates = db.Column('Coordinates', db.String(127))

    # Relationships
    zip_codes = relationship('ZipCode', backref='city')

    def __repr__(self):
        return "<City (name = '%r')>" % self.name


class ZipCode(db.Model):
    __tablename__ = 'zipcode'
    id = db.Column('Id', db.Integer, primary_key=True)
    code = db.Column('Code', db.String(31))
    city_id = db.Column('CityId', db.Integer, db.ForeignKey('city.id'))
    coordinates = db.Column('Coordinates', db.String(127))

    def __repr__(self):
        return "<Zipcode (code=' %r')>" % self.code


class Frequency(db.Model):
    __table_name__ = 'frequency'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Description', db.String(10), nullable=False)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    sms_campaigns = relationship('SmsCampaign', backref='frequency')
    push_campaigns = relationship('PushCampaign', backref='frequency')

    # frequency Ids
    ONCE = 1
    DAILY = 2
    WEEKLY = 3
    BIWEEKLY = 4
    MONTHLY = 5
    YEARLY = 6
    CUSTOM = 7

    def __repr__(self):
        return "<Frequency: (id = {})>".format(self.id)

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def get_seconds_from_id(cls, frequency_id):
        """
        This gives us the number of seconds for given frequency_id.
        frequency_id is in range 1 to 6 representing
            'Once', 'Daily', 'Weekly', 'Biweekly', 'Monthly', 'Yearly'
        respectively.
        :param frequency_id: int
        :return: seconds
        :rtype: int
        """
        if not frequency_id:
            return 0
        if not isinstance(frequency_id, int):
            raise InvalidUsage('Include frequency id as int')
        seconds_from_frequency_id = {
            cls.ONCE: 0,
            cls.DAILY: 24 * 3600,
            cls.WEEKLY: 7 * 24 * 3600,
            cls.BIWEEKLY: 14 * 24 * 3600,
            cls.MONTHLY: 30 * 24 * 3600,
            cls.YEARLY: 365 * 24 * 3600,
            cls.CUSTOM: 5 * SchedulerUtils.MIN_ALLOWED_FREQUENCY
        }
        seconds = seconds_from_frequency_id.get(frequency_id)
        if not seconds and seconds != 0:
            raise InvalidUsage("Unknown frequency ID: %s" % frequency_id)
        return seconds

    @classmethod
    def standard_frequencies(cls):
        """Returns a dict of system wide standard frequency names and period in seconds"""
        return {'once': cls.get_seconds_from_id(cls.ONCE),
                'daily': cls.get_seconds_from_id(cls.DAILY),
                'weekly': cls.get_seconds_from_id(cls.WEEKLY),
                'biweekly': cls.get_seconds_from_id(cls.BIWEEKLY),
                'monthly': cls.get_seconds_from_id(cls.MONTHLY),
                'yearly': cls.get_seconds_from_id(cls.YEARLY)}


class CustomField(db.Model):
    __tablename__ = 'custom_field'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id'))
    name = db.Column('Name', db.String(255))
    type = db.Column('Type', db.String(127))
    category_id = db.Column('CategoryId', db.Integer)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationship
    candidate_custom_fields = relationship('CandidateCustomField', backref='custom_field',
                                           cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return "<CustomField (name = %r)>" % self.name

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def get_domain_custom_fields(cls, domain_id):
        """Function gets all domain's custom fields
        :type domain_id:  int|long
        :rtype:  list[CustomField]
        """
        return cls.query.filter(CustomField.domain_id==domain_id).all()


class UserEmailTemplate(db.Model):
    __tablename__ = 'user_email_template'
    id = db.Column('Id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.ForeignKey('user.Id'), index=True)
    type = db.Column('Type', db.Integer, server_default=db.text("'0'"))
    name = db.Column('Name', db.String(255), nullable=False)
    email_body_html = db.Column('EmailBodyHtml', db.Text)
    email_body_text = db.Column('EmailBodyText', db.Text)
    email_template_folder_id = db.Column('EmailTemplateFolderId', db.ForeignKey('email_template_folder.id', ondelete=u'SET NULL'), index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, server_default=db.text("'0'"))
    updated_time = db.Column('UpdatedTime', db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    # Relationships
    email_template_folder = relationship(u'EmailTemplateFolder', backref=db.backref('user_email_template',
                                                                                    cascade="all, delete-orphan"))
    user = relationship(u'User', backref=db.backref('user_email_template', cascade="all, delete-orphan"))


class EmailTemplateFolder(db.Model):
    __tablename__ = 'email_template_folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    parent_id = db.Column('ParentId', db.ForeignKey('email_template_folder.id', ondelete='CASCADE'),
                          index=True)
    is_immutable = db.Column('IsImmutable', db.Integer, nullable=False, server_default=db.text("'0'"))
    domain_id = db.Column('DomainId', db.ForeignKey('domain.Id', ondelete='CASCADE'), index=True)
    updated_time = db.Column('UpdatedTime', db.DateTime, nullable=False,
                             server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    domain = relationship('Domain', backref=db.backref('email_template_folder', cascade="all, delete-orphan"))
    parent = relationship('EmailTemplateFolder', remote_side=[id], backref=db.backref('email_template_folder',
                                                                                       cascade="all, delete-orphan"))

class CustomFieldCategory(db.Model):
    __tablename__ = 'custom_field_category'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'))
    name = db.Column('Name', db.String(255))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


# class PatentDetail(db.Model):
#     __tablename__ = 'patent_detail'
#     id = db.Column('Id', db.BIGINT, primary_key=True)
#     patent_id = db.Column('PatentId', db.BIGINT)
#     issuing_authority = db.Column('IssuingAuthority', db.String(255))
#     country_id = db.Column('CountryId', db.INT, db.ForeignKey('country.Id'))
#     updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
#
#     def __repr__(self):
#         return "<PatentDetail (id = {})>".format(self.id)


class UrlConversion(db.Model):
    __tablename__ = 'url_conversion'
    id = db.Column('Id', db.Integer, primary_key=True)
    source_url = db.Column('SourceUrl', db.String(512))  # Ours
    destination_url = db.Column('DestinationUrl', db.String(512))  # Theirs
    hit_count = db.Column('HitCount', db.Integer, default=0)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    last_hit_time = db.Column('LastHitTime', db.DateTime)

    def __repr__(self):
        return "<UrlConversion (id = {})>".format(self.id)

    # Relationships
    sms_campaign_sends_url_conversions = relationship('SmsCampaignSendUrlConversion',
                                                      cascade='all,delete-orphan',
                                                      passive_deletes=True,
                                                      backref='url_conversion')

    email_campaign_sends_url_conversions = relationship('EmailCampaignSendUrlConversion',
                                                        cascade='all,delete-orphan',
                                                        passive_deletes=True,
                                                        backref='url_conversion')

    push_campaign_sends_url_conversions = relationship('PushCampaignSendUrlConversion',
                                                       cascade='all,delete-orphan',
                                                       passive_deletes=True,
                                                       backref='url_conversion',
                                                       lazy='dynamic')

    def __repr__(self):
        return "<UrlConversion (id=' %r')>" % self.id

