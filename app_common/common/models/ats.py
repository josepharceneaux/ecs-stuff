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
        assert isinstance(ats_id, (int, long)) and ats_id > 0, 'ATS Id should be a valid positive number'
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

    def to_dict(self):
        """
        """
        return { 'active' : self.active, 'ats_id' : self.ats_id, 'user_id' : self.user_id, 'ats_credential_id' : self.ats_credential_id }

    @classmethod
    def get_by_id(cls, account_id):
        """
        """
        assert isinstance(account_id, (int, long)) and account_id > 0, 'Account Id should be a valid positive number'
        return cls.query.filter_by(id=account_id).first()

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

    @classmethod
    def get_accounts_for_user(cls, user_id):
        """
        """
        accounts = cls.query.filter(ATSAccount.user_id == user_id)
        return accounts

    @classmethod
    def get_accounts_for_user_as_json(cls, user_id):
        """
        """
        return_json = []
        accounts = ATSAccount.get_accounts_for_user(user_id)
        for a in accounts:
            credentials = ATSCredential.get_by_id(a.ats_credential_id)
            item = a.to_dict()
            ats = ATS.get_by_id(a.ats_id)
            item.update(ats.to_dict())
            item.update({ 'credentials': credentials.credentials_json})
            return_json.append( { a.id : item })

        return json.dumps(return_json)

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

    @classmethod
    def get_by_id(cls, credentials_id):
        """
        """
        assert isinstance(credentials_id, (int, long)) and credentials_id > 0, 'ATS Id {} should be a valid positive number'.format(credentials_id)
        return cls.query.filter_by(id=credentials_id).first()

    def __repr__(self):
        return "<ATS Credential ( = %r)>" % self.credentials_json


class ATSCandidate(db.Model):
    """
    """
    __tablename__ = 'ats_candidate'
    id = db.Column(db.BigInteger, primary_key=True)
    ats_account_id = db.Column(db.BigInteger)
    ats_remote_id = db.Column(db.String(100))
    gt_candidate_id = db.Column(db.BigInteger)
    profile_id = db.Column(db.BigInteger)
    added_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)

    def to_dict(self):
        """
        """
        return { 'id' : self.id, 'ats_account_id' : self.ats_account_id, 'ats_remote_id' : self.ats_remote_id, 'gt_candidate_id' : self.gt_candidate_id }

    @classmethod
    def get_all(cls, account_id):
        """
        """
        return cls.query.filter_by(ats_account_id=account_id).all()

    @classmethod
    def get_all_as_json(cls, account_id):
        """
        """
        candidates = ATSCandidate.get_all(account_id)
        if not candidates:
            return

        return_json = []
        for c in candidates:
            item = c.to_dict()
            profile = ATSCandidateProfile.get_by_id(c.profile_id)
            item.update(profile.to_dict())
            return_json.append( { c.id : item } )

        return json.dumps(return_json)

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

    def to_dict(self):
        """
        """
        return { 'active' : self.active, 'profile_json' : self.profile_json }

    @classmethod
    def get_by_id(cls, profile_id):
        """
        """
        assert isinstance(profile_id, (int, long)) and profile_id > 0, 'Candidate profile id should be a valid positive number'
        return cls.query.filter_by(id=profile_id).first()

    def __repr__(self):
        return "<ATS Candidate Profile ( = %r)>" % self.profile_json
