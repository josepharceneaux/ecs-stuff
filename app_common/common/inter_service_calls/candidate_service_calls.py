"""File contains handy functions which can be used to call frequently used
candidate_service API calls."""

import json
import requests
from ..models.user import User
from ..routes import CandidateApiUrl
from ..utils.handy_functions import create_oauth_headers, http_request
from ..error_handling import InternalServerError, InvalidUsage, ForbiddenError

__author__ = 'jitesh'


def search_candidates_from_params(search_params, access_token, user_id=None):
    """
    Calls the candidate_service's Search API with given search criteria and returns the search result.
    :param search_params: Search params or search criteria upon which candidates would be filtered.
    :param access_token: Oauth-based or JWT-based token
    :param user_id: Id of logged-in user
    :return: search result based on search criteria.
    """
    if not access_token:
        secret_key_id, jw_token = User.generate_jw_token(user_id=user_id)
        headers = {'Authorization': jw_token,
                   'X-Talent-Secret-Key-ID': secret_key_id,
                   'Content-Type': 'application/json'}
    else:
        access_token = access_token if 'Bearer' in access_token else 'Bearer %s' % access_token
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}

    response = requests.get(
            url=CandidateApiUrl.CANDIDATE_SEARCH_URI,
            params=search_params,
            headers=headers
    )
    if not response.ok:
        raise InvalidUsage("Couldn't get candidates from Search API because %s" % response)
    else:
        return response.json()


def update_candidates_on_cloudsearch(access_token, candidate_ids):
    """
    Calls candidate search service to upload candidate documents for given candidate ids
    :param access_token: User's access token
    :type access_token: basestring
    :param candidate_ids: List of candidate ids
    :type candidate_ids: list
    """
    # Update Candidate Documents in Amazon Cloud Search
    headers = {'Authorization': access_token if 'Bearer' in access_token else 'Bearer %s' % access_token,
               'Content-Type': 'application/json'}
    response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
                             data=json.dumps({'candidate_ids': candidate_ids}))

    if response.status_code != 204:
        raise InternalServerError("Error occurred while uplaoding candidates on cloudsearch. "
                                  "Status Code: %s Response: %s"
                                  % (response.status_code, response.json()))


def create_candidates_from_candidate_api(oauth_token, data, return_candidate_ids_only=False, user_id=None):
    """
    Function sends a request to CandidateResource/post()
    Call candidate api using oauth token or user_id

    :param oauth_token: Oauth token, if None, then create a secret X-Talent-Key oauth token (JWT)
    :param data: Candidates object data to create candidate
    :param return_candidate_ids_only: If true it will only return the created candidate ids
    else it will return the created candidate response json object
    Returns: list of created candidate ids
    # """

    if not oauth_token and not user_id:
        raise InvalidUsage(error_message="Call to candidate service should be made either with user oauth or JWT oauth."
                                         "oauth_token and user_id cannot be None at same time.")

    headers = dict()
    if not oauth_token and user_id:
        secret_key_id, oauth_token = User.generate_jw_token(user_id=user_id)
        headers.update({'X-Talent-Secret-Key-ID': secret_key_id})
        headers.update({'Authorization': oauth_token})
    else:
        headers.update({'Authorization': oauth_token if 'Bearer' in oauth_token else 'Bearer %s' % oauth_token})

    headers.update({'content-type': 'application/json'})

    resp = requests.post(
            url=CandidateApiUrl.CANDIDATES,
            headers={'Authorization': oauth_token if 'Bearer' in oauth_token else 'Bearer %s'
                                                                                  % oauth_token,
                     'content-type': 'application/json'},
            data=json.dumps(data)
    )
    assert resp.status_code == 201
    if return_candidate_ids_only:
        return [candidate['id'] for candidate in resp.json()['candidates']]
    return resp.json()


def get_candidate_subscription_preference(candidate_id, user_id):
    """
    Method to get the subscription preference of a candidate with specified candidate id.
    :param candidate_id: Id of candidate for which subscription prederence is to be retrieved.
    :param user_id: Id of owner user of the candidate.
    """
    if not candidate_id:
        raise InternalServerError(error_message='candidate_id must be provided')
    if not user_id:
        raise InternalServerError(error_message='user_id must be provided')
    resp = http_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id,
                        headers=create_oauth_headers(user_id=user_id))
    if resp.status_code == ForbiddenError.http_status_code():
        raise ForbiddenError('Not authorized to get Candidate(id:%s)' % candidate_id)
    assert resp.status_code == 200
    response = resp.json()
    # return candidate's subscription_preference
    return response['candidate']['subscription_preference']
