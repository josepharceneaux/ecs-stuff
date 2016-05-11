import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, BIGINT
from db import db
from ..models.candidate import Candidate


class Tag(db.Model):
    __tablename__ = 'tag'
    id = Column(INTEGER, primary_key=True)
    name = Column(VARCHAR(12), nullable=False, unique=True)
    added_datetime = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_datetime = db.Column(TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<Tag (id = {})>".format(self.id)

    @classmethod
    def get_by_name(cls, name):
        """
        :type name:  str
        :rtype:  Tag
        """
        return cls.query.filter_by(name=name).first()


class CandidateTag(db.Model):
    __tablename__ = 'candidate_tag'
    tag_id = Column(INTEGER, ForeignKey('tag.id'), primary_key=True)
    candidate_id = Column(BIGINT, ForeignKey('candidate.Id'), primary_key=True)
    added_datetime = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_datetime = db.Column(TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<CandidateTag (candidate_id = {})>".format(self.candidate_id)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by(cls, **filters):
        """
        Function will return the first matching object filtered by keywords
        :param filters: keywords, e.g. (candidate_id=1, tag_id=2)
        :rtype:  CandidateTag
        """
        return cls.query.filter_by(**filters).first()

    @classmethod
    def get_all(cls, candidate_id):
        """
        Function will return a list of CandidateTag for specified candidate
        :type candidate_id:  int | long
        :rtype: list[CandidateTag]
        """
        return cls.query.filter_by(candidate_id=candidate_id).all()

    @classmethod
    def get_one(cls, candidate_id, tag_id):
        """
        Function will get a single CandidateTag
        :type candidate_id:  int | long
        :type tag_id:        int |long
        :rtype:  CandidateTag
        """
        return cls.query.filter_by(candidate_id=candidate_id, tag_id=tag_id).first()
