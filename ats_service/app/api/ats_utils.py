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

    :param dict data: keys and their values
    :rtype: None
    """
    missing_fields = [field for field in ATS_ACCOUNT_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise InvalidUsage('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))


def invalid_account_fields_check(data):
    """
    Verify that data contains only valid ATS account fields.

    :param dict data: keys and their values
    :rtype: None
    """
    field_names = data.keys()
    invalid_fields = [name for name in field_names if name not in ATS_ACCOUNT_FIELDS]
    if invalid_fields:
        raise UnprocessableEntity("Invalid data", additional_error_info=dict(missing_fields=invalid_fields))


def validate_ats_candidate_data(data):
    """
    Verify that POST data contains all required fields for dealing with an ATS candidate.

    :param dict data: keys and their values
    :return: None, or throws an exception.
    """
    missing_fields = [field for field in ATS_CANDIDATE_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise InvalidUsage('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))


def new_ats(data):
    """
    Register a new Applicant Tracking System.

    :param dict data: keys and values describing the ATS.
    :rtype: ATS
    """
    ats = ATS(name=data['ats_name'], homepage_url=data['ats_homepage'], login_url=data['ats_login'], auth_type=data['ats_auth_type'])
    ats.save()
    return ats


def new_ats_account(user_id, ats_id, data):
    """
    Register an ATS account for a user.

    :param int user_id: id of the user to associate the account with.
    :param int ats_id: id of the ATS system.
    :param dict data: keys and values describing the account.
    :rtype: ATS
    """
    # Create account and credential entries
    account = ATSAccount(active=True, ats_id=ats_id, user_id=user_id, ats_credential_id=0)
    account.save()
    credentials = ATSCredential(ats_account_id=0, auth_type=data['ats_auth_type'], credentials_json=data['ats_credentials'])
    credentials.save()

    # Now make the two rows point to each other
    update_dict = {'ats_credential_id': credentials.id}
    account.update(**update_dict)
    update_dict = {'ats_account_id': account.id}
    credentials.update(**update_dict)
    update_dict = {'ats_enabled': True}
    User.get(user_id).update(**update_dict)

    return account


def update_ats_account(account_id, new_data):
    """
    Update the values of an ATS account.

    :param int account_id: primary key of the account.
    :param dict new_data: New values for the account.
    :rtype: None
    """
    # Search for the account, complain if it doesn't exist
    account = ATSAccount.get(account_id)
    if not account:
        raise UnprocessableEntity("Invalid ats account id", additional_error_info=dict(id=account_id))
    ats = ATS.get(account.ats_id)
    if not ats:
        raise UnprocessableEntity("Invalid ats id", additional_error_info=dict(id=account.ats_id))

    # Update the ATS info
    update_dict = {}
    if 'ats_name' in new_data:
        update_dict['name'] = new_data['ats_name']
    if 'ats_homepage' in new_data:
        update_dict['homepage_url'] = new_data['ats_homepage']
    if 'ats_login' in new_data:
        update_dict['login_url'] = new_data['ats_login']
    if 'ats_auth_type' in new_data:
        update_dict['auth_type'] = new_data['ats_auth_type']
    if len(update_dict) > 0:
        ats.update(**update_dict)

    update_dict = {}
    if 'active' in new_data:
        if new_data['active'] == "False":
            update_dict['active'] = False
        else:
            update_dict['active'] = True

        account.update(**update_dict)

    # If they're changing credentials, find those. Presumably auth_type won't change.
    if 'ats_credentials' in new_data:
        credentials = ATSCredential.get(account.ats_credential_id)
        update_dict = {'credentials_json' : new_data['ats_credentials']}
        credentials.update(**update_dict)


def delete_ats_account(user_id, ats_account_id):
    """
    Remove an ATS account and all of its candidates.

    :param int ats_account_id: id of the ATS account.
    :rtype: None
    """
    # First, verify the user and account
    account = ATSAccount.get(ats_account_id)
    if not account:
        raise NotFoundError('delete_ats_account: No such account {}'.format(ats_account_id))

    user = User.get(user_id)
    if not user:
        raise NotFoundError('delete_ats_account: No such user {}'.format(user_id))

    # Next remove all candidates and candidate attributes from the account
    candidate_list = ATSCandidate.query.filter(ATSCandidate.ats_account_id == ats_account_id).all()
    for candidate in candidate_list:
        profile = ATSCandidateProfile.get(candidate.profile_id)
        ATSCandidateProfile.delete(profile)

    # Then remove the account credentials
    credentials = ATSCredential.get(account.ats_credential_id)
    ATSCredential.delete(credentials)

    # Remove the account
    ATSAccount.delete(account)

    # If this is the only ATS account for this user, mark the user as not ATS enabled
    all_accounts = ATSAccount.query.filter(ATSAccount.user_id == user_id).all()
    if not all_accounts:
        update_dict = {'ats_enabled': False}
        User.query.filter(User.id == user_id).update(update_dict)
        db.session.commit()


def new_ats_candidate(account, data):
    """
    Register an ATS candidate with an ATS account.

    :param obj account: an ATS account object.
    :param dict data: keys and values describing the candidate.
    :rtype: ATSCandidate
    """
    gt_candidate_id = data.get('gt_candidate_id', None)
    profile = ATSCandidateProfile(active=True, profile_json=data['profile_json'], ats_id=account.ats_id)
    profile.save()
    candidate = ATSCandidate(ats_account_id=account.id, ats_remote_id=data['ats_remote_id'], gt_candidate_id=gt_candidate_id, profile_id=profile.id)
    candidate.save()

    return candidate
 

def delete_ats_candidate(candidate_id):
    """
    Remove an ATS candidate from the database.

    :param int candidate_id: The id of the candidate.
    :rtype: None
    """
    candidate = ATSCandidate.get(candidate_id)
    if not candidate:
        raise InvalidUsage('delete_ats_candidate: No such candidate {}'.format(candidate_id))

    profile = ATSCandidateProfile.get(candidate.profile_id)
    if profile:
        ATSCandidateProfile.delete(profile)

    Candidate.delete(profile)


def update_ats_candidate(account_id, candidate_id, new_data):
    """
    Update the profile of an ATS candidate.

    :param int account_id: primary key of the account the candidate belongs to.
    :param int candidate_id: primary key of the candidate.
    :param dict new_data: values to update for the candidate.
    :rtype: None
    """
    if 'profile_json' not in new_data:
        raise InvalidUsage("profile_json not found.")

    # Validate ATS Account
    account = ATSAccount.get(account_id)
    if not account:
        raise InvalidUsage("ATS account {} not found.".format(account_id))

    # Validate candidate id
    candidate = ATSCandidate.get(candidate_id)
    if not candidate:
        raise UnprocessableEntity("Invalid candidate id", additional_error_info=dict(id=account.candidate_id))

    # Validate profile id
    profile = ATSCandidateProfile.get(candidate.profile_id)
    if not profile:
        raise UnprocessableEntity("Invalid candidate profile id", additional_error_info=dict(id=candidate.profile_id))

    update_dict = {'profile_json' : new_data['profile_json']}
    profile.update(**update_dict)
    return candidate


def link_ats_candidate(gt_candidate_id, ats_candidate_id):
    """
    Mark an ATS candidate as being the same as a getTalent candidate.

    :param int gt_candidate_id: id of the GT candidate.
    :param int ats_candidate_id: id of the ATS candidate.
    :rtype: None
    """
    gt_candidate = Candidate.get(gt_candidate_id)
    if not gt_candidate:
        raise InvalidUsage("getTalent candidate id {} not found".format(gt_candidate_id))

    ats_candidate = ATSCandidate.get(ats_candidate_id)
    if not ats_candidate:
        raise InvalidUsage("ATS candidate id {} not found.".format(ats_candidate_id))

    update_dict = {'gt_candidate_id': gt_candidate_id}
    ats_candidate.update(**update_dict)


def unlink_ats_candidate(gt_candidate_id, ats_candidate_id):
    """
    Remove the association of a GT candidate with an ATS candidate.

    :param int gt_candidate_id: id of the GT candidate.
    :param int ats_candidate_id: id of the ATS candidate.
    :rtype: None
    """
    gt_candidate = Candidate.get(gt_candidate_id)
    if not gt_candidate:
        raise InvalidUsage("Candidate id {} not found".format(gt_candidate_id))

    ats_candidate = ATSCandidate.get(ats_candidate_id)
    if not ats_candidate:
        raise InvalidUsage("ATS Candidate id {} not found".format(ats_candidate_id))

    update_dict = {'gt_candidate_id': None}
    ats_candidate.update(**update_dict)
