from sqlalchemy.orm import relationship
from db import db
import datetime
import time


class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column('FirstName', db.String(50))
    middle_name = db.Column('MiddleName', db.String(50))
    last_name = db.Column('LastName', db.String(50))
    formatted_name = db.Column('FormattedName', db.String(150))
    candidate_status_id = db.Column('StatusId', db.Integer, db.ForeignKey('candidate_status.id'))
    # is_dirty = db.Column('IsDirty', db.Boolean)
    is_web_hidden = db.Column('IsWebHidden', db.Boolean, default=False)
    is_mobile_hidden = db.Column('IsMobileHidden', db.Boolean, default=False)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    user_id = db.Column('OwnerUserId', db.Integer, db.ForeignKey('user.id'))
    domain_can_read = db.Column('DomainCanRead', db.Boolean, default=True)
    domain_can_write = db.Column('DomainCanWrite', db.Boolean, default=False)
    dice_social_profile_id = db.Column('DiceSocialProfileId', db.String(128))
    dice_profile_id = db.Column('DiceProfileId', db.String(128))
    candidate_source_id = db.Column('sourceId', db.Integer, db.ForeignKey('candidate_source.id'))
    source_product_id = db.Column('sourceProductId', db.Integer, db.ForeignKey('product.id'), nullable=False, default=2) # Web = 2
    filename = db.Column(db.String(100))
    objective = db.Column(db.Text)
    summary = db.Column(db.Text)
    total_months_experience = db.Column('totalMonthsExperience', db.Integer)
    resume_text = db.Column('resumeText', db.Text)
    culture_id = db.Column('cultureId', db.Integer, db.ForeignKey('culture.id'), default=1)

    # One-to-many Relationships; i.e. Candidate has many:
    candidate_achievements = relationship('CandidateAchievement', backref='candidate')
    candidate_phones = relationship('CandidatePhone', backref='candidate')
    candidate_emails = relationship('CandidateEmail', backref='candidate')
    candidate_photos = relationship('CandidatePhoto', backref='candidate')
    candidate_text_comments = relationship('CandidateTextComment', backref='candidate')
    voice_comments = relationship('VoiceComment', backref='candidate')
    candidate_documents = relationship('CandidateDocument', backref='candidate')
    candidate_work_preferences = relationship('CandidateWorkPreference', backref='candidate')
    candidate_preferred_locations = relationship('CandidatePreferredLocation', backref='candidate')
    candidate_social_network = relationship('CandidateSocialNetwork', backref='candidate')

    # Many-to-many Relationships
    # rating_tags = relationship('RatingTag', secondary=candidate_rating)

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<Candidate(formatted_name=' %r')>" % self.formatted_name


class CandidateAchievement(db.Model):
    __tablename__ = 'candidate_achievement'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column('Date', db.DateTime)
    issuing_authority = db.Column('IssuingAuthority', db.String(150))
    description = db.Column('Description', db.String(10000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))

    def __repr__(self):
        return "<CandidateAchievement (description=' %r')>" % self.description


class CandidateStatus(db.Model):
    __tablename = 'candidate_status'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # One-to-many Relationships
    candidates = relationship('Candidate', backref='candidate_status')

    def __repr__(self):
        return "<CandidateStatus(description=' %r')>" % self.description


class PhoneLabel(db.Model):
    __tablename__ = 'phone_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(20))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # One-to-many Relationships
    candidate_phones = relationship('CandidatePhone', backref='phone_label')

    def __repr__(self):
        return "<PhoneLabel (description=' %r')>" % self.description


class CandidateSource(db.Model):
    __tablename__ = 'candidate_source'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    notes = db.Column('Notes', db.String(500))
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # One-to-many Relationships
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
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    phone_label_id = db.Column(db.Integer, db.ForeignKey('phone_label.id'))
    value = db.Column(db.String(50), nullable=False)
    extension = db.Column(db.String(5))
    is_default = db.Column(db.Boolean)

    def __repr__(self):
        return "<CandidatePhone (value=' %r', extention= ' %r')>" % (self.value, self.extension)


class EmailLabel(db.Model):
    __tablename__ = 'email_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # One-to-many Relationships
    candidate_emails = relationship('CandidateEmail', backref='email_label')

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
    is_default = db.Column(db.Boolean)

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

    # Many-to-many Relationship
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
    candidate_id = db.Column('CandidatedId', db.Integer, db.ForeignKey('candidate.id'))
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




















