from db import db
from sqlalchemy.orm import relationship
import datetime
import time

from associations import ReferenceEmail

class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column('FirstName', db.String(50))
    middle_name = db.Column('MiddleName', db.String(50))
    last_name = db.Column('LastName', db.String(50))
    formatted_name = db.Column('FormattedName', db.String(150))
    candidate_status_id = db.Column('StatusId', db.Integer, db.ForeignKey('candidate_status.id'))
    is_web_hidden = db.Column('IsWebHidden', db.Boolean, default=False)
    is_mobile_hidden = db.Column('IsMobileHidden', db.Boolean, default=False)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    user_id = db.Column('OwnerUserId', db.Integer, db.ForeignKey('user.id'))
    domain_can_read = db.Column('DomainCanRead', db.Boolean, default=True)
    domain_can_write = db.Column('DomainCanWrite', db.Boolean, default=False)
    dice_social_profile_id = db.Column('DiceSocialProfileId', db.String(128))
    dice_profile_id = db.Column('DiceProfileId', db.String(128))
    source_id = db.Column('sourceId', db.Integer, db.ForeignKey('candidate_source.id'))
    source_product_id = db.Column('sourceProductId', db.Integer, db.ForeignKey('product.id'), nullable=False, default=2) # Web = 2
    filename = db.Column(db.String(100))
    objective = db.Column(db.Text)
    summary = db.Column(db.Text)
    total_months_experience = db.Column('totalMonthsExperience', db.Integer)
    resume_text = db.Column('resumeText', db.Text)
    culture_id = db.Column('cultureId', db.Integer, db.ForeignKey('culture.id'), default=1)

    # One-to-many Relationships; i.e. Candidate has many:
    candidate_phones = relationship('CandidatePhone', backref='candidate')
    candidate_emails = relationship('CandidateEmail', backref='candidate')
    candidate_photos = relationship('CandidatePhoto', backref='candidate')
    candidate_text_comments = relationship('CandidateTextComment', backref='candidate')
    voice_comments = relationship('VoiceComment', backref='candidate')
    candidate_documents = relationship('CandidateDocument', backref='candidate')
    candidate_work_preferences = relationship('CandidateWorkPreference', backref='candidate')
    candidate_preferred_locations = relationship('CandidatePreferredLocation', backref='candidate')
    candidate_social_network = relationship('CandidateSocialNetwork', backref='candidate')
    candidate_languages = relationship('CandidateLanguage', backref='candidate')
    candidate_license_certifications = relationship('CandidateLicenseCertification', backref='candidate')
    candidate_references = relationship('CandidateReference', backref='candidate')
    candidate_associations = relationship('CandidateAssociation', backref='candidate')
    candidate_achievements = relationship('CandidateAchievement', backref='candidate')
    candidate_military_services = relationship('CandidateMilitaryService', backref='candidate')
    candidate_patent_histories = relationship('CandidatePatentHistory', backref='candidate')
    candidate_publications = relationship('CandidatePublication', backref='candidate')
    candidate_addresses = relationship('CandidateAddress', backref='candidate')
    candidate_educations = relationship('CandidateEducation', backref='candidate')
    candidate_skills = relationship('CandidateSkill', backref='candidate')
    candidate_unidentifieds = relationship('CandidateUnidentified', backref='candidate')

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<Candidate(formatted_name=' %r')>" % self.formatted_name


class CandidateStatus(db.Model):
    __tablename = 'candidate_status'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidates = relationship('Candidate', backref='candidate_status')

    def __repr__(self):
        return "<CandidateStatus(description=' %r')>" % self.description


class PhoneLabel(db.Model):
    __tablename__ = 'phone_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(20))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_phones = relationship('CandidatePhone', backref='phone_label')
    reference_phones = relationship('ReferencePhone', backref='phone_label')

    def __repr__(self):
        return "<PhoneLabel (description=' %r')>" % self.description


class CandidateSource(db.Model):
    __tablename__ = 'candidate_source'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    notes = db.Column('Notes', db.String(500))
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidates = relationship('Candidate', backref='candidate_source')

    def __repr__(self):
        return "<CandidateSource (description= '%r')>" % self.description


