import json
import requests
from ..utils.api_utils import DEFAULT_PAGE
from ..error_handling import InternalServerError
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


def get_candidates_of_smartlist(list_id, campaign, candidate_ids_only=False, access_token=None):
    """
    Calls smartlist API and retrieves the candidates of a smart or dumb list.
    :param list_id: smartlist id.
    :param campaign: email campaign object
    :param candidate_ids_only: Whether or not to get only ids of candidates
    :return:
    """
    per_page = 1000  # Smartlists can have a large number of candidates, hence page size of 1000
    params = {'fields': 'id'} if candidate_ids_only else {}
    response = get_candidates_from_smartlist_with_page_params(list_id, per_page, DEFAULT_PAGE,
                                                              params, campaign, access_token)
    response_body = response.json()
    candidates = response_body['candidates']
    no_of_pages = response_body['max_pages']
    if int(no_of_pages) > DEFAULT_PAGE:
        for current_page in range(DEFAULT_PAGE, int(no_of_pages)):
            next_page = current_page + DEFAULT_PAGE
            response = get_candidates_from_smartlist_with_page_params(list_id, per_page,
                                                                      next_page, params, campaign,
                                                                      access_token)
            response_body = response.json()
            candidates.extend(response_body['candidates'])
    if candidate_ids_only:
        return [long(candidate['id']) for candidate in candidates]
    return candidates


def get_candidates_from_smartlist_with_page_params(list_id, per_page, page, params,
                                                   campaign, access_token=None):
    """
    Method to get candidates from smartlist based on smartlist id and pagination params.
    :param list_id: Id of smartlist.
    :param per_page: Number of results per page
    :param page: Number of page to fetch in response
    :param params: Specific params to include in request. e.g. candidates_ids_only etc
    :param campaign: Email Campaign object
    :param access_token: access token of user
    :return:
    """
    if not list_id:
        raise InternalServerError("get_candidates_from_smartlist_with_page_params: Smartlist id not provided"
                                  "for email-campaign (id:%d) & user(id:%d)" % (campaign.id, campaign.user_id))
    if not per_page or not page:
        raise InternalServerError("get_candidates_from_smartlist_with_page_params: Pagination params not provided"
                                  "for email-campaign (id:%d) & user(id:%d)" % (campaign.id, campaign.user_id))
    if not params:
        params = {}
    params.update({'page': page}) if page else None
    params.update({'limit': per_page}) if per_page else None
    response = http_request('get', CandidatePoolApiUrl.SMARTLIST_CANDIDATES % list_id,
                            params=params, headers=create_oauth_headers(access_token))
    return response
