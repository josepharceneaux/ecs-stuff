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
        return "<ATS ( = %r)>" % self.name

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
        return cls.query.filter_by(id=ats_id).first()

    @classmethod
    def get_by_name(cls, ats_name):
        """
        """
        assert isinstance(ats_name, basestring), 'ATS Name should be a string'
        return cls.query.filter_by(name=ats_name).first()

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


class ATSAccount(db.Model):
    """
    """
    __tablename__ = 'ats_account'
    id = db.Column(db.BigInteger, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    ats_id = db.Column(db.BigInteger)
    user_id = db.Column(db.BigInteger)
    ats_credential_id = db.Column(db.BigInteger)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    @classmethod
    def get_account(cls, user_id, ats_name):
        """
        """
        accounts = cls.query.filter_by(user_id=user_id).all()
        if accounts:
            for a in accounts:
                ats = ATS.get_by_id(a.ats_id)
                if ats and ats.name == ats_name:
                    return ats

    def __repr__(self):
        return "<ATS Credential ( = %r)>" % self.id

class ATSCredential(db.Model):
    """
    """
    __tablename__ = 'ats_credential'
    id = db.Column(db.BigInteger, primary_key=True)
    ats_account_id = db.Column(db.BigInteger)
    auth_type = db.Column(db.String(45))
    credentials_json = db.Column(db.Text)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ATS Credential ( = %r)>" % self.credentials_json


class ATSCandidate(db.Model):
    """
    """
    __tablename__ = 'ats_candidate'
    id = db.Column(db.BigInteger, primary_key=True)
    ats_remote_id = db.Column(db.String(100))
    gt_candidate_id = db.Column(db.BigInteger)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ATS Candidate ( = %r)>" % self.ats_remote_id


class ATSCandidateProfile(db.Model):
    """
    """
    __tablename__ = 'ats_candidate_profile'
    id = db.Column(db.BigInteger, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    profile_json = db.Column(db.Text)
    ats_id  = db.Column(db.BigInteger)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ATS Candidate Profile ( = %r)>" % self.profile_json