class PublicCandidateSharing(db.Model):
    __tablename__ = 'public_candidate_sharing'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    notes = db.Column('Notes', db.String(500))
    title = db.Column('Title', db.String(100))
    candidate_id_list = db.Column('CandidateIdList', db.Text, nullable=False)
    hash_key = db.Column('HashKey', db.String(50))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<PublicCandidateSharing (title=' %r')>" % self.title


class CandidatePhone(db.Model):
    __tablename__ = 'candidate_phone'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    phone_label_id = db.Column('PhoneLabelId', db.Integer, db.ForeignKey('phone_label.id'))
    value = db.Column(db.String(50), nullable=False)
    extension = db.Column(db.String(5))
    is_default = db.Column('IsDefault', db.Boolean)

    def __repr__(self):
        return "<CandidatePhone (value=' %r', extention= ' %r')>" % (self.value, self.extension)


class EmailLabel(db.Model):
    __tablename__ = 'email_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_emails = relationship('CandidateEmail', backref='email_label')
    reference_emails = relationship('ReferenceEmail', backref='email_label')

    def __repr__(self):
        return "<EmailLabel (description=' %r')>" % self.description


class CandidateEmail(db.Model):
    __tablename__ = 'candidate_email'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    email_label_id = db.Column('EmailLabelId', db.Integer, db.ForeignKey('email_label.id')) # 1 = Primary
    address = db.Column('Address', db.String(100))
    is_default = db.Column('IsDefault', db.Boolean)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())


class CandidatePhoto(db.Model):
    __tablename__ = 'candidate_photo'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.Integer)
    filename = db.Column(db.String(260))
    is_default = db.Column('IsDefault', db.Boolean)

    def __repr__(self):
        return "<CandidatePhoto (filename=' %r')>" % self.filename


class CandidateRating(db.Model):
    __tablename__ = 'candidate_rating'
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'), primary_key=True)
    rating_tag_id = db.Column('RatingTagId', db.Integer, db.ForeignKey('rating_tag.id'), primary_key=True)
    value = db.Column('Value', db.Integer, default=0)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())


class RatingTag(db.Model):
    __tablename__ = 'rating_tag'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidates = relationship('Candidate', secondary="candidate_rating")

    def __repr__(self):
        return "<RatingTag (desctiption=' %r')>" % self.description


class RatingTagUser(db.Model):
    __tabelname__ = 'rating_tag_user'
    rating_tag_id = db.Column('RatingTagId', db.Integer, db.ForeignKey('rating_tag.id'), primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'), primary_key=True)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())


class CandidateTextComment(db.Model):
    __tablename__ = 'candidate_text_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.Integer)
    comment = db.Column(db.String(5000))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())


class VoiceComment(db.Model):
    __tablename__ = 'voice_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.Integer)
    filename = db.Column('Filename', db.String(260))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())


class CandidateDocument(db.Model):
    __tablename__ = 'candidate_document'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    filename = db.Column('Filename', db.String(260))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())


class SocialNetwork(db.Model):
    __tablename__ = 'social_network'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100), nullable=False)
    url = db.Column('Url', db.String(255))
    api_url = db.Column('apiUrl', db.String(255))
    client_key = db.Column('clientKey', db.String(500))
    secret_key = db.Column('secretKey', db.String(500))
    redirect_uri = db.Column('redirectUri', db.String(255))
    auth_url = db.Column('authUrl', db.String(200))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_social_networks = relationship('CandidateSocialNetwork', backref='social_network')

    def __repr__(self):
        return "<SocialNetwork (url=' %r')>" % self.url


class CandidateSocialNetwork(db.Model):
    __tablename__ = 'candidate_social_network'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    social_network_id = db.Column('SocialNetworkId', db.Integer, db.ForeignKey('social_network.id'), nullable=False)
    social_profile_url = db.Column('SocialProfileUrl', db.String(250), nullable=False)

    def __repr__(self):
        return "<CandidateSocialNetwork (social_profile_url=' %r')>" % self.social_profile_url


