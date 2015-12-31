import json
from sqlalchemy import and_
from candidate_pool_service.common.models.user import User
from candidate_pool_service.common.models.candidate import Candidate
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.error_handling import InvalidUsage, ForbiddenError
__author__ = 'jitesh'


def validate_and_parse_request_data(data):
    return_fields = data.get('fields').split(',') if data.get('fields') else []
    candidate_ids_only = False
    count_only = False
    if 'candidate_ids_only' in return_fields:
        candidate_ids_only = True
    if 'count_only' in return_fields:
        count_only = True

    return {'candidate_ids_only': candidate_ids_only,
            'count_only': count_only}


def validate_and_format_smartlist_post_data(data, user):
    """Validates request.form data against required parameters
    strips unwanted whitespaces (if present)
    creates list of candidate ids (if present)
    returns list of candidate ids or search params
    """
    smartlist_name = data.get('name')
    candidate_ids = data.get('candidate_ids')  # comma separated ids
    search_params = data.get('search_params')
    if not smartlist_name or not smartlist_name.strip():
        raise InvalidUsage(error_message="Missing input: `name` is required for creating list")
    # any of the parameters "search_params" or "candidate_ids" should be present
    if not candidate_ids and not search_params:
        raise InvalidUsage(error_message="Missing input: Either `search_params` or `candidate_ids` are required")
    # Both the parameters will create a confusion, so only one parameter should be present. Its better to notify user.
    if candidate_ids and search_params:
        raise InvalidUsage(
            error_message="Bad input: `search_params` and `candidate_ids` both are present. Service accepts only one")
    if search_params:
        # validate if search_params in valid dict format.
        if not isinstance(search_params, dict):
            raise InvalidUsage("`search_params` should in dictionary format.")
    smartlist_name = smartlist_name.strip()
    if Smartlist.query.join(Smartlist.user).filter(and_(User.domain_id == user.domain_id, Smartlist.name == smartlist_name)).first():
        raise InvalidUsage("Given smartlist `name` %s already exists in your domain" % smartlist_name)
    formatted_request_data = {'name': smartlist_name,
                              'candidate_ids': None,
                              'search_params': None}
    if candidate_ids:
        if not isinstance(candidate_ids, list):
            raise InvalidUsage("`candidate_ids` should be in list format.")
        if filter(lambda x: not isinstance(x, (int, long)), candidate_ids):
            raise InvalidUsage("`candidate_ids` should be list of whole numbers")
        # Remove duplicate ids, in case user accidentally added duplicates
        candidate_ids = list(set(candidate_ids))
        # Check if provided candidate ids are present in our database and also belongs to auth user's domain
        if not validate_candidate_ids_belongs_to_user_domain(candidate_ids, user):
            raise ForbiddenError("Provided list of candidates does not belong to user's domain")
        formatted_request_data['candidate_ids'] = candidate_ids
    else:  # if not candidate_ids then it is search_params
        formatted_request_data['search_params'] = json.dumps(search_params)
    return formatted_request_data


def validate_candidate_ids_belongs_to_user_domain(candidate_ids, user):
    return Candidate.query.with_entities(Candidate.id).join(User, Candidate.user_id == User.id).filter(
        and_(User.domain_id == user.domain_id, Candidate.id.in_(candidate_ids))).count() == len(candidate_ids)

