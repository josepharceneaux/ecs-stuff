from models import db
from sqlalchemy.orm import relationship
import datetime


#TODO: set length for integer inputs for domain_can_read & is_web_hidden, etc.
class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    formatted_name = db.Column(db.String(150))
    status_id = db.Column(db.Integer, db.ForeignKey('candidate_status.id'))
    is_web_hidden = db.Column(db.Integer, default=0)
    is_mobile_hidden = db.Column(db.Integer, default=0)
    added_time = db.Column(db.DateTime, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    domain_can_read = db.Column(db.Integer, default=1)
    domain_can_write = db.Column(db.Integer, default=0)
    dice_social_profile_id = db.Column(db.String(128))
    dice_profile_id = db.Column(db.String(128))
    source_id = db.Column(db.Integer, db.ForeignKey('candidate_source.id'))
    source_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, default=2) # Web = 2
    filename = db.Column(db.String(100))
    objective = db.Column(db.Text)
    summary = db.Column(db.Text)
    total_months_experience = db.Column(db.Integer)
    resume_text = db.Column(db.Text)
    culture_id = db.Column(db.Integer, db.ForeignKey('culture.id'), default=1)

    def __repr__(self):
        return "<Candidate(formatted_name=' %r')>" % (self.formatted_name)


class CandidateStatus(db.Model):
    __tablename = 'candidate_status'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100))
    notes = db.Column(db.String(500))

    candidate = relationship('Candidate')

    def __repr__(self):
        return "<CandidateStatus(description=' %r')>" % (self.description)


class PhoneLabel(db.Model):
    __tablename__ = 'phone_label'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(20))

    def __repr__(self):
        return "<PhoneLabel (description=' %r')>" % (self.description)


class CandidateSource(db.Model):
    __tablename__ = 'candidate_source'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100))
    notes = db.Column(db.String(500))
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))

    candidate = relationship('Candidate')

    def __repr__(self):
        return "<CandidateSource (description= '%r')>" % (self.description)


class PublicCandidateSharing(db.Model):
    __tablename__ = 'public_candidate_sharing'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.String(500))
    title = db.Column(db.String(100))
    candidate_id_list = db.Column(db.Text, nullable=False)
    hash_key = db.Column(db.String(50))


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
    description = db.Column(db.String(50))

    def __repr__(self):
        return "<EmailLabel (description=' %r')>" % (self.description)


class CandidateEmail(db.Model):
    __tablename__ = 'candidate_email'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    email_label_id = db.Column(db.Integer, db.ForeignKey('email_label.id')) # 1 = Primary
    address = db.Column(db.String(100))
    is_default = db.Column(db.Boolean)


class CandidatePhoto(db.Model):
    __tablename__ = 'candidate_photo'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    filename = db.Column(db.String(260))
    is_default = db.Column(db.Boolean)

    def __repr__(self):
        return "<CandidatePhoto (filename=' %r')>" % self.filename


class RatingTag(db.Model):
    __tablename__ = 'rating_tag'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100))

    def __repr__(self):
        return "<RatingTag (desctiption=' %r')>" % self.description


class CandidateRating(db.Model):
    __tablename__ = 'candidate_rating'
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), primary_key=True) #TODO: cannot have 2 primary keys
    rating_tag_id = db.Column(db.Integer, db.ForeignKey('rating_tag.id'), primary_key=True)
    value = db.Column(db.Integer, default=0) #TODO: length must be 2
    added_time = db.Column(db.DateTime)


class RatingTagUser(db.Model):
    __tabelname__ = 'rating_tag_user'
    rating_tag_id = db.Column(db.Integer, db.ForeignKey('rating_tag.id'))      #TODO: cannot have 2 primary keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class CandidateTextComment(db.Model):
    __tablename__ = 'candidate_text_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column(db.Integer) #TODO: integer length must be 2
    comment = db.Column(db.Text)
    added_time = db.Column(db.DateTime, default=datetime.datetime.now())


class VoiceComment(db.Model):
    __tablename__ = 'voice_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column(db.Integer) #TODO: integer length must be 2
    filename = db.Column(db.String(260))
    added_time = db.Column(db.DateTime, default=datetime.datetime.now())


class CandidateDocument(db.Model):
    __tablename__ = 'candidate_document'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    filename = db.Column(db.String(260))
    added_time = db.Column(db.DateTime, default=datetime.datetime.now())


class SocialNetwork(db.Model):  #TODO: updated time, see table in talent_staging
    __tablename__ = 'social_network'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255))
    api_url = db.Column(db.String(255))
    client_key = db.Column(db.String(500))
    secret_key = db.Column(db.String(500))
    redirect_uri = db.Column(db.String(255))
    auth_url = db.Column(db.String(200))

    def __repr__(self):
        return "<SocialNetwork (url=' %r')>" % self.url


class CandidateSocialNetwork(db.Model):
    __tablename__ = 'candidate_social_network'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    social_network_id = db.Column(db.Integer, db.ForeignKey('social_network.id'), nullable=False)
    social_profile_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return "<CandidateSocialNetwork (social_profile_url=' %r')>" % self.social_profile_url


class CandidateWorkExperience(db.Model):
    __tablename__ = 'candidate_work_experience'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    relocate = db.Column(db.Boolean, default=False)
    authorization = db.Column(db.String(250))
    telecommute = db.Column(db.Boolean, default=False)
    travel_percentage = db.Column(db.Integer, default=0)
    hourly_rate = db.Column(db.Float, default=0.0)
    salary = db.Column(db.Float, default=0.0)
    tax_terms = db.Column(db.String(255))
    security_clearance = db.Column(db.Boolean, default=False)
    third_party = db.Column(db.Boolean, default=False)


class CandidatePreferredLocation(db.Model):
    __tablename__ = 'candidate_preferred_location'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    address = db.Column(db.String(255))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    city = db.Column(db.String(255))
    region = db.Column(db.String(255))
    zipcode = db.Column(db.String(10))






















