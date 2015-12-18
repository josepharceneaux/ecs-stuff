import json
import ast
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


def validate_list_belongs_to_domain(smartlist, user_id):
    """
    Validates if given list belongs to user's domain
    :param smartlist: smart list database row
    :param user_id:
    :return:False, if list does not belongs to current user's domain else True
    """
    if smartlist.user_id == user_id:
        # if user id is same then smart list belongs to user
        return True
    # check whether smartlist belongs to user's domain
    return Smartlist.query.with_entities(Smartlist.id).join(Smartlist.user).filter(and_(User.domain_id == user_id, Smartlist.id == smartlist.id)).count() == 1


def validate_and_format_smartlist_post_data(data, user_id):
    """Validates request.form data against required parameters
    strips unwanted whitespaces (if present)
    creates list of candidate ids (if present)
    returns list of candidate ids or search params
    """
    smartlist_name = data.get('name')
    candidate_ids = data.get('candidate_ids')  # comma separated ids
    search_params = data.get('search_params')
    if not smartlist_name or not smartlist_name.strip():
        raise InvalidUsage(error_message="Missing input: `name` is required for creating list", error_code=400)
    # any of the parameters "search_params" or "candidate_ids" should be present
    if not candidate_ids and not search_params:
        raise InvalidUsage(error_message="Missing input: Either `search_params` or `candidate_ids` are required",
                           error_code=400)
    # Both the parameters will create a confusion, so only one parameter should be present. Its better to notify user.
    if candidate_ids and search_params:
        raise InvalidUsage(
            error_message="Bad input: `search_params` and `candidate_ids` both are present. Service accepts only one",
            error_code=400)
    if search_params:
        # validate if search_params in valid dict format.
        try:
            search_params = ast.literal_eval(search_params)
        except Exception:
            raise InvalidUsage("`search_params` should be in valid format.", 400)

        if not isinstance(search_params, dict):
            raise InvalidUsage("`search_params` should in dictionary format.", 400)

    formatted_request_data = {'name': smartlist_name.strip(),
                              'candidate_ids': None,
                              'search_params': None}
    if candidate_ids:
        try:
            # Remove duplicate ids, in case user accidentally added duplicates
            # remove unwanted whitespaces and convert unicode to long
            candidate_ids = [long(candidate_id.strip()) for candidate_id in set(candidate_ids.split(',')) if candidate_id]
        except ValueError:
            raise InvalidUsage("Incorrect input: Candidate ids must be numeric value and separated by comma")
        # Check if provided candidate ids are present in our database and also belongs to auth user's domain
        if not validate_candidate_ids_belongs_to_user_domain(candidate_ids, user_id):
            raise ForbiddenError("Provided list of candidates does not belong to user's domain")
        formatted_request_data['candidate_ids'] = candidate_ids
    else:  # if not candidate_ids then it is search_params
        formatted_request_data['search_params'] = json.dumps(search_params)
    return formatted_request_data


def validate_candidate_ids_belongs_to_user_domain(candidate_ids, user_id):
    user = User.query.get(user_id)
    return Candidate.query.with_entities(Candidate.id).join(User, Candidate.user_id == User.id).filter(
        and_(User.domain_id == user.domain_id, Candidate.id.in_(candidate_ids))).count() == len(candidate_ids)

