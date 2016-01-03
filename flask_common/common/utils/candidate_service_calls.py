"""File contains handy functions which can be used to call frequently used candidate_service API calls."""

import requests
import json
from ..models.user import User
from ..routes import CandidateApiUrl
from ..error_handling import InternalServerError

__author__ = 'jitesh'


def search_candidates_from_params(search_params, access_token, user_id=None):
    """
    Calls the search service with given search criteria and returns the search result.
    :param search_params: Search params or search criteria upon which candidates would be filtered.
    :param access_token: User access token TODO: Change once server to server trusted calls are implemented.
    :return: search result based on search criteria.
    """
    if not access_token:
        secret_key, oauth_token = User.generate_auth_token(user_id=user_id)
        headers = {'Authorization': oauth_token, 'X-Talent-Server-Key': secret_key, 'Content-Type': 'application/json'}
    else:
        access_token = access_token if 'Bearer' in access_token else 'Bearer %s' % access_token
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}

    return requests.get(
        url=CandidateApiUrl.CANDIDATE_SEARCH_URI,
        params=search_params,
        headers=headers
    ).json()


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
        raise InternalServerError("Error occurred while uplaoding candidates on cloudsearch. Status Code: %s Response: %s" % (response.status_code, response.json()))
