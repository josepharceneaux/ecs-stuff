"""
Database classes for ATS service.
"""

__author__ = 'Joseph Arceneaux'

import datetime
import json

from db import db


class ATS(db.Model):
    """
    Class representing table holding list of ATS we have integrated with.
    """
    __tablename__ = 'ats'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255))
    homepage_url = db.Column(db.String(255))
    login_url = db.Column(db.String(255))
    auth_type = db.Column(db.String(45))
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ATS ( = %r)>" % self.body_text

    def to_dict(self):
        """
        """
        return { 'name' : self.name, 'homepage_url' : self.homepage_url, 'login_url' : self.login_url, 'auth_type' : self.auth_type }

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
        assert isinstance(ats_name, basestring), 'ATS Name should be a string'
        return cls.query.filter_by(name=ats_name).all()

    @classmethod
    def get_all(cls):
        """
        """
        ats_list = []
        found = cls.query.all()
        if len(found) > 0:
            for element in found:
                ats_list.append(element)

        return ats_list

    @classmethod
    def get_all_as_json(cls):
        """
        """
        return_json = []
        ats_list = ATS.get_all()
        for ats in ats_list:
            item = ats.to_dict()
            return_json.append(item)

        return json.dumps(return_json)
