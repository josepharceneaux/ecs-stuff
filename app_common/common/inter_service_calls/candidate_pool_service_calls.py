import json
import requests
from contracts import contract
from ..custom_contracts import define_custom_contracts
from ..routes import CandidatePoolApiUrl, EmailCampaignApiUrl
from ..utils.handy_functions import http_request, create_oauth_headers

define_custom_contracts()


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
            url=EmailCampaignApiUrl.CAMPAIGNS,
            data=json.dumps(data),
            headers={'Authorization': access_token,
                     'content-type': 'application/json'}
            )
    assert response.status_code == 201
    return response.json()


def create_campaign_send_from_api(campaign_id, access_token):
    access_token = access_token if "Bearer" in access_token else "Bearer %s" % access_token
    response = requests.post(
            url=EmailCampaignApiUrl.SEND % campaign_id,
            headers={'Authorization': access_token,
                     'content-type': 'application/json'}
            )
    assert response.status_code == 200
    return response.json()


@contract
def get_candidates_of_smartlist(list_id, candidate_ids_only=False, access_token=None, user_id=None, per_page=1000,
                                cursor='initial'):
    """
    Calls smartlist API and retrieves the candidates of a smart or dumb list.
    :param int | long list_id: smartlist id.
    :param bool candidate_ids_only: Whether or not to get only ids of candidates
    :param str | unicode | None access_token: Token for authorization
    :param int | long | None user_id: id of user
    :param int | long per_page: Number of results in one page
    :param str| unicode cursor: Cursor for the page to be fetched
    :rtype: list

    """
    params = {'fields': 'id'} if candidate_ids_only else {}
    candidates = []
    page_no = 0
    has_more_candidates = True

    # Details regarding aws pagination can be found at:
    # http://docs.aws.amazon.com/cloudsearch/latest/developerguide/paginating-results.html

    while has_more_candidates:
        response = get_candidates_from_smartlist_with_page_params(list_id, per_page,
                                                                  cursor, params,
                                                                  access_token, user_id)
        page_no += 1
        response_body = response.json()
        total_pages = response_body['max_pages']
        candidates.extend(response_body['candidates'])

        if total_pages == page_no:
            cursor = response_body['cursor']
        else:
            has_more_candidates = False

    if candidate_ids_only:
        return [long(candidate['id']) for candidate in candidates]
    return candidates


@contract(returns=requests.Response)
def get_candidates_from_smartlist_with_page_params(list_id, per_page, cursor, params, access_token=None, user_id=None):
    """
    Method to get candidates from smartlist based on smartlist id and pagination params.
    :param (int | long) list_id: Id of smartlist.
    :param (int) per_page: Number of results per page
    :param (str | unicode) cursor: Cursor against which candidates are to be fetched.
    :param (dict| None) params: Specific params to include in request. e.g. candidates_ids_only etc
    :param (str | None) access_token: access token of user
    :param (int | long | None) user_id: Id of user
    """
    if not params:
        params = {}
    params.update({'page': cursor}) if cursor else None
    params.update({'limit': per_page}) if per_page else None
    response = http_request('get', CandidatePoolApiUrl.SMARTLIST_CANDIDATES % str(list_id),
                            params=params, headers=create_oauth_headers(access_token, user_id=user_id))
    return response


@contract
def assert_smartlist_candidates(smartlist_id, expected_count, access_token):
    """
    This gets the candidates for given smartlist_id.
    If number of candidates found is same as expected_count, it returns True.
    Otherwise it returns False.
    :param (int | long) smartlist_id: id of smartlist
    :param (int | long) expected_count: expected number of candidates
    :param (str) access_token: access token of user to make HTTP request on smartlist API
    """
    candidates = get_candidates_of_smartlist(smartlist_id, True, access_token)
    assert len(candidates) == expected_count, \
        'Expecting %s candidate(s). Got %s candidate(s) for smartlist(id:%s).' \
        % (expected_count, len(candidates), smartlist_id)
