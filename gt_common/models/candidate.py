from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Candidate(Base):
    __tablename__ = 'candidate'
    id = Column('id', Integer, primary_key=True)
    first_name = Column('firstName', String(50))
    middle_name = Column('middleName', String(50))
    last_name = Column('lastName', String(50))
    formatted_name = Column('formattedName', String(150))
    status_id = Column('statusId', Integer, ForeignKey('candidate_status.id'))
    is_web_hidden = Column('isWebHidden', Integer)
    is_mobile_hidden = Column('isMobileHidden', Integer)
    added_time = Column('addedTime', DateTime)
    owner_user_id = Column('ownerUserId', Integer, ForeignKey('user.id'))
    domain_can_read = Column('domainCanRead', Integer)
    domain_can_write = Column('domainCanWrite', Integer)
    dice_social_profile_id = Column('diceSocialProfileId', String(128))
    dice_profile_id = Column('diceProfileId', String(128))
    source_id = Column('sourceId', Integer, ForeignKey('candidate_source.id'))
    source_product_id = Column('sourceProductId', Integer, ForeignKey('product.id'), default=2, nullable=False)
    filename = Column('filename', String(512))
    objective = Column('objective', String(1000))
    summary = Column('summary', String(1000))
    total_months_experience = Column('totalMonthsExperience', Integer)
    resume_text = Column('resumeText', String(1000))
    culture_id = Column('cultureId', Integer, ForeignKey('culture.id'), default=1)

    def __repr__(self):
        return '<Candidate %r %r>' % self.first_name, self.last_name

    @classmethod
    def get_by_first_last_name_owner_user_id_source_id_product(cls, first_name,
                                                               last_name,
                                                               owner_user_id,
                                                               source_id,
                                                               product_id):
        assert owner_user_id is not None
        return cls.query.filter(
            and_(
                Candidate.first_name == first_name,
                Candidate.last_name == last_name,
                Candidate.owner_user_id == owner_user_id,
                Candidate.source_id == source_id,
                Candidate.source_product_id == product_id
            )
        ).first()


class CandidateStatus(Base):
    __tablename__ = 'candidate_status'
    id = Column('id', Integer, primary_key=True)
    description = Column('description', String(100))
    notes = Column('notes', String(500))

    def __repr__(self):
        return '<CandidateStatus %r>' % self.description


class CandidateSource(Base):
    __tablename__ = 'candidate_source'
    id = Column('id', Integer, primary_key=True)
    description = Column('description', String(100))
    notes = Column('notes', String(500))
    domain_id = Column('domainId', Integer, ForeignKey('domain.id'))

    def __repr__(self):
        return '<CandidateSource %r>' % self.description

    @classmethod
    def get_by_description_and_notes(cls, event_name, event_description):
        assert event_name is not None
        return cls.query.filter(
            and_(
                CandidateSource.description == event_name,
                CandidateSource.notes == event_description,
            )
        ).first()
