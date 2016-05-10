import json
import requests
from ..utils.api_utils import DEFAULT_PAGE
from ..utils.validators import raise_if_not_instance_of
from ..routes import CandidatePoolApiUrl, EmailCampaignUrl
from ..utils.handy_functions import http_request, create_oauth_headers


def create_smartlist_from_api(data, access_token):
    access_token = access_token if "Bearer" in access_token else "Bearer %s" % access_token
    response = requests.post(
            url=CandidatePoolApiUrl.SMARTLISTS,
            data=json.dumps(data),
            headers={'Authorization': access_token,
                     'content-type': 'application/json'}
            )
    assert response.status_code == 201
    return response.json()


def create_campaign_from_api(data, access_token):
    access_token = access_token if "Bearer" in access_token else "Bearer %s" % access_token
    response = requests.post(
            url=EmailCampaignUrl.CAMPAIGNS,
            data=json.dumps(data),
            headers={'Authorization': access_token,
                     'content-type': 'application/json'}
            )
    assert response.status_code == 201
    return response.json()


def create_campaign_send_from_api(campaign_id, access_token):
    access_token = access_token if "Bearer" in access_token else "Bearer %s" % access_token
    response = requests.post(
            url=EmailCampaignUrl.SEND % campaign_id,
            headers={'Authorization': access_token,
                     'content-type': 'application/json'}
            )
    assert response.status_code == 200
    return response.json()


def get_candidates_of_smartlist(list_id, candidate_ids_only=False, access_token=None):
    """
    Calls smartlist API and retrieves the candidates of a smart or dumb list.
    :param (int, long) list_id: smartlist id.
    :param (bool) candidate_ids_only: Whether or not to get only ids of candidates
    """
    per_page = 1000  # Smartlists can have a large number of candidates, hence page size of 1000
    params = {'fields': 'id'} if candidate_ids_only else {}
    response = get_candidates_from_smartlist_with_page_params(list_id, per_page, DEFAULT_PAGE,
                                                              params, access_token)
    response_body = response.json()
    candidates = response_body['candidates']
    no_of_pages = response_body['max_pages']
    if no_of_pages > DEFAULT_PAGE:
        for current_page in range(DEFAULT_PAGE, int(no_of_pages)):
            next_page = current_page + DEFAULT_PAGE
            response = get_candidates_from_smartlist_with_page_params(list_id, per_page,
                                                                      next_page, params,
                                                                      access_token)
            response_body = response.json()
            candidates.extend(response_body['candidates'])
    if candidate_ids_only:
        return [candidate['id'] for candidate in candidates]
    return candidates


def get_candidates_from_smartlist_with_page_params(list_id, per_page, page, params, access_token=None):
    """
    Method to get candidates from smartlist based on smartlist id and pagination params.
    :param (int, long) list_id: Id of smartlist.
    :param (int) per_page: Number of results per page
    :param (int) page: Number of page to fetch in response
    :param (dict| None) params: Specific params to include in request. e.g. candidates_ids_only etc
    :param (str | None) access_token: access token of user
    """
    raise_if_not_instance_of(list_id, (int, long))
    raise_if_not_instance_of(page, int)
    raise_if_not_instance_of(per_page, int)
    if not params:
        params = {}
    params.update({'page': page}) if page else None
    params.update({'limit': per_page}) if per_page else None
    response = http_request('get', CandidatePoolApiUrl.SMARTLIST_CANDIDATES % list_id,
                            params=params, headers=create_oauth_headers(access_token))
    return response


def assert_smartlist_candidates(smartlist_id, expected_count, access_token):
    """
    This gets the candidates for given smartlist_id.
    If number of candidates found is same as expected_count, it returns True.
    Otherwise it returns False.
    :param (int, long) smartlist_id: id of smartlist
    :param (int, long) expected_count: expected number of candidates
    :param (str) access_token: access token of user to make HTTP request on smartlist API
    """
    candidates = get_candidates_of_smartlist(smartlist_id, True, access_token)
    assert len(candidates) == expected_count
