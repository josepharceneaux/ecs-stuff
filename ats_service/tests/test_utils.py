"""
Utilities for ATS tests.
"""

import json

from requests import codes
from contracts import contract

from ats_service.common.error_handling import InvalidUsage
from ats_service.common.utils.test_utils import send_request
from ats_service.common.routes import ATSServiceApi, ATSServiceApiUrl
from ats_service.common.models.ats import db, ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile

# Database
from ats_service.common.models.candidate import db, Candidate

def missing_field_test(data, key, token):
    """
    This function sends a POST request to the ATS account api with data which has one required field
    missing and checks that it raises InvalidUsage 400
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

def create_and_validate_account(token, post_data):
    """
    Create an account and validate that all entries have been correctly made.

    :param str token: authentication token
    :param str post_data: JSON string of account values
    """
    response = send_request('post', ATSServiceApiUrl.ACCOUNTS, token, post_data)
    assert response.status_code == codes.CREATED
    account_id = response.headers['location'].split('/')[-1]
    response = send_request('get', ATSServiceApiUrl.ACCOUNT % account_id, token, {}, verify=False)
    assert response.status_code == codes.OK
    values = json.loads(json.loads(response.text))
    assert values['credentials'] == post_data['ats_credentials']
    response = send_request('get', ATSServiceApiUrl.ATS, token, {}, verify=False)
    assert response.status_code == codes.OK
    values = json.loads(json.loads(response.text))
    assert len(values) == 1
    assert values[0]['login_url'] == post_data['ats_login']
    return account_id

def verify_nonexistant_account(token, account_id):
    """
    Verify that an account does not exist.

    :param str token: authentication token
    :param int account_id: primary key of the account
    """
    response = send_request('get', ATSServiceApiUrl.ACCOUNT % account_id, token, {}, verify=False)
    assert response.status_code == codes.NOT_FOUND

def create_and_validate_candidate(token, account_id, post_data):
    """
    Create a candidate and validate that all entries have been correctly made.

    :param str token: authentication token
    :param int account_id: primary key of the account
    :param str post_data: JSON string of candidate values
    """
    # Grab a candidate field value to test
    profile_dict = json.loads(post_data['profile_json'])
    # Create an ATS account for the candidate to belong to
    response = send_request('post', ATSServiceApiUrl.CANDIDATES % account_id, token, post_data)
    assert response.status_code == codes.CREATED
    values = json.loads(response.text)
    candidate_id = values['id']
    # Now fetch all the candidates from the account
    response = send_request('get', ATSServiceApiUrl.CANDIDATES % account_id, token, {}, verify=False)
    assert response.status_code == codes.OK
    values = json.loads(json.loads(response.text))
    assert len(values) == 1
    # Extract the returned field
    key = values[0].keys()[0]
    profile = json.loads(values[0][key]['profile_json'])
    assert profile['some'] == profile_dict.values()[0]
    return candidate_id

def verify_nonexistant_candidate(token, account_id, candidate_id):
    """
    Verify that a candidate does not exist.

    :param str token: authentication token
    :param int account_id: primary key of the account
    :param int candidate_id: primary key of the candidate
    """
    response = send_request('get', ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id), token, {}, verify=False)
    assert response.status_code == codes.NOT_FOUND

def link_candidates(token, account_data, candidate_data):
    """
    Link a GT candidate to an ATS candidate and validate the link.

    :param str token: authentication token
    :param dict account_data: data to create an account with
    :param int candidate_data: data to create an ATS candidate
    """
    account_id = create_and_validate_account(token, account_data)
    candidate_id = create_and_validate_candidate(token, account_id, candidate_data)
    gt_candidate = db.session.query(Candidate).first()
    url = ATSServiceApiUrl.CANDIDATE_LINK % (gt_candidate.id, candidate_id)
    response = send_request('post', url, token, {})
    assert response.status_code == codes.CREATED
    response = send_request('get', ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id), token, {}, verify=False)
    assert response.status_code == codes.OK
    values = json.loads(response.text)
    assert gt_candidate.id == int(values['gt_candidate_id'])
    return account_id, gt_candidate.id, candidate_id
