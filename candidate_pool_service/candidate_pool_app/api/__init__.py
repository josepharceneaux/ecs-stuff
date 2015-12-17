import requests
from candidate_pool_service.candidate_pool_app import logger
from candidate_pool_service.common.utils.app_rest_urls import CandidateApiUrl
from candidate_pool_service.common.error_handling import InternalServerError


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
            headers={'Authorization': 'Bearer %s' % access_token}
        ).json()
    except Exception as ex:
        logger.exception("Exception occurred while calling search service. Exception: %s" % ex)
        raise InternalServerError("Error occurred while searching for candidates.")

