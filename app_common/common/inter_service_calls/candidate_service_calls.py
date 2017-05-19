"""File contains handy functions which can be used to call frequently used
candidate_service API calls."""

# Standard Imports
import json

# Third Party
import requests
from requests import codes
from requests_futures.sessions import FuturesSession

# Application Specific
from ..models.user import User
from ..routes import CandidateApiUrl
from ..utils.handy_functions import create_oauth_headers, http_request, send_request
from ..error_handling import InternalServerError, InvalidUsage, ForbiddenError
from ..utils.validators import raise_if_not_positive_int_or_long

__author__ = 'jitesh'

MAX_WORKERS = 20

futures_session = FuturesSession(max_workers=MAX_WORKERS)


def search_candidates_from_params(search_params, access_token, url_args=None, user_id=None):
    """
    Calls the candidate_service's Search API with given search criteria and returns the Future object.
    We can get the result from future object by applying .result() on it.
    :param search_params: Search params or search criteria upon which candidates would be filtered.
    :param access_token: Oauth-based or JWT-based token
    :param  url_args:  accepted arguments sent via the url; e.g. "?user_ids=2,3,4"
    :param user_id: Id of logged-in user
    :return: future object for search result based on search criteria.
    """
    if not access_token:
        jw_token = User.generate_jw_token(user_id=user_id)
        headers = {'Authorization': jw_token,
                   'Content-Type': 'application/json'}
    else:
        access_token = access_token if 'Bearer' in access_token else 'Bearer %s' % access_token
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}

    url = CandidateApiUrl.CANDIDATE_SEARCH_URI
    future = futures_session.get(url=(url + url_args) if url_args else url, params=search_params, headers=headers)
    return future


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
        oauth_token = User.generate_jw_token(user_id=user_id)
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
    assert resp.status_code == 201, resp.text
    if return_candidate_ids_only:
        return [candidate['id'] for candidate in resp.json()['candidates']]
    return resp.json()


def create_or_update_candidate(oauth_token, data, return_candidate_ids_only=False, request_method='post'):
    """
    Function sends a request to CandidateResource/post()
    Call candidate api using oauth token or user_id

    :param oauth_token: Oauth token, if None, then create a secret X-Talent-Key oauth token (JWT)
    :type oauth_token: str
    :param data: Candidates object data to create candidate
    :type data: dict
    :param return_candidate_ids_only: If true it will only return the created candidate ids
    :type return_candidate_ids_only: bool
    else it will return the created candidate response json object
    Returns: list of created candidate ids
    :param string request_method: HTTP method to be called on candidate-service
    :rtype: dict|int|long
    """
    resp = send_request(request_method, url=CandidateApiUrl.CANDIDATES, access_token=oauth_token, data=data)
    data_resp = resp.json()
    if resp.status_code not in [codes.CREATED, codes.OK]:
        raise InternalServerError('Candidate creation failed. Error:%s' % data_resp)
    if return_candidate_ids_only:
        return data_resp['candidates'][0]['id']
    return data_resp


def get_candidate_subscription_preference(candidate_id, user_id, app=None):
    """
    Method to get the subscription preference of a candidate with specified candidate id.
    :param candidate_id: Id of candidate for which subscription preference is to be retrieved.
    :param user_id: Id of user.
    :param app: Flask app instance
    :type candidate_id: int | long
    :type user_id: int | long
    :rtype: int
    """
    raise_if_not_positive_int_or_long(candidate_id)
    raise_if_not_positive_int_or_long(user_id)
    resp = http_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % str(candidate_id),
                        headers=create_oauth_headers(user_id=user_id), app=app)
    if resp.status_code == ForbiddenError.http_status_code():
        raise ForbiddenError('Not authorized to get Candidate(id:%s)' % candidate_id)
    assert resp.status_code == 200
    response = resp.json()
    # return candidate's subscription_preference
    return response['candidate']['subscription_preference']
