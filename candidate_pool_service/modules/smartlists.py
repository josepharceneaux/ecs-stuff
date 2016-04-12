from candidate_pool_service.common.models.db import db
from candidate_pool_service.common.models.user import User
from candidate_pool_service.candidate_pool_app import cache
from candidate_pool_service.common.models.candidate import Candidate
from candidate_pool_service.common.error_handling import InternalServerError
from candidate_pool_service.common.models.smartlist import SmartlistCandidate, Smartlist
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import get_smartlist_candidates
from candidate_pool_service.common.inter_service_calls.candidate_service_calls import update_candidates_on_cloudsearch

__author__ = 'jitesh'


@cache.memoize(timeout=86400)
def search_and_count_candidates_from_params(smartlist):
    """
    This function will search and count candidates using search_params
    :param smartlist: SmartList object
    :return:
    """
    return get_smartlist_candidates(smartlist, None, {'fields': 'count_only'})


def create_candidates_dict(candidate_ids):
    """Given candidate ids, function will return respective candidates in formatted dict
    :param candidate_ids: Ids of candidates.
    """
    candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
    candidates_dict = {"candidates": [], "total_found": 0}
    for candidate in candidates:
        candidate_dict = {}
        candidate_id = candidate.id
        candidate_dict["id"] = candidate_id
        candidate_dict["emails"] = [email.address for email in
                                    candidate.emails]
        # Finally append all candidates in list and return it
        candidates_dict["candidates"].append(candidate_dict)
    candidates_dict["total_found"] = len(candidates)
    return candidates_dict


def create_smartlist_dict(smartlist, oauth_token):
    """
    Given smartlist object returns the formatted smartlist dict.
    :param smartlist: smartlist row object
    :param oauth_token: oauth token
    """
    candidate_count = get_smartlist_candidates(smartlist, oauth_token, {'fields': 'count_only'}).get('total_found')

    return {
        "total_found": candidate_count,
        "user_id": smartlist.user_id,
        "id": smartlist.id,
        "talent_pipeline_id": smartlist.talent_pipeline_id,
        "name": smartlist.name,
        "search_params": smartlist.search_params
    }


def get_all_smartlists(auth_user, oauth_token, page=None, page_size=None):
    """
    Get all smartlists from user's domain.
    :param oauth_token: Token for authentication.
    :param auth_user: User object
    :param page: Index of Page
    :param page_size: Size of a single page
    :return: List of dictionary of all smartlists present in user's domain
    """
    if page and page_size:
        smartlists = Smartlist.query.join(Smartlist.user).filter(
                User.domain_id == auth_user.domain_id, Smartlist.is_hidden == 0).paginate(page, page_size, False)
        smartlists = smartlists.items
    else:
        smartlists = Smartlist.query.join(Smartlist.user).filter(
            User.domain_id == auth_user.domain_id, Smartlist.is_hidden == False).all()

    if smartlists:
        return [create_smartlist_dict(smartlist, oauth_token) for smartlist in smartlists]

    return "Could not find any smartlist in your domain"


def save_smartlist(user_id, name, talent_pipeline_id, search_params=None, candidate_ids=None, access_token=None):
    """
    Creates a smart or dumb list.

    :param user_id: list owner
    :param name: name of list
    :param search_params:
    :param talent_pipeline_id:
    :param candidate_ids: only set if you want to create a dumb list
    :type candidate_ids: list[long|int] | None
                         * only one parameter should be present: either `search_params` or `candidate_ids`
                         (Should be validated by 'calling' function)
    :param access_token: oauth token required only in case of candidate_ids, it is required by search service
                         to upload candidates to cloudsearch
    :type access_token: basestring
    :return: Newly created smartlist row object
    """
    if candidate_ids and not access_token:
        raise InternalServerError("Access token is required when adding candidate ids to smartlist")

    smartlist = Smartlist(name=name,
                          user_id=user_id,
                          search_params=search_params, talent_pipeline_id=talent_pipeline_id)
    db.session.add(smartlist)
    db.session.commit()

    if candidate_ids:
        # if candidate_ids are there store in SmartlistCandidate table.
        for candidate_id in candidate_ids:
            row = SmartlistCandidate(smartlist_id=smartlist.id, candidate_id=candidate_id)
            db.session.add(row)
        db.session.commit()

        # Update candidate documents on cloudsearch
        update_candidates_on_cloudsearch(access_token, candidate_ids)

    # TODO Add activity
    return smartlist
