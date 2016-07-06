"""
Utility functions for the ATS service.
"""

__author__ = 'Joseph Arceneaux'

from ats_service.common.models.ats import db, ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile
from ats_service.common.models.candidate import Candidate
from ats_service.common.models.user import User
from ats_service.common.error_handling import *


ATS_ACCOUNT_FIELDS = ['ats_name', 'ats_homepage', 'ats_login', 'ats_auth_type', 'ats_id', 'ats_credentials']
ATS_CANDIDATE_FIELDS = ['ats_remote_id', 'profile_json']


def validate_ats_account_data(data):
    """
    Verify that POST data contains all required fields for dealing with an ATS account.

    :param data: dict, keys and their values
    :return: None, or throws an exception.
    """
    missing_fields = [field for field in ATS_ACCOUNT_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise MissingRequiredField('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))


def validate_ats_candidate_data(data):
    """
    Verify that POST data contains all required fields for dealing with an ATS candidate.

    :param data: dict, keys and their values
    :return: None, or throws an exception.
    """
    missing_fields = [field for field in ATS_CANDIDATE_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise MissingRequiredField('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))


def new_ats(data):
    """
    Register a new Applicant Tracking System.

    :param data: dict, keys and values describing the ATS.
    :rtype: ats object
    """
    ats = ATS(name=data['ats_name'], homepage_url=data['ats_homepage'], login_url=data['ats_login'], auth_type=data['ats_auth_type'])
    db.session.add(ats)
    db.session.commit()
    return ats


def new_ats_account(user_id, ats_id, data):
    """
    Register an ATS account for a user.

    :param user_id: int, id of the user to associate the account with.
    :param ats_id: int, id of the ATS system.
    :param data: dict, keys and values describing the account.
    :rtype object, an ATS account object.
    """
    # Create account and credential entries
    account = ATSAccount(active=True, ats_id=ats_id, user_id=user_id, ats_credential_id=0)
    db.session.add(account)
    credentials = ATSCredential(ats_account_id=0, auth_type=data['ats_auth_type'], credentials_json=data['ats_credentials'])
    db.session.add(credentials)
    db.session.commit()

    # Now make the two rows point to each other
    update_dict = { 'ats_credential_id': credentials.id }
    ATSAccount.query.filter(ATSAccount.id == account.id).update(update_dict)
    update_dict = { 'ats_account_id': account.id }
    ATSCredential.query.filter(ATSCredential.id == credentials.id).update(update_dict)
    update_dict = { 'ats_enabled': True }
    User.query.filter(User.id == user_id).update(update_dict)
    db.session.commit()

    return account


def delete_ats_account(user_id, ats_account_id):
    """
    Remove an ATS account and all of its candidates.

    :param ats_account_id: int, id of the ATS account.
    :rtype None
    """
    # First, verify the user and account
    account = ATSAccount.get_by_id(ats_account_id)
    if not account:
        raise MissingRequiredField('delete_ats_account: No such account {}'.format(ats_account_id))

    user = User.get_by_id(user_id)
    if not user:
        raise MissingRequiredField('delete_ats_account: No such user {}'.format(user_id))

    # Next remove all candidates and candidate attributes from the account
    candidate_list = ATSCandidate.query.filter(ATSCandidate.ats_account_id == ats_account_id).all()
    for candidate in candidate_list:
        profile = ATSCandidateProfile.get_by_id(candidate.profile_id)
        db.session.delete(profile)
        db.session.delete(candidate)

    # Then remove the account credentials
    credentials = ATSCredential.get_by_id(account.ats_credential_id)
    db.session.delete(credentials)

    # Remove the account
    db.session.delete(account)
    db.session.commit()

    # If this is the only ATS account for this user, mark the user as not ATS enabled
    all_accounts = ATSAccount.query.filter(ATSAccount.id == ats_account_id).all()
    if not all_accounts:
        update_dict = { 'ats_enabled': False }
        User.query.filter(User.id == user_id).update(update_dict)
        db.session.commit()


def new_ats_candidate(account, data):
    """
    Register an ATS candidate with an ATS account.

    :param account: object, an ATS account object.
    :param data: dict, keys and values describing the candidate.
    :rtype object, an ATS candidate object.
    """
    gt_candidate_id = data.get('gt_candidate_id', None)
    profile = ATSCandidateProfile(active=True, profile_json=data['profile_json'], ats_id=account.ats_id)
    db.session.add(profile)
    db.session.commit()
    candidate = ATSCandidate(ats_account_id=account.id, ats_remote_id=data['ats_remote_id'], gt_candidate_id=gt_candidate_id, profile_id=profile.id)
    db.session.add(candidate)
    db.session.commit()

    return candidate
 

def link_ats_candidate(candidate_id, ats_candidate_id):
    """
    Mark an ATS candidate as being the same as a getTalent candidate.

    :param candidate_id: int, id of the GT candidate.
    :param ats_candidate_id: int, id of the ATS candidate.
    :rtype None
    """
    gt_candidate = Candidate.get_by_id(candidate_id)
    if not gt_candidate:
        raise MissingRequiredField("getTalent candidate id {} not found".format(candidate_id))

    ats_candidate = ATSCandidate.get_by_id(ats_candidate_id)
    if not ats_candidate:
        raise MissingRequiredField("ATS candidate id {} not found.".format(ats_candidate_id))

    update_dict = { 'gt_candidate_id': candidate_id }
    ATSCandidate.query.filter(ATSCandidate.id == ats_candidate_id).update(update_dict)
    db.session.commit()


def unlink_ats_candidate(candidate_id, ats_candidate_id):
    """
    Remove the association of a GT candidate with an ATS candidate.

    :param candidate_id: int, id of the GT candidate.
    :param ats_candidate_id: int, id of the ATS candidate.
    :rtype None
    """
    gt_candidate = Candidate.get_by_id(candidate_id)
    if not gt_candidate:
        raise MissingRequiredField("Candidate id {} not found".format(candidate_id))

    ats_candidate = ATSCandidate.get_by_id(ats_candidate_id)
    if not ats_candidate:
        raise MissingRequiredField("ATS Candidate id {} not found".format(ats_candidate_id))

    update_dict = { 'gt_candidate_id': None }
    ATSCandidate.query.filter(ATSCandidate.id == ats_candidate_id).update(update_dict)
    db.session.commit()