class CandidateWorkPreference(db.Model):
    __tablename__ = 'candidate_work_preference'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('candidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    relocate = db.Column(db.Boolean, default=False)
    authorization = db.Column(db.String(250))
    telecommute = db.Column(db.Boolean, default=False)
    travel_percentage = db.Column(db.Integer, default=0)
    hourly_rate = db.Column(db.Float, default=0.0)
    salary = db.Column(db.Float, default=0.0)
    tax_terms = db.Column(db.String(255))
    security_clearance = db.Column(db.Boolean, default=False)
    third_party = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<CandidateWorkPreference (authorization=' %r')>" % self.authorization


class CandidatePreferredLocation(db.Model):
    __tablename__ = 'candidate_preferred_location'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('candidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    address = db.Column(db.String(255))
    country_id = db.Column('countryId', db.Integer, db.ForeignKey('country.id'))
    city = db.Column(db.String(255))
    region = db.Column(db.String(255))
    zipcode = db.Column(db.String(10))

    def __repr__(self):
        return "<CandidatePreferredLocation (candidate_id=' %r')>" % self.candidate_id


class Language(db.Model):
    __tablename__ = 'language'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(200))
    code = db.Column('Code', db.String(3), unique=True)

    # Relationships
    candidate_languages = relationship('CandidateLanguage', backref='language')

    def __repr__(self):
        return "<Language (code=' %r')>" % self.code


class CandidateLanguage(db.Model):
    __tablename__ = 'candidate_language'
    id = db.Column(db.BigInteger, primary_key=True)
    language_id = db.Column('LanguageId', db.Integer, db.ForeignKey('language.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    can_read = db.Column('CanRead', db.Boolean)
    can_write = db.Column('CanWrite', db.Boolean)
    can_speak = db.Column('CanSpeak', db.Boolean)
    read = db.Column('Read', db.Boolean)
    write = db.Column('Write', db.Boolean)
    speak = db.Column('Speak', db.Boolean)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateLanguage (candidate_id=' %r')>" % self.candidate_id


class CandidateLicenseCertification(db.Model):
    __tablename__ = 'candidate_license_certification'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    name = db.Column('Name', db.String(500))
    description = db.Column('Description', db.String(10000))
    issuing_authority = db.Column('IssuingAuthority', db.String(255))
    valid_from = db.Column('ValidFrom', db.String(30))
    valid_to = db.Column('ValidTo', db.String(30))
    first_issued_date = db.Column('FirstIssuedDate', db.String(30))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateLicenseCertification (name=' %r')>" % self.name


class CandidateReference(db.Model):
    __tablename__ = 'candidate_reference'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    person_name = db.Column('PersonName', db.String(150))
    position_title = db.Column('PositionTitle', db.String(150))
    comments = db.Column('Comments', db.String(5000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    reference_emails = relationship('ReferenceEmail', backref='candidate_reference')
    reference_phones = relationship('ReferencePhone', backref='candidate_reference')
    reference_web_addresses = relationship('ReferenceWebAddress', backref='candidate_reference')

    def __repr__(self):
        return "<CandidateReference (candidate_id=' %r')>" % self.candidate_id


class ReferenceWebAddress(db.Model):
    __tablename__ = 'reference_web_address'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.id'))
    url = db.Column('Url', db.String(200))
    description = db.Column('Description', db.String(1000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<ReferenceWebAddress (url=' %r')>" % self.url


class CandidateAssociation(db.Model):
    __tablename__ = 'candidate_association'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(255))
    description = db.Column('Description', db.String(5000))
    link = db.Column('Link', db.String(200))
    start_date = db.Column('StartDate', db.DateTime)
    end_date = db.Column('EndDate', db.DateTime)
    comments = db.Column('Comments', db.String(10000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateAssociation (candidate_id=' %r')>" % self.candidate_id


class CandidateAchievement(db.Model):
    __tablename__ = 'candidate_achievement'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column('Date', db.DateTime)
    issuing_authority = db.Column('IssuingAuthority', db.String(150))
    description = db.Column('Description', db.String(10000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))

    def __repr__(self):
        return "<CandidateAchievement (candidate_id=' %r')>" % self.candidate_id


class CandidateMilitaryService(db.Model):
    __tablename__ = 'candidate_military_service'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    service_status = db.Column('ServiceStatus', db.String(200))
    highest_rank = db.Column('HighestRank', db.String(255))
    highest_grade = db.Column('HighestGrade', db.String(7))
    branch = db.Column('Branch', db.String(200))
    comments = db.Column('Comments', db.String(5000))
    from_date = db.Column('FromDate', db.DateTime)
    to_date = db.Column('ToDate', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateMilitaryService (candidate_id=' %r')>" % self.candidate_id


class CandidatePatentHistory(db.Model):
    __tablename__ = 'candidate_patent_history'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(255))
    description = db.Column('Description', db.String(10000))
    link = db.Column('Link', db.String(150))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidatePatentHistory (title=' %r')>" % self.title


class PatentDetail(db.Model):
    __tabelname__ = 'patent_detail'
    id = db.Column(db.BigInteger, primary_key=True)
    patent_id = db.Column('PatentId', db.BigInteger, db.ForeignKey('patent.id')) # TODO: add relationship
    issuing_authority = db.Column('IssuingAuthority', db.String(255))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<PatentDetail (patent_id=' %r')>" % self.patent_id


class PatentStatus(db.Model):
    __tablename__ = 'patent_status'
    id = db.Column(db.BigInteger, primary_key=True)
    description = db.Column('Description', db.String(1000))
    notes = db.Column('Notes', db.String(1000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    patent_milestones = relationship('PatentMilestone', backref='patent_status')

    def __repr__(self):
        return "<PatentStatus (id=' %r')>" % self.id


class PatentInventor(db.Model):
    __tablename__ = 'patent_inventor'
    id = db.Column(db.BigInteger, primary_key=True)
    patent_id = db.Column('PatentId', db.BigInteger, db.ForeignKey('patent.id')) # TODO: add relationship
    name = db.Column('Name', db.String(500))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<PatentInventor (patent_id=' %r')>" % self.patent_id


class PatentMilestone(db.Model):
    __tabelname__ = 'patent_milestone'
    id = db.Column(db.BigInteger, primary_key=True)
    patent_status_id = db.Column('StatusId', db.Integer, db.ForeignKey('patent_status.id'))
    issued_date = db.Column('IssuedDate', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<PatentMilestone (patent_status_id=' %r')>" % self.patent_status_id


class CandidatePublication(db.Model):
    __tablename__ = 'candidate_publication'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(200))
    start_year = db.Column('StartYear', db.Integer)    # todo: accept Year format only or create a function to validate
    start_month = db.Column('StartMonth', db.Integer)
    end_year = db.Column('EndYear', db.Integer)        # todo: accept Year format only or create a function to validate
    end_month = db.Column('EndMonth', db.Integer)
    description = db.Column('Description', db.String(10000))
    added_time = db.Column('AddedTime', db.DateTime)
    link = db.Column('Link', db.String(200))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidatePublication (title=' %r')>" % self.title


class CandidateAddress(db.Model):
    __tablename__ = 'candidate_address'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    address_line_1 = db.Column('AddressLine1', db.String(255))
    address_line_2 = db.Column('AddressLine2', db.String(255))
    city = db.Column('City', db.String(100))
    state = db.Column('State', db.String(100))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    zip_code = db.Column('ZipCode', db.String(10))
    po_box = db.Column('POBox', db.String(20))
    is_default = db.Column('IsDefault', db.Boolean, default=False)  # todo: check other is_default fields for their default values
    coordinates = db.Column('Coordinates', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateAddress (candidate_id=' %r')>" % self.candidate_id


class CandidateEducation(db.Model):
    __tablename__ = 'candidate_education'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)    # todo: ascertain smallinteger == tinyint; also check all list_order columns in db
    school_name = db.Column('SchoolName', db.String(200))
    school_type = db.Column('SchoolType', db.String(100))
    city = db.Column('City', db.String(50))
    state = db.Column('State', db.String(50))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    is_current = db.Column('IsCurrent', db.Boolean)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_education_degrees = relationship('CandidateEducationDegree', backref='candidate_education')

    def __repr__(self):
        return "<CandidateEducation (candidate_id=' %r')>" % self.candidate_id


class CandidateEducationDegree(db.Model):
    __tablename__ = 'candidate_education_degree'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_education_id = db.Column('CandidateEducationId', db.BigInteger, db.ForeignKey('candidate_education.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    degree_type = db.Column('DegreeType', db.String(100))
    degree_title = db.Column('DegreeTitle', db.String(100))
    start_year = db.Column('StartYear', db.Integer)  # todo: accept Year format only or create a function to validate
    start_month = db.Column('StartMonth', db.SmallInteger)
    end_year = db.Column('EndYear', db.Integer)  # todo: accept Year format only or create a function to validate
    end_month = db.Column('EndMonth', db.SmallInteger)
    gpa_num = db.Column('GpaNum', db.DECIMAL)
    gpa_denom = db.Column('GpaDenom', db.DECIMAL)
    added_time = db.Column('AddedTime', db.DateTime)
    classification_type_id = db.Column('ClassificationTypeId', db.Integer, db.ForeignKey('classification_type.id')) # todo: create parent table
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())
    start_time = db.Column('StartTime', db.DateTime)
    end_time = db.Column('EndTime', db.DateTime)

    # Relationships
    candidate_education_degree_bullets = relationship('CandidateEducationDegreeBullet', backref='candidate_education_degree')

    def __repr__(self):
        return "<CandidateEducationDegree (candidate_education_id=' %r')>" % self.candidate_education_id


class CandidateEducationDegreeBullet(db.Model):
    __tablename__ = 'candidate_education_degree_bullet'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_education_degree_id = db.Column('CandidateEducationDegreeId', db.BigInteger, db.ForeignKey('candidate_education_degree.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    concentration_type = db.Column('ConcentrationType', db.String(200))
    comments = db.Column('Comments', db.String(5000))
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateEducationDegreeBullet (candidate_education_degree_id=' %r')>" % self.candidate_education_degree_id


class CandidateExperience(db.Model):
    __tablename__ = 'candidate_experience'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    organization = db.Column('Organization', db.String(150))
    position = db.Column('Position', db.String(150))
    city = db.Column('City', db.String(50))
    state = db.Column('State', db.String(50))
    end_month = db.Column('EndMonth', db.SmallInteger)
    start_year = db.Column('StartYear', db.Integer)  # todo: accept Year format only or create a function to validate
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    start_month = db.Column('StartMonth', db.SmallInteger)
    end_year = db.Column('EndYear', db.Integer)  # todo: accept Year format only or create a function to validate
    is_current = db.Column('IsCurrent', db.Boolean, default=False)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_experience_bullets = relationship('CandidateExperienceBullet', backref='candidate_experience')

    def __repr__(self):
        return "<CandidateExperience (candidate_id=' %r)>" % self.candidate_id


class CandidateExperienceBullet(db.Model):
    __tablename__ = 'candidate_experience_bullet'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_experience_id = db.Column('CandidateExperienceId', db.BigInteger, db.ForeignKey('candidate_experience.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    description = db.Column('Description', db.String(10000))
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateExperienceBullet (candidate_experience_id=' %r')>" % self.candidate_experience_id


class CandidateSkill(db.Model):
    __tablename__ = 'candidate_skill'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    description = db.Column('Description', db.String(10000))
    added_time = db.Column('AddedTime', db.DateTime)
    totla_months = db.Column('TotalMonths', db.Integer)
    last_used = db.Column('LastUsed', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateSkill (candidate_id=' %r')>" % self.candidate_id


class CandidateUnidentified(db.Model):
    __tablename__ = 'candidate_unidentified'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_Id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(100))
    description = db.Column('Description', db.Text)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateUnidentified (title=' %r')>" % self.title


class University(db.Model):
    __tablename__ = 'university'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(255))
    state_id = db.Column('StateId', db.Integer, db.ForeignKey('state.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<University (name=' %r')>" % self.name
















