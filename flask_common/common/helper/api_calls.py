from ..routes import CandidateApiUrl
from ..tests.sample_data import generate_single_candidate_data
from ..error_handling import InternalServerError
import requests
import json

__author__ = 'jitesh'


def create_candidates_from_candidate_api(access_token, data=None):
    """
    Function sends a request to CandidateResource/post()
    Returns: list of created candidate ids
    """
    if not data:
        data = generate_single_candidate_data()

    resp = requests.post(
        url=CandidateApiUrl.CANDIDATES,
        headers={'Authorization': 'Bearer %s' % access_token if 'Bearer' in access_token else 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    assert resp.status_code == 201
    return [candidate['id'] for candidate in resp.json()['candidates']]


def search_candidates_from_params(search_params, access_token):
    """
    Calls the search service with given search criteria and returns the search result.
    :param search_params: Search params or search criteria upon which candidates would be filtered.
    :param access_token: User access token TODO: Change once server to server trusted calls are implemented.
    :return: search result based on search criteria.
    """
    try:
        return requests.get(
            url=CandidateApiUrl.SEARCH,
            params=search_params,
            headers={'Authorization': access_token if 'Bearer' in access_token else 'Bearer %s' % access_token}
        ).json()
    except Exception as ex:
        raise InternalServerError("Error occurred while searching for candidates. Exception: %s" % ex)

