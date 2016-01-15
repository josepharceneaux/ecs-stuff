from sqlalchemy import and_
from db import db
from sqlalchemy.orm import relationship, backref
import datetime
from sqlalchemy.dialects.mysql import TINYINT
from email_marketing import EmailCampaignSend
from associations import ReferenceEmail
from venue import Venue
from event import Event


class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column('FirstName', db.String(50))
    middle_name = db.Column('MiddleName', db.String(50))
    last_name = db.Column('LastName', db.String(50))
    formatted_name = db.Column('FormattedName', db.String(150))
    candidate_status_id = db.Column('StatusId', db.Integer, db.ForeignKey('candidate_status.id'))
    is_web_hidden = db.Column('IsWebHidden', TINYINT, default=False)
    is_mobile_hidden = db.Column('IsMobileHidden', TINYINT, default=False)
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    user_id = db.Column('OwnerUserId', db.Integer, db.ForeignKey('user.id'))
    domain_can_read = db.Column('DomainCanRead', TINYINT, default=True)
    domain_can_write = db.Column('DomainCanWrite', TINYINT, default=False)
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

    # TODO: Below are necessary for now, but should remove once all tables have been defined
    is_dirty = db.Column('IsDirty', db.SmallInteger, default=0)

    # Relationships
    candidate_achievements = relationship('CandidateAchievement', cascade='all, delete-orphan', passive_deletes=True)
    candidate_addresses = relationship('CandidateAddress', cascade='all, delete-orphan', passive_deletes=True)
    candidate_associations = relationship('CandidateAssociation', cascade='all, delete-orphan', passive_deletes=True)
    candidate_custom_fields = relationship('CandidateCustomField', cascade='all, delete-orphan', passive_deletes=True)
    candidate_documents = relationship('CandidateDocument', cascade='all, delete-orphan', passive_deletes=True)
    candidate_educations = relationship('CandidateEducation', cascade='all, delete-orphan', passive_deletes=True)
    candidate_emails = relationship('CandidateEmail', cascade='all, delete-orphan', passive_deletes=True)
    candidate_experiences = relationship('CandidateExperience', cascade='all, delete-orphan', passive_deletes=True)
    candidate_languages = relationship('CandidateLanguage', cascade='all, delete-orphan', passive_deletes=True)
    candidate_license_certifications = relationship('CandidateLicenseCertification', cascade='all, delete-orphan', passive_deletes=True)
    candidate_military_services = relationship('CandidateMilitaryService', cascade='all, delete-orphan', passive_deletes=True)
    candidate_patent_histories = relationship('CandidatePatentHistory', cascade='all, delete-orphan', passive_deletes=True)
    candidate_phones = relationship('CandidatePhone', cascade='all, delete-orphan', passive_deletes=True)
    candidate_photos = relationship('CandidatePhoto', cascade='all, delete-orphan', passive_deletes=True)
    candidate_publications = relationship('CandidatePublication', cascade='all, delete-orphan', passive_deletes=True)
    candidate_preferred_locations = relationship('CandidatePreferredLocation', cascade='all, delete-orphan', passive_deletes=True)
    candidate_references = relationship('CandidateReference', cascade='all, delete-orphan', passive_deletes=True)
    candidate_skills = relationship('CandidateSkill', cascade='all, delete-orphan', passive_deletes=True)
    candidate_social_networks = relationship('CandidateSocialNetwork', cascade='all, delete-orphan', passive_deletes=True)
    candidate_text_comments = relationship('CandidateTextComment', cascade='all, delete-orphan', passive_deletes=True)
    candidate_work_preferences = relationship('CandidateWorkPreference', cascade='all, delete-orphan', passive_deletes=True)
    candidate_unidentifieds = relationship('CandidateUnidentified', cascade='all, delete-orphan', passive_deletes=True)
    email_campaign_sends = relationship('EmailCampaignSend', cascade='all, delete-orphan', passive_deletes=True)
    voice_comments = relationship('VoiceComment', cascade='all, delete-orphan', passive_deletes=True)

    def __repr__(self):
        return "<Candidate(formatted_name=' %r')>" % self.formatted_name

    def get_id(self):
        return unicode(self.id)

    @classmethod
    def get_by_id(cls, candidate_id):
        return cls.query.filter_by(id=candidate_id).first()

    @classmethod
    def get_by_first_last_name_owner_user_id_source_id_product(cls, first_name,
                                                               last_name,
                                                               user_id,
                                                               source_id,
                                                               product_id):
        assert user_id
        return cls.query.filter(
            and_(
                Candidate.first_name == first_name,
                Candidate.last_name == last_name,
                Candidate.user_id == user_id,
                Candidate.source_id == source_id,
                Candidate.source_product_id == product_id
            )
        ).first()

    @classmethod
    def set_is_web_hidden_to_true(cls, candidate_id):
        cls.query.filter_by(id=candidate_id).first().is_web_hidden = 1
        db.session.commit()


