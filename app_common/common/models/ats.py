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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    homepage_url = db.Column(db.String(255))
    login_url = db.Column(db.String(255))
    auth_type = db.Column(db.String(45))
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ATS (name = %r)>" % self.name

    def to_dict(self):
        """
        Return a dict representation of this object.
        :rtype: dict
        """
        return { 'name' : self.name, 'homepage_url' : self.homepage_url,
                 'login_url' : self.login_url, 'auth_type' : self.auth_type }

    @classmethod
    def get_by_name(cls, ats_name):
        """
        Find and return this object by its name field.
        :param str ats_name: name of the object.
        :rtype: ATS
        """
        assert isinstance(ats_name, basestring), 'ATS Name should be a string'
        return cls.query.filter_by(name=ats_name).first()

    @classmethod
    def get_all_as_json(cls):
        """
        Retrieve all ATS entries and return as JSON.
        :rtype: str
        """
        return_json = [ats.to_dict() for ats in ATS.query.all()]

        return json.dumps(return_json)


class ATSAccount(db.Model):
    """
    An ATS account belonging to a GT user.
    """
    __tablename__ = 'ats_account'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    ats_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    ats_credential_id = db.Column(db.Integer)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def to_dict(self):
        """
        Return a dict representation of this object.
        :rtype: dict
        """
        return { 'active' : self.active, 'ats_id' : self.ats_id, 'user_id' : self.user_id,
                 'ats_credential_id' : self.ats_credential_id }

    @classmethod
    def get_account(cls, user_id, ats_name):
        """
        Retrieve a specific ATS account of a user.
        :param int user_id: id of the GT user.
        :param str ats_name: name of the ATS.
        :rtype: ATSAccount
        """
        accounts = cls.query.filter_by(user_id=user_id).all()
        for a in accounts:
            ats = ATS.get(a.ats_id)
            if ats and ats.name == ats_name:
                return ats

    def __repr__(self):
        return "<ATS Credential ( = %r)>" % self.id


class ATSCredential(db.Model):
    """
    Credentials used to access an ATS account.
    """
    __tablename__ = 'ats_credential'
    id = db.Column(db.Integer, primary_key=True)
    ats_account_id = db.Column(db.Integer)
    auth_type = db.Column(db.String(45))
    credentials_json = db.Column(db.Text)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<ATS Credential ( = %r)>" % self.credentials_json


class ATSCandidate(db.Model):
    """
    A candidate from an ATS. May or may not be linked to a GT candidate.
    """
    __tablename__ = 'ats_candidate'
    id = db.Column(db.Integer, primary_key=True)
    # ID in ATS table
    ats_account_id = db.Column(db.Integer)
    # Candidate ID in the remote ATS
    ats_remote_id = db.Column(db.String(100))
    # getTalent candidate ID, if linked
    gt_candidate_id = db.Column(db.Integer)
    # ID into the ATSCandidateProfile table
    profile_id = db.Column(db.Integer)
    # ID into an ATS-specific table
    ats_table_id = db.Column(db.Integer)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def to_dict(self):
        """
        Return a dict representation of this object.
        :rtype: dict
        """
        return { 'id' : self.id, 'ats_account_id' : self.ats_account_id,
                 'ats_remote_id' : self.ats_remote_id, 'gt_candidate_id' : self.gt_candidate_id }

    @classmethod
    def get_all(cls, account_id):
        """
        Return all ATS candidates associated with this account.

        :param int account_id: primary key of the account.
        :rtype list: list of candidates.
        """
        return cls.query.filter_by(ats_account_id=account_id).all()

    @classmethod
    def get_all_as_json(cls, account_id):
        """
        Return all ATS candidates associated with this account as JSON.

        :param int account_id: primary key of the account.
        :rtype str: JSON list of candidates.
        """
        candidates = ATSCandidate.get_all(account_id)
        if not candidates:
            return

        return_json = []
        for c in candidates:
            item = c.to_dict()
            profile = ATSCandidateProfile.get(c.profile_id)
            item.update(profile.to_dict())
            return_json.append({c.id : item})

        return json.dumps(return_json)

    @classmethod
    def get_by_ats_id(cls, account_id, ats_id):
        """
        Retrive a candidate by ATS account and remote ATS id.

        :param int account_id: primary key of the account.
        :param int ats_id: Id of the candidate in the remote ATS.
        :rtype list: A candidate.
        """
        # TODO Test this.
        return cls.query.filter(cls.ats_account_id==account_id, cls.ats_remote_id==ats_id).first()

    def __repr__(self):
        return "<ATS Candidate (id = %r)>" % self.ats_remote_id


class ATSCandidateProfile(db.Model):
    """
    Attributes of an ATS candidate.
    """
    __tablename__ = 'ats_candidate_profile'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    profile_json = db.Column(db.Text)
    ats_id  = db.Column(db.Integer)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def to_dict(self):
        """
        Return a dict representation of this object.
        :rtype: dict
        """
        return { 'active' : self.active, 'profile_json' : self.profile_json }

    def __repr__(self):
        return "<ATS Candidate Profile (profile = %r)>" % self.profile_json
