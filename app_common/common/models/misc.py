import datetime

from db import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import DOUBLE

from ..error_handling import InvalidUsage
from candidate import CandidateMilitaryService
from sms_campaign import SmsCampaign
from push_campaign import (PushCampaign, PushCampaignBlast,
                           PushCampaignSend, PushCampaignSendUrlConversion)
from ..utils.scheduler_utils import SchedulerUtils


class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column('Id', db.Integer, primary_key=True)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.utcnow, index=True)
    type = db.Column('Type', db.Integer)
    source_table = db.Column('SourceTable', db.String(127))
    source_id = db.Column('SourceId', db.Integer)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id'))
    user = relationship('User', backref='activity')
    params = db.Column('Params', db.Text)

    class MessageIds(object):
        """
        When user performs some action e.g. creates a smartlist or create a candidate etc, we need
        to create an activity for those actions. So, here we have the Activity Message Ids to create
        such activities. Corresponding activity messages are in activity_service.
        (These ids and messages will be moved to database later).
        This is placed inside Activity model so that any service can use these ids to create
        activities without initializing activity_service.
        """
        #########################################################################################
        #   LEGACY CODES
        #########################################################################################

        # params=dict(formattedName)
        CANDIDATE_CREATE_WEB = 1
        CANDIDATE_UPDATE = 2
        CANDIDATE_DELETE = 3
        CANDIDATE_CREATE_CSV = 18
        CANDIDATE_CREATE_WIDGET = 19
        CANDIDATE_CREATE_MOBILE = 20  # TODO add in

        # params=dict(id, name)
        # All Campaigns
        CAMPAIGN_CREATE = 4
        CAMPAIGN_DELETE = 5
        CAMPAIGN_SEND = 6  # also has num_candidates
        CAMPAIGN_EXPIRE = 7  # recurring campaigns only # TODO implement
        CAMPAIGN_PAUSE = 21
        CAMPAIGN_RESUME = 22
        CAMPAIGN_SCHEDULE = 27

        # params=dict(name, is_smartlist=0/1)
        SMARTLIST_CREATE = 8
        SMARTLIST_DELETE = 9
        SMARTLIST_ADD_CANDIDATE = 10  # also has formattedName (of candidate) and candidateId
        SMARTLIST_REMOVE_CANDIDATE = 11  # also has formattedName and candidateId

        # params=dict(firstName, lastName)
        USER_CREATE = 12

        # params=dict(client_ip)
        WIDGET_VISIT = 13

        # TODO implement frontend + backend
        NOTIFICATION_CREATE = 14  # when we want to show the users a message

        # params=dict(candidateId, campaign_name, candidate_name)
        # Email campaign
        CAMPAIGN_EMAIL_SEND = 15
        CAMPAIGN_EMAIL_OPEN = 16
        CAMPAIGN_EMAIL_CLICK = 17

        # Social Network Service
        RSVP_EVENT = 23
        EVENT_CREATE = 28
        EVENT_DELETE = 29
        EVENT_UPDATE = 30

        # SMS campaign
        CAMPAIGN_SMS_SEND = 24
        CAMPAIGN_SMS_CLICK = 25
        CAMPAIGN_SMS_REPLY = 26

        # Dumblists
        # TODO

        CAMPAIGN_SMS_CREATE = 28

        # Push campaign
        CAMPAIGN_PUSH_CREATE = 29
        CAMPAIGN_PUSH_SEND = 30
        CAMPAIGN_PUSH_CLICK = 31

    ####################################################################################################
    #   V2.0+ Codes
    #   Activity Codes are set up in blocks of 100 to avoid search for the last used int.
    ####################################################################################################

        # RESUME_PARSING_SERVICE 100-199
        # USER_SERVICE_PORT  200-299
        # CANDIDATE_SERVICE 300-399
        # WIDGET_SERVICE 400-499
        # SOCIAL_NETWORK_SERVICE 500-599

        # CANDIDATE_POOL_SERVICE = 600-699

        # params = dict(name)
        PIPELINE_CREATE = 600
        PIPELINE_DELETE = 601
        # params = dict(name)
        TALENT_POOL_CREATE = 602
        TALENT_POOL_DELETE = 603
        # params = dict(name)
        DUMBLIST_CREATE = 604
        DUMBLIST_DELETE = 605

        # SPREADSHEET_IMPORT_SERVICE 700-799
        # DASHBOARD_SERVICE 800-899
        # SCHEDULER_SERVICE 900-999
        # SMS_CAMPAIGN_SERVICE 1000-1099
        # EMAIL_CAMPAIGN_SERVICE 1100-1199

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

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
        :type domain_id: int|long
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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

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
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.utcnow)

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)

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


class CustomFieldCategory(db.Model):
    __tablename__ = 'custom_field_category'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.Id', ondelete='CASCADE'))
    name = db.Column('Name', db.String(255))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.utcnow)


# class PatentDetail(db.Model):
#     __tablename__ = 'patent_detail'
#     id = db.Column('Id', db.BIGINT, primary_key=True)
#     patent_id = db.Column('PatentId', db.BIGINT)
#     issuing_authority = db.Column('IssuingAuthority', db.String(255))
#     country_id = db.Column('CountryId', db.INT, db.ForeignKey('country.Id'))
#     updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetim.utcnow)
#
#     def __repr__(self):
#         return "<PatentDetail (id = {})>".format(self.id)


class UrlConversion(db.Model):
    __tablename__ = 'url_conversion'
    id = db.Column('Id', db.Integer, primary_key=True)
    source_url = db.Column('SourceUrl', db.String(512))  # Ours
    destination_url = db.Column('DestinationUrl', db.String(512))  # Theirs
    hit_count = db.Column('HitCount', db.Integer, default=0)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now)
    last_hit_time = db.Column('LastHitTime', db.DateTime)

    def __repr__(self):
        return "<UrlConversion (id = {})>".format(self.id)

    @classmethod
    def get_by_id_and_domain_id_for_push_campaign_send(cls, _id, domain_id):
        """
        This method returns a UrlConversion object that is associated to a campaign send object
        given by `send_id` and it belongs to domain with id `domain_id`.
        :param _id: UrlConversion id
        :type _id: int | long
        :param domain_id: Domain id of user
        :type domain_id: int | long
        :return: UrlConversion object | None
        :rtype: UrlConversion | None
        """
        # importing User and Domain here due to cyclic dependency
        from user import User, Domain
        return cls.query.join(PushCampaignSendUrlConversion).join(
            PushCampaignSend).join(PushCampaignBlast).join(PushCampaign).join(User).join(Domain).filter(
            PushCampaignSendUrlConversion.url_conversion_id == _id).filter(
            PushCampaign.user_id == User.id).filter(User.domain_id == domain_id).first()

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


