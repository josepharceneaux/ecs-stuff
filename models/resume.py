from models import db
from user import Culture
from candidate import *
from product import Product
from job import JobOpening
from sqlalchemy.orm import relationship, backref
from auth_service.oauth import logger
import time

# TODO: Update joint tables for many-to-many relationships

class Resume(db.Model):
    __tablename__ = 'resume'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    job_opening_id = db.Column('JobOpeningId', db.BigInteger, db.ForeignKey('job_opening.id'))
    candidate_source_id = db.Column('SourceId', db.Integer, db.ForeignKey('source.id'))
    source_product_id = db.Column('SourceProductId', db.Integer, db.ForeignKey('source_product.id'))
    culture_id = db.Column('CultureId', db.Integer, db.ForeignKey('culture.id'))
    resume_xml_directory_tag_id = db.Column('ResumeXmlDirectoryTagId', db.Integer)
    filename = db.Column('Filename', db.String(260))
    filename_directory_tag_id = db.Column('FilenameDirectoryTagId', db.Integer)
    search_flag = db.Column('SearchFlag', db.SmallInteger)
    objective = db.Column('Objective', db.Text)
    current_job_title = db.Column('CurrentJobTitle', db.String(200))
    summary = db.Column('Summary', db.Text)
    total_months_experience = db.Column('TotalMonthsExperience', db.SmallInteger)
    current_employer = db.Column('CurrentEmployer', db.String(100))
    highest_education = db.Column('HighestEducation', db.String(200))
    current_salary = db.Column('CurrentSalary', db.String(100))
    expected_salary = db.Column('ExpectedSalary', db.String(100))
    resume_text = db.Column('ResumeText', db.Text)
    availability = db.Column('Availability', db.DateTime)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_languages = relationship('CandidateLanguage', backref='resume')
    candidate_license_certifications = relationship('CandidateLicenseCertification', backref='resume')
    candidate_references = relationship('CandidateReference', backref='resume')
    candidate_associations = relationship('CandidateAssociation', backref='resume')
    candidate_achievements = relationship('CandidateAchievement', backref='resume')
    candidate_military_services = relationship('CandidateMilitaryService', backref='resume')
    candidate_patent_histories = relationship('CandidatePatentHistory', backref='resume')
    candidate_publications = relationship('CandidatePublicationsd', backref='resume')
    candidate_addresses = relationship('CandidateAddress', backref='resume')
    candidate_educations = relationship('CandidateEducation', backref='resume')
    candidate_skills = relationship('CandidateSkill', backref='resume')
    candidate_unidentifieds = relationship('CandidateUnidentified', backref='resume')

    def __repr__(self):
        return "<Resume (CandidateId=' %r')>" % self.candidate_id


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
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    can_read = db.Column('CanRead', db.Boolean)
    can_write = db.Column('CanWrite', db.Boolean)
    can_speak = db.Column('CanSpeak', db.Boolean)
    read = db.Column('Read', db.Boolean)
    write = db.Column('Write', db.Boolean)
    speak = db.Column('Speak', db.Boolean)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateLanguage (resume_id=' %r')>" % self.resume_id


class CandidateLicenseCertification(db.Model):
    __tablename__ = 'candidate_license_certification'
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
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
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
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
        return "<CandidateReference (resume_id=' %r')>" % self.resume_id


class ReferenceEmail(db.Model):
    # TODO: JOINT TABLE
    __tablename__ = 'reference_email'
    candidate_reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('candidate_reference.id'))
    email_label_id = db.Column('EmailLabelId', db.Integer, db.ForeignKey('email_label.id'))
    is_default = db.Column('IsDefault', db.Boolean)
    value = db.Column('Value', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<ReferenceEmail (reference_id=' %r')>" % self.candidate_reference_id


class ReferencePhone(db.Model):
    # TODO: JOINT TABLE
    __tablename__ = 'reference_phone'
    candidate_reference_id = db.Column('ReferenceId', db.BigInteger, db.ForeignKey('reference.id'), primary_key=True)
    phone_label_id = db.Column('PhoneLabelId', db.Integer)
    is_default = db.Column('IsDefault', db.Boolean)
    value = db.Column('Value', db.String(50))
    extension = db.Column('Extension', db.String(10))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<ReferencePhone (reference_id=' %r')>" % self.candidate_reference_id


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
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(255))
    description = db.Column('Description', db.String(5000))
    link = db.Column('Link', db.String(200))
    start_date = db.Column('StartDate', db.DateTime)
    end_date = db.Column('EndDate', db.DateTime)
    comments = db.Column('Comments', db.String(10000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateAssociation (resume_id=' %r')>" % self.resume_id


class CandidateAchievement(db.Model):
    __tablename__ = 'candidate_achievement'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column('Date', db.DateTime)
    issuing_authority = db.Column('IssuingAuthority', db.String(150))
    description = db.Column('Description', db.String(10000))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))

    def __repr__(self):
        return "<CandidateAchievement (resume_id=' %r')>" % self.resume_id