class CandidateStatus(db.Model):
    __tablename__ = 'candidate_status'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidates = relationship('Candidate', backref='candidate_status')

    def __repr__(self):
        return "<CandidateStatus(description=' %r')>" % self.description


class PhoneLabel(db.Model):
    __tablename__ = 'phone_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(20))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidate_phones = relationship('CandidatePhone', backref='phone_label')
    reference_phones = relationship('ReferencePhone', backref='phone_label')

    def __repr__(self):
        return "<PhoneLabel (description=' %r')>" % self.description

    @classmethod
    def phone_label_id_from_phone_label(cls, phone_label):
        """
        Function retrieves phone_label_id from phone_label
        e.g. 'Primary' => 1
        :return:  phone_label ID if phone_label is recognized, otherwise 6 ('Other')
        """
        if phone_label:
            phone_label_row = cls.query.filter_by(description=phone_label).first()
            if phone_label_row:
                return phone_label_row.id
        return 6


class CandidateSource(db.Model):
    __tablename__ = 'candidate_source'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    notes = db.Column('Notes', db.String(500))
    domain_id = db.Column('DomainId', db.Integer, db.ForeignKey('domain.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidates = relationship('Candidate', backref='candidate_source')

    def __repr__(self):
        return "<CandidateSource (description= '%r')>" % self.description

    @classmethod
    def get_by_description_and_notes(cls, source_name, source_description):
        assert source_description and source_name
        return cls.query.filter(
            and_(
                cls.description == source_name,
                cls.notes == source_description,
            )
        ).first()


class PublicCandidateSharing(db.Model):
    __tablename__ = 'public_candidate_sharing'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    notes = db.Column('Notes', db.String(500))
    title = db.Column('Title', db.String(100))
    candidate_id_list = db.Column('CandidateIdList', db.Text, nullable=False)
    hash_key = db.Column('HashKey', db.String(50))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

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

    # Relationships
    candidate = relationship('Candidate', backref='candidate_phone')

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def set_is_default_to_false(cls, candidate_id):
        for phone in cls.query.filter_by(candidate_id=candidate_id).all():
            phone.is_default = False


class EmailLabel(db.Model):
    __tablename__ = 'email_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidate_emails = relationship('CandidateEmail', backref='email_label')
    reference_emails = relationship('ReferenceEmail', backref='email_label')

    def __repr__(self):
        return "<EmailLabel (description=' %r')>" % self.description

    @classmethod
    def email_label_id_from_email_label(cls, email_label=None):
        """
        Function retrieves email_label_id from email_label
        e.g. 'Primary' => 1
        :return:  email_label ID if email_label is recognized, otherwise 4 ('Other')
        """
        if email_label:
            email_label_row = cls.query.filter(EmailLabel.description == email_label).first()
            if email_label_row:
                return email_label_row.id
        return 4



class CandidateEmail(db.Model):
    __tablename__ = 'candidate_email'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    email_label_id = db.Column('EmailLabelId', db.Integer, db.ForeignKey('email_label.id')) # 1 = Primary
    address = db.Column('Address', db.String(100))
    is_default = db.Column('IsDefault', db.Boolean)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidateEmail (address='%r')" % self.address

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def set_is_default_to_false(cls, candidate_id):
        for email in cls.query.filter_by(candidate_id=candidate_id).all():
            email.is_default = False

    @classmethod
    def get_by_address(cls, email_address):
        return cls.query.filter_by(address=email_address).first()


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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


class RatingTag(db.Model):
    __tablename__ = 'rating_tag'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidates = relationship('Candidate', secondary="candidate_rating")

    def __repr__(self):
        return "<RatingTag (description=' %r')>" % self.description


class RatingTagUser(db.Model):
    __tabelname__ = 'rating_tag_user'
    rating_tag_id = db.Column('RatingTagId', db.Integer, db.ForeignKey('rating_tag.id'), primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'), primary_key=True)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


class CandidateTextComment(db.Model):
    __tablename__ = 'candidate_text_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.Integer)
    comment = db.Column(db.String(5000))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


class VoiceComment(db.Model):
    __tablename__ = 'voice_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.Integer)
    filename = db.Column('Filename', db.String(260))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


class CandidateDocument(db.Model):
    __tablename__ = 'candidate_document'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    filename = db.Column('Filename', db.String(260))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())


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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidate_social_networks = relationship('CandidateSocialNetwork', backref='social_network')
    events = relationship("Event", backref='social_network', lazy='dynamic')
    user_credentials = relationship("UserSocialNetworkCredential")
    venues = relationship('Venue', backref='social_network', lazy='dynamic')

    def __repr__(self):
        return "<SocialNetwork (url=' %r')>" % self.url

    @classmethod
    def get_by_name(cls, name):
        assert name
        return cls.query.filter(
            SocialNetwork.name == name.strip()
        ).one()

    @classmethod
    def get_by_id(cls, id):
        assert id
        return cls.query.filter(
            SocialNetwork.id == id
        ).one()

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_all_except_ids(cls, ids):
        assert isinstance(ids, list)
        if ids:
            return cls.query.filter(
                db.not_(
                    SocialNetwork.id.in_(
                        ids
                    )
                )
            ).all()
        else:
            # Didn't input 'ids' it means we we need list of all, the following
            # probably help us avoid the expensive in_ with empty sequence
            SocialNetwork.get_all()

    @classmethod
    def get_by_ids(cls, ids):
        assert isinstance(ids, list)
        return cls.query.filter(
            SocialNetwork.id.in_(
                ids
            )
        ).all()


class CandidateSocialNetwork(db.Model):
    __tablename__ = 'candidate_social_network'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    social_network_id = db.Column('SocialNetworkId', db.Integer, db.ForeignKey('social_network.id'), nullable=False)
    social_profile_url = db.Column('SocialProfileUrl', db.String(250), nullable=False)

    def __repr__(self):
        return "<CandidateSocialNetwork (social_profile_url=' %r')>" % self.social_profile_url

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def get_by_candidate_id_and_sn_id(cls, candidate_id, social_network_id):
        assert candidate_id
        assert social_network_id
        return cls.query.filter(
            and_(
                cls.candidate_id == candidate_id,
                cls.social_network_id == social_network_id
            )
        ).first()


class CandidateWorkPreference(db.Model):
    __tablename__ = 'candidate_work_preference'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('candidateId', db.Integer, db.ForeignKey('candidate.id'))
    relocate = db.Column(db.CHAR(1), default='F')
    authorization = db.Column(db.String(255))
    telecommute = db.Column(db.CHAR(1), default='F')
    travel_percentage = db.Column(db.Integer, default=0)
    hourly_rate = db.Column(db.Float, default=0.0)
    salary = db.Column(db.Float, default=0.0)
    tax_terms = db.Column(db.String(255))
    security_clearance = db.Column(db.CHAR(1), default='F')
    third_party = db.Column(db.CHAR(1), default='F')

    def __repr__(self):
        return "<CandidateWorkPreference (authorization=' %r')>" % self.authorization

    @property
    def bool_third_party(self):
        if self.third_party == 'F':
            return False
        elif self.third_party == unicode(0):
            return False
        return True

    @property
    def bool_security_clearance(self):
        if self.security_clearance == 'F':
            return False
        elif self.security_clearance == unicode(0):
            return False
        return True

    @property
    def bool_telecommute(self):
        if self.telecommute == 'F':
            return False
        elif self.telecommute == unicode(0):
            return False
        return True

    @property
    def bool_relocate(self):
        if self.relocate == 'F':
            return False
        elif self.relocate == unicode(0):
            return False
        return True

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class CandidatePreferredLocation(db.Model):
    __tablename__ = 'candidate_preferred_location'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('candidateId', db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    address = db.Column(db.String(255))
    country_id = db.Column('countryId', db.Integer, db.ForeignKey('country.id'))
    city = db.Column(db.String(255))
    region = db.Column(db.String(255))
    zip_code = db.Column('zipcode', db.String(10))

    def __repr__(self):
        return "<CandidatePreferredLocation (candidate_id=' %r')>" % self.candidate_id

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidateLicenseCertification (name=' %r')>" % self.name


class CandidateReference(db.Model):
    __tablename__ = 'candidate_reference'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    person_name = db.Column('PersonName', db.String(150))
    position_title = db.Column('PositionTitle', db.String(150))
    comments = db.Column('Comments', db.String(5000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidateAssociation (candidate_id=' %r')>" % self.candidate_id


class CandidateAchievement(db.Model):
    __tablename__ = 'candidate_achievement'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column('Date', db.DateTime)
    issuing_authority = db.Column('IssuingAuthority', db.String(150))
    description = db.Column('Description', db.String(10000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # TODO: Below are necessary for now, but should remove once all tables have been defined
    resume_id = db.Column('ResumeId', db.BigInteger, nullable=True)

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def __repr__(self):
        return "<CandidateMilitaryService (candidate_id=' %r')>" % self.candidate_id


class CandidatePatentHistory(db.Model):
    __tablename__ = 'candidate_patent_history'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(255))
    description = db.Column('Description', db.String(10000))
    link = db.Column('Link', db.String(150))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidatePatentHistory (title=' %r')>" % self.title


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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
    # TODO: Below are necessary for now, but should remove once all tables have been defined
    resume_id = db.Column('ResumeId', db.BigInteger, nullable=True)

    def __repr__(self):
        return "<CandidateAddress (id = %r)>" % self.id

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def set_is_default_to_false(cls, candidate_id):
        for address in cls.query.filter_by(candidate_id=candidate_id).all():
            address.is_default = False


class CandidateEducation(db.Model):
    __tablename__ = 'candidate_education'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    school_name = db.Column('SchoolName', db.String(200))
    school_type = db.Column('SchoolType', db.String(100))
    city = db.Column('City', db.String(50))
    state = db.Column('State', db.String(50))
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    is_current = db.Column('IsCurrent', db.Boolean)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
    # TODO: Below are necessary for now, but should remove once all tables have been defined
    resume_id = db.Column('ResumeId', db.BigInteger, nullable=True)

    # Relationships
    candidate_education_degrees = relationship(
        'CandidateEducationDegree', cascade='all, delete-orphan', passive_deletes=True
    )

    def __repr__(self):
        return "<CandidateEducation (candidate_id = %r)>" % self.candidate_id

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def set_is_current_to_false(cls, candidate_id):
        for education in cls.query.filter_by(candidate_id=candidate_id).all():
            education.is_current = False


class CandidateEducationDegree(db.Model):
    __tablename__ = 'candidate_education_degree'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_education_id = db.Column('CandidateEducationId', db.BigInteger, db.ForeignKey('candidate_education.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    degree_type = db.Column('DegreeType', db.String(100))
    degree_title = db.Column('DegreeTitle', db.String(100))
    start_year = db.Column('StartYear', db.Integer)
    start_month = db.Column('StartMonth', db.SmallInteger)
    end_year = db.Column('EndYear', db.Integer)
    end_month = db.Column('EndMonth', db.SmallInteger)
    gpa_num = db.Column('GpaNum', db.DECIMAL)
    gpa_denom = db.Column('GpaDenom', db.DECIMAL)
    added_time = db.Column('AddedTime', db.DateTime)
    classification_type_id = db.Column('ClassificationTypeId', db.Integer, db.ForeignKey('classification_type.id'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())
    start_time = db.Column('StartTime', db.DateTime)
    end_time = db.Column('EndTime', db.DateTime)

    # Relationships
    candidate_education = relationship('CandidateEducation', backref=backref(
        'candidate_education_degree', cascade='all, delete-orphan', passive_deletes=True
    ))
    candidate_education_degree_bullets = relationship(
            'CandidateEducationDegreeBullet', cascade='all, delete-orphan', passive_deletes=True
    )

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
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    candidate_education_degree = relationship('CandidateEducationDegree', backref=backref(
        'candidate_education_degree_bullet', cascade='all, delete-orphan', passive_deletes=True
    ))

    def __repr__(self):
        return "<CandidateEducationDegreeBullet (candidate_education_degree_id=' %r')>" % \
               self.candidate_education_degree_id


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
    start_year = db.Column('StartYear', db.Integer)
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    start_month = db.Column('StartMonth', db.SmallInteger)
    end_year = db.Column('EndYear', db.Integer)
    is_current = db.Column('IsCurrent', db.Boolean, default=False)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # TODO: Below are necessary for now, but should remove once all tables have been defined
    resume_id = db.Column('ResumeId', db.BigInteger, nullable=True)

    # Relationships
    candidate = relationship('Candidate', backref=backref(
        'candidate_experience', cascade='all, delete-orphan', passive_deletes=True
    ))
    candidate_experience_bullets = relationship(
            'CandidateExperienceBullet', cascade='all, delete-orphan', passive_deletes=True
    )

    def __repr__(self):
        return "<CandidateExperience (candidate_id=' %r)>" % self.candidate_id

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def set_is_current_to_false(cls, candidate_id):
        experiences = cls.query.filter_by(candidate_id=candidate_id).all()
        for experience in experiences:
            experience.is_current = False


class CandidateExperienceBullet(db.Model):
    __tablename__ = 'candidate_experience_bullet'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_experience_id = db.Column('CandidateExperienceId', db.BigInteger, db.ForeignKey('candidate_experience.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    description = db.Column('Description', db.String(10000))
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # Relationship
    candidate_experience = relationship('CandidateExperience', backref=backref(
            'candidate_experience_bullet', cascade='all, delete-orphan', passive_deletes=True
    ))

    def __repr__(self):
        return "<CandidateExperienceBullet (candidate_experience_id=' %r')>" % self.candidate_experience_id


class CandidateSkill(db.Model):
    __tablename__ = 'candidate_skill'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    description = db.Column('Description', db.String(10000))
    added_time = db.Column('AddedTime', db.DateTime)
    total_months = db.Column('TotalMonths', db.Integer)
    last_used = db.Column('LastUsed', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    # TODO: Below are necessary for now, but should remove once all tables have been defined
    resume_id = db.Column('ResumeId', db.BigInteger, nullable=True)

    def __repr__(self):
        return "<CandidateSkill (candidate_id=' %r')>" % self.candidate_id

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class CandidateUnidentified(db.Model):
    __tablename__ = 'candidate_unidentified'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_Id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(100))
    description = db.Column('Description', db.Text)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidateUnidentified (title=' %r')>" % self.title


class CandidateCustomField(db.Model):
    __tablename__ = 'candidate_custom_field'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column('Value', db.Text)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'))
    custom_field_id = db.Column('CustomFieldId', db.Integer, db.ForeignKey('custom_field.id', ondelete='CASCADE'))
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidateCustomField (id = %r)>" % self.id

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def get_custom_field(cls, candidate_id, custom_field_id):
        return cls.query.filter(db.and_(CandidateCustomField.candidate_id == candidate_id,
                                        CandidateCustomField.custom_field_id == custom_field_id)).first()

    @classmethod
    def get_candidate_custom_fields(cls, candidate_id):
        return cls.query.filter_by(candidate_id=candidate_id).all()


class ClassificationType(db.Model):
    __tablename__ = 'classification_type'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column('Code', db.String(100))
    description = db.Column('Description', db.String(250))
    notes = db.Column('Notes', db.String(500))
    list_order = db.Column('ListOrder', db.Integer)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<ClassificationType (code = %r)>" % self.code

    @classmethod
    def classification_type_id_from_degree_type(cls, degree_type):
        """
        Function will return classification_type ID of the ClassificationType that
        matches degree_type. E.g. degree_type = 'Masters' => ClassificationType.id: 5
        """
        classification_type = None
        if degree_type:
            classification_type = cls.query.filter(ClassificationType.code == degree_type).first()

        return classification_type.id if classification_type else None


class CandidateSubscriptionPreference(db.Model):
    __tablename__ = 'candidate_subscription_preference'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('candidateId', db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'))
    frequency_id = db.Column('frequencyId', db.Integer, db.ForeignKey('frequency.id', ondelete='CASCADE'))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<CandidateSubscriptionPreference (candidate_id = %r)>" % self.candidate_id

    @classmethod
    def get_by_candidate_id(cls, candidate_id):
        return cls.query.filter_by(candidate_id=candidate_id).first()