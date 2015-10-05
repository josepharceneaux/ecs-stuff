from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Candidate(Base):
    __tablename__ = 'candidate'
    id = Column(Integer, primary_key=True)
    firstName = Column(String(50))
    middleName = Column(String(50))
    lastName = Column(String(50))
    formattedName = Column(String(150))
    statusId = Column(Integer, ForeignKey('candidate_status.id'))
    isWebHidden = Column(Integer)
    isMobileHidden = Column(Integer)
    addedTime = Column(DateTime)
    ownerUserId = Column(Integer, ForeignKey('user.id'))
    domainCanRead = Column(Integer)
    domainCanWrite = Column(Integer)
    diceSocialProfileId = Column(String(128))
    diceProfileId = Column(String(128))
    sourceId = Column(Integer, ForeignKey('candidate_source.id'))
    sourceProductId = Column(Integer, ForeignKey('product.id'), default=2, nullable=False)
    filename = Column(String(512))
    objective = Column(String(1000))
    summary = Column(String(1000))
    totalMonthsExperience = Column(Integer)
    resumeText = Column(String(1000))
    cultureId = Column(Integer, ForeignKey('culture.id'), default=1)

    def __repr__(self):
        return '<Candidate %r %r>' % self.firstName, self.lastName

    @classmethod
    def get_by_first_last_name_owner_user_id_source_id_product(cls, first_name,
                                                               last_name,
                                                               owner_user_id,
                                                               source_id,
                                                               product_id):
        assert owner_user_id is not None
        return cls.query.filter(
            and_(
                Candidate.firstName == first_name,
                Candidate.lastName == last_name,
                Candidate.ownerUserId == owner_user_id,
                Candidate.sourceId == source_id,
                Candidate.sourceProductId == product_id
            )
        ).first()


class CandidateStatus(Base):
    __tablename__ = 'candidate_status'
    id = Column(Integer, primary_key=True)
    description = Column(String(100))
    notes = Column(String(500))

    def __repr__(self):
        return '<CandidateStatus %r>' % self.description


class CandidateSource(Base):
    __tablename__ = 'candidate_source'
    id = Column(Integer, primary_key=True)
    description = Column(String(100))
    notes = Column(String(500))
    domainId = Column(Integer, ForeignKey('domain.id'))

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
