"""
Utilities for ATS tests.
"""

from requests import codes
from contracts import contract

from ats_service.common.error_handling import MissingRequiredField
from ats_service.common.utils.test_utils import send_request
from ats_service.common.routes import ATSServiceApi, ATSServiceApiUrl
from ats_service.common.models.ats import db, ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile


def missing_field_test(data, key, token):
    """
    This function sends a POST request to the ATS account api with data which has one required field
    missing and checks that it MissingRequiredField 400
    :param dict data: ATS data
    :param string key: field key
    :param string token: auth token
    """
    del data[key]
    response = send_request('post', ATSServiceApiUrl.ACCOUNTS, token, data)
    assert response.status_code == codes.BAD_REQUEST
    response = response.json()
    error = response['error']
    assert error['missing_fields'] == [key]

def empty_database():
    """
    Empty all ATS-related data from the DB
    """
    ats_list = ATS.query.all()
    for ats in ats_list:
        db.session.delete(ats)

    account_list = ATSAccount.query.all()
    for account in account_list:
        db.session.delete(account)

    credentials_list = ATSCredential.query.all()
    for creds in credentials_list:
        db.session.delete(creds)

    candidate_list = ATSCandidate.query.all()
    for candidate in candidate_list:
        db.session.delete(candidate)

    profile_list = ATSCandidateProfile.query.all()
    for profile in profile_list:
        db.session.delete(profile)

    db.session.commit()