class CandidateMilitaryService(db.Model):
    __tablename__ = 'candidate_military_service'
    id = db.Column(db.BigInteger, primary_key=True)
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
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
        return "<CandidateMilitaryService (resume_id=' %r')>" % self.resume_id


class CandidatePatentHistory(db.Model):
    __tablename__ = 'candidate_patent_history'
    id = db.Column(db.BigInteger, primary_key=True)
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
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
    patent_status_id = db.Column('StatusId', db.Integer, db.ForeignKey('status.id'))
    issued_date = db.Column('IssuedDate', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<PatentMilestone (patent_status_id=' %r')>" % self.patent_status_id


class CandidatePublication(db.Model):
    __tablename__ = 'candidate_publication'
    id = db.Column(db.BigInteger, primary_key=True)
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(200))
    start_year = db.Column('StartYear', db.Year)    # todo: accpet Year format only or create a function to validate
    start_month = db.Column('StartMonth', db.Integer)
    end_year = db.Column('EndYear', db.Year)        # todo: accept Year format only or create a function to validate
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
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
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
        return "<CandidateAddress (resume_id=' %r')>" % self.resume_id


class CandidateEducation(db.Model):
    __tablename__ = 'candidate_education'
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
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
        return "<CandidateEducation (resume_id=' %r')>" % self.resume_id


class CandidateEducationDegree(db.Model):
    __tablename__ = 'candidate_education_degree'
    id = db.Column(db.BigInteger, primary_key=True)
    candidate_education_id = db.Column('CandidateEducationId', db.BigInteger, db.ForeignKey('candidate_education.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    degree_type = db.Column('DegreeType', db.String(100))
    degree_title = db.Column('DegreeTitle', db.String(100))
    start_year = db.Column('StartYear', db.Year)
    start_month = db.Column('StartMonth', db.SmallInteger)
    EndYear = db.Column('EndYear', db.Year)
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
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    organization = db.Column('Organization', db.String(150))
    position = db.Column('Position', db.String(150))
    city = db.Column('City', db.String(50))
    state = db.Column('State', db.String(50))
    end_month = db.Column('EndMonth', db.SmallInteger)
    start_year = db.Column('StartYear', db.Year)
    country_id = db.Column('CountryId', db.Integer, db.ForeignKey('country.id'))
    start_month = db.Column('StartMonth', db.SmallInteger)
    end_year = db.Column('EndYear', db.Year)
    is_current = db.Column('IsCurrent', db.Boolean, default=False)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidate_experience_bullets = relationship('CandidateExperienceBullet', backref='candidate_experience')

    def __repr__(self):
        return "<CandidateExperience (resume_id=' %r)>" % self.resume_id


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
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
    candidate_id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.SmallInteger)
    description = db.Column('Description', db.String(10000))
    added_time = db.Column('AddedTime', db.DateTime)
    totla_months = db.Column('TotalMonths', db.Integer)
    last_used = db.Column('LastUsed', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateSkill (resume_id=' %r')>" % self.resume_id


class CandidateUnidentified(db.Model):
    __tablename__ = 'candidate_unidentified'
    id = db.Column(db.BigInteger, primary_key=True)
    resume_id = db.Column('ResumeId', db.BigInteger, db.ForeignKey('resume.id'))
    candidate_Id = db.Column('CandidateId', db.Integer, db.ForeignKey('candidate.id'))
    title = db.Column('Title', db.String(100))
    description = db.Column('Description', db.Text)
    added_time = db.Column('AddedTime', db.DateTime)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<CandidateUnidentified (title=' %r')>" % self.title











































