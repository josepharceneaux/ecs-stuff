import json

from candidate_pool_service.common.models.db import db
from candidate_pool_service.common.models.smartlist import SmartlistCandidate, Smartlist
from candidate_pool_service.common.models.candidate import Candidate
from candidate_pool_service.common.models.user import User
from candidate_pool_service.common.error_handling import InternalServerError
from candidate_pool_service.common.utils.candidate_service_calls import (search_candidates_from_params,
                                                                         update_candidates_on_cloudsearch)

__author__ = 'jitesh'


def get_candidates(smartlist, access_token, candidate_ids_only=False, count_only=False, max_candidates=0):
    """
    Get the candidates of a smart or dumb list.
    :param smartlist: Smartlist row object
    :param max_candidates: If set to 0, will have no limit.
    :return:  candidates and total_found
    what TalentSearch.search_candidates returns
    """
    # If it is a smartlist, perform the dynamic search
    if smartlist.search_params:
        search_params = json.loads(smartlist.search_params)
        if candidate_ids_only:
            search_params['fields'] = 'id'
        if count_only:
            search_params['fields'] = 'count_only'
        search_results = search_candidates_from_params(search_params, access_token)
    # If a dumblist & getting count only, just do count
    elif count_only:
        count = SmartlistCandidate.query.with_entities(SmartlistCandidate.candidate_id).filter_by(
            smartlist_id=smartlist.id).count()
        return dict(candidates=[], total_found=count)
    # If a dumblist and not doing count only, simply return all smartlist_candidates
    else:
        smartlist_candidate_rows = SmartlistCandidate.query.with_entities(SmartlistCandidate.candidate_id)\
            .filter_by(smartlist_id=smartlist.id)
        if max_candidates:
            smartlist_candidate_rows = smartlist_candidate_rows.limit(max_candidates)

        candidates = []
        candidate_ids = []
        for smartlist_candidate_row in smartlist_candidate_rows:
            candidates.append({'id': smartlist_candidate_row.candidate_id})
            candidate_ids.append(smartlist_candidate_row.candidate_id)
        if candidate_ids_only:
            return {'candidates': candidates, 'total_found': len(candidate_ids)}
        search_results = create_candidates_dict(candidate_ids)

    return search_results


def create_candidates_dict(candidate_ids):
    """Given candidate ids, function will return respective candidates in formatted dict"""
    candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
    candidates_dict = {"candidates": [], "total_found": 0}
    for candidate in candidates:
        candidate_dict = {}
        candidate_id = candidate.id
        candidate_dict["id"] = candidate_id
        candidate_dict["emails"] = [email.address for email in
                                    candidate.candidate_emails]
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
    candidate_count = get_candidates(smartlist, oauth_token, count_only=True)['total_found']

    return {
        "total_found": candidate_count,
        "user_id": smartlist.user_id,
        "id": smartlist.id,
        "name": smartlist.name,
        "search_params": smartlist.search_params
    }



def get_all_smartlists(auth_user, oauth_token):
    """
    Get all smartlists from user's domain.
    :param auth_user: User object
    :return: List of dictionary of all smartlists present in user's domain
    """
    smartlists = Smartlist.query.join(Smartlist.user).filter(
        User.domain_id == auth_user.domain_id, Smartlist.is_hidden == False).all()

    if smartlists:
        return [create_smartlist_dict(smartlist, oauth_token) for smartlist in smartlists]

    return "Could not find any smartlist in your domain"


def save_smartlist(user_id, name, search_params=None, candidate_ids=None, access_token=None):
    """
    Creates a smart or dumb list.

    :param user_id: list owner
    :param name: name of list
    :param search_params:
    :param candidate_ids: only set if you want to create a dumb list
    :type candidate_ids: list[long|int] | None
    * only one parameter should be present: either `search_params` or `candidate_ids` (Should be validated by 'calling' function)
    :param access_token: oauth token required only in case of candidate_ids, it is required by search service to upload candidates to cloudsearch
    :type access_token: basestring
    :return: Newly created smartlist row object
    """
    if candidate_ids and not access_token:
        raise InternalServerError("Access token is required when adding candidate ids to smartlist")

    smartlist = Smartlist(name=name,
                          user_id=user_id,
                          search_params=search_params)
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

