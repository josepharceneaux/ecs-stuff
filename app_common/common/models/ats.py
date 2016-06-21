"""
Database classes for ATS service.
"""

__author__ = 'Joseph Arceneaux'

import datetime
from db import db


class ATS(db.Model):
    """
    Class representing table holding list of ATS we have integrated with.
    """
    __tablename__ = 'ats'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    homepage_url = db.Column(db.String(255))
    login_url = db.Column(db.String(255))
    auth_type = db.Column(db.String(45))
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP)

    def __repr__(self):
        return "<ATS ( = %r)>" % self.body_text

    @classmethod
    def get_by_id(cls, ats_id):
        """
        """
        assert isinstance(ats_id, (int, long)) and ats_id > 0, \
            'ATS Id should be a valid positive number'
        return cls.query.filter_by(id=_id).all()

    @classmethod
    def get_by_name(cls, ats_name):
        """
        """
        assert isinstance(ats_id, basestring) 'ATS Name should be a string'
        return cls.query.filter_by(name=ats_name).all()

    @classmethod
    def get_all(cls):
        """
        """
        found = cls.query.all()
        if len(found) > 0:
            ats_list = []
            for element in found:
                ats_list.append(element.name)
