import json

from candidate_service.candidate_app import db, logger
from candidate_service.common.models.smart_list import SmartListCandidate
from candidate_service.common.models.candidate import Candidate, CandidateEmail, CandidateSocialNetwork, CandidatePhone

__author__ = 'jitesh'


def get_candidates(smart_list, candidate_ids_only=False, count_only=False, max_candidates=0):
    """
    Get the candidates of a smart or dumb list.
    :param max_candidates: If set to 0, will have no limit.
    :return:  dict of 'candidate_ids, total_found' if candidate_ids_only=True, otherwise returns
    what TalentSearch.search_candidates returns
    """
    domain_id = smart_list.user.domain_id

    # If it is a smartlist, perform the dynamic search
    if smart_list.search_params:
        search_params = json.loads(smart_list.search_params)
        # TODO: Get candidates from candidate search service
        search_results = search_candidates(domain_id, search_params, search_limit=max_candidates,
                                           candidate_ids_only=candidate_ids_only,
                                           count_only=count_only)
    # If a dumblist & getting count only, just do count
    elif count_only:
        count = db.session.query(SmartListCandidate.candidate_id).filter_by(smart_list_id=smart_list.id).count()
        search_results = dict(candidate_ids=[], total_found=count)
    # If a dumblist and not doing count only, simply return all smart_list_candidates
    else:
        smart_list_candidate_rows = db.session.query(SmartListCandidate.candidate_id)\
            .filter_by(smart_list_id=smart_list.id)
        if max_candidates:
            smart_list_candidate_rows = smart_list_candidate_rows.limit(max_candidates)

        # count = smart_list_candidate_rows.count()
        candidate_ids = [smart_list_candidate_row.candidate_id for smart_list_candidate_row in smart_list_candidate_rows]

        search_results = create_candidates_dict(candidate_ids)

    return search_results


def search_candidates(domain_id, search_params, search_limit, candidate_ids_only, count_only):
    """Call search API with search params to retrieve candidates"""
    # TODO: Call search API
    return {}


def create_candidates_dict(candidate_ids):
    """Given candidate ids, function will return respective candidates in formatted dict"""
    # TODO: Add pagination
    candidates = db.session.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    candidates_dict = {"candidates": [], "count": 0}
    for candidate in candidates:
        candidate_dict = {}
        candidate_id = candidate.id
        candidate_dict["id"] = candidate_id
        candidate_dict["emails"] = [{email.email_label.description: email.address} for email in
                                    db.session.query(CandidateEmail).filter_by(candidate_id=candidate_id).all()]
        candidate_dict["social_network"] = [{"url": sn.social_profile_url, "id": sn.social_network_id} for sn in
                                            db.session.query(CandidateSocialNetwork).filter_by(
                                                candidate_id=candidate_id).all()]
        candidate_dict["phone_numbers"] = [{phone.phone_label.description: phone.value} for phone in
                                    db.session.query(CandidatePhone).filter_by(candidate_id=candidate_id).all()]
        # TODO: Add more fields
        # Finally append all candidates in list and return it
        candidates_dict["candidates"].append(candidate_dict)
        # increment the counter
        candidates_dict["count"] += 1
    return candidates_dict

