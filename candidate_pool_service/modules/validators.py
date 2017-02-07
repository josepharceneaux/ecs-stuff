import json
from sqlalchemy import and_
from candidate_pool_service.common.models.user import User
from candidate_pool_service.common.models.candidate import Candidate
from candidate_pool_service.common.models.smartlist import SmartlistCandidate
from candidate_pool_service.common.error_handling import InvalidUsage, ForbiddenError
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPipeline

__author__ = 'jitesh'


def validate_and_format_smartlist_post_data(data, user):
    """Validates request.form data against required parameters
    strips unwanted whitespaces (if present)
    creates list of candidate ids (if present)
    returns list of candidate ids or search params
    """
    smartlist_name = data.get('name')
    candidate_ids = data.get('candidate_ids')  # comma separated ids
    search_params = data.get('search_params')
    talent_pipeline_id = data.get('talent_pipeline_id')

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

    talent_pipeline = TalentPipeline.query.get(talent_pipeline_id) if talent_pipeline_id else None

    if not talent_pipeline:
        raise InvalidUsage("Valid talent-pipeline-id is required to create new smartlist")

    smartlist_name = smartlist_name.strip()
    formatted_request_data = {'name': smartlist_name,
                              'candidate_ids': None,
                              'search_params': None,
                              'talent_pipeline_id': talent_pipeline.id}
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


def validate_and_format_smartlist_patch_data(smart_list, data, user):
    """Validates request.form data against required parameters
    strips unwanted whitespaces (if present)
    creates list of candidate ids (if present)
    returns list of candidate ids or search params
    """
    smartlist_name = data.get('name', '').strip()
    candidate_ids = data.get('candidate_ids')  # comma separated ids
    search_params = data.get('search_params')
    talent_pipeline_id = data.get('talent_pipeline_id')

    # Both the parameters will create a confusion, so only one parameter should be present. Its better to notify user.
    if candidate_ids and search_params:
        raise InvalidUsage("Bad input: `search_params` and `candidate_ids` both are present. Service accepts only one")
    if search_params and not isinstance(search_params, dict):
        raise InvalidUsage("`search_params` should in dictionary format.")

    talent_pipeline = TalentPipeline.query.get(talent_pipeline_id) if talent_pipeline_id else None

    formatted_request_data = {'name': smartlist_name,
                              'candidate_ids': None,
                              'search_params': None,
                              'talent_pipeline_id': talent_pipeline_id if talent_pipeline else None}

    if candidate_ids:
        if not isinstance(candidate_ids, dict):
            raise InvalidUsage("`candidate_ids` should be in dict format.")

        add_candidate_ids = candidate_ids.get('add', [])
        remove_candidate_ids = candidate_ids.get('remove', [])

        if add_candidate_ids:
            formatted_request_data['add_candidate_ids'] = validate_candidate_ids(add_candidate_ids, user)
            if SmartlistCandidate(SmartlistCandidate.smartlist_id == smart_list.id,
                                  SmartlistCandidate.candidate_id.in_(
                                          formatted_request_data['add_candidate_ids'])).count():
                raise InvalidUsage("Some candidates to be added are already the part of smart_list")

        if remove_candidate_ids:
            formatted_request_data['remove_candidate_ids'] = validate_candidate_ids(remove_candidate_ids, user)
            if SmartlistCandidate.query.filter(
                            SmartlistCandidate.smartlist_id == smart_list.id, SmartlistCandidate.candidate_id.in_(
                            formatted_request_data['remove_candidate_ids'])).count() != len(
                    formatted_request_data['remove_candidate_ids']):
                raise InvalidUsage("Some of candidates to be removed are not the part of smart_list")
    else:
        formatted_request_data['search_params'] = json.dumps(search_params)

    return {key:value for key, value in formatted_request_data.items() if value}


def validate_candidate_ids(candidate_ids, user):

    if not isinstance(candidate_ids, list):
        raise InvalidUsage("`candidate_ids` should be in list format.")

    if filter(lambda x: not isinstance(x, (int, long)), candidate_ids):
        raise InvalidUsage("`candidate_ids` should be list of whole numbers")

    # Remove duplicate ids, in case user accidentally added duplicates
    candidate_ids = list(set(candidate_ids))

    # Check if provided candidate ids are present in our database and also belongs to auth user's domain
    if not validate_candidate_ids_belongs_to_user_domain(candidate_ids, user):
        raise ForbiddenError("Provided list of candidates does not belong to user's domain")

    return candidate_ids


def validate_candidate_ids_belongs_to_user_domain(candidate_ids, user):
    return Candidate.query.with_entities(Candidate.id).join(User, Candidate.user_id == User.id).filter(
        and_(User.domain_id == user.domain_id, Candidate.id.in_(candidate_ids))).count() == len(candidate_ids)

