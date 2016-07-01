"""
"""


from ats_service.common.models.ats import db, ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile
from ats_service.common.models.user import User
from ats_service.common.error_handling import *

from ats_service.common.error_handling import InternalServerError, ResourceNotFound, ForbiddenError, InvalidUsage


ATS_ACCOUNT_FIELDS = ['ats_name', 'ats_homepage', 'ats_login', 'ats_auth_type', 'ats_id', 'ats_credentials']
ATS_CANDIDATE_FIELDS = ['ats_remote_id', 'profile_json']


def validate_ats_account_data(data):
    """
    """
    missing_fields = [field for field in ATS_ACCOUNT_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise MissingRequiredField('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))

def validate_ats_candidate_data(data):
    """
    """
    missing_fields = [field for field in ATS_CANDIDATE_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise MissingRequiredField('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))

def new_ats(data):
    """
    """
    ats = ATS(name=data['ats_name'], homepage_url=data['ats_homepage'], login_url=data['ats_login'], auth_type=data['ats_auth_type'])
    db.session.add(ats)
    db.session.commit()
    return ats

def new_ats_account(user_id, ats_id, data):
    """
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

def new_ats_candidate(account, data):
    """
    """
    gt_candidate_id = data.get('gt_candidate_id', None)
    profile = ATSCandidateProfile(active=True, profile_json=data['profile_json'], ats_id=account.ats_id)
    db.session.add(profile)
    db.session.commit()
    candidate = ATSCandidate(ats_account_id=account.id, ats_remote_id=data['ats_remote_id'], gt_candidate_id=gt_candidate_id, profile_id=profile.id)
    db.session.add(candidate)
    db.session.commit()

    return candidate
