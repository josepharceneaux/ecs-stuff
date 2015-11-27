"""
Functions related to candidate_service/candidate_app/api validations
"""
from sqlalchemy import and_
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User
from candidate_service.common.models.misc import (AreaOfInterest, CustomField)
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.common.error_handling import InvalidUsage, ForbiddenError

def does_candidate_belong_to_user(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    :type   candidate_id: int
    :type   user_row: User
    :rtype: bool
    """
    candidate_row = db.session.query(Candidate).join(User).filter(
        Candidate.id == candidate_id, Candidate.user_id == user_row.id,
        User.domain_id == user_row.domain_id
    ).first()

    return True if candidate_row else False


def do_candidates_belong_to_user(user_row, candidate_ids):
    """
    Function checks if:
        1. Candidates belong to user AND
        2. Candidates are in the same domain as the user
    :type user_row:         User
    :type candidate_ids:    list
    :rtype  bool
    """
    assert isinstance(candidate_ids, list)
    exists = db.session.query(Candidate).join(User).\
                 filter(Candidate.id.in_(candidate_ids),
                        User.domain_id != user_row.domain_id).count() == 0
    return exists


def is_custom_field_authorized(user_domain_id, custom_field_ids):
    """
    Function checks if custom_field_ids belong to the logged-in-user's domain
    :type   user_domain_id:   int
    :type   custom_field_ids: [int]
    :rtype: bool
    """
    assert isinstance(custom_field_ids, list)
    exists = db.session.query(CustomField).\
                 filter(CustomField.id.in_(custom_field_ids),
                        CustomField.domain_id != user_domain_id).count() == 0
    return exists


def is_area_of_interest_authorized(user_domain_id, area_of_interest_ids):
    """
    Function checks if area_of_interest_ids belong to the logged-in-user's domain
    :type   user_domain_id:       int
    :type   area_of_interest_ids: [int]
    :rtype: bool
    """
    assert isinstance(area_of_interest_ids, list)
    exists = db.session.query(AreaOfInterest).\
                 filter(AreaOfInterest.id.in_(area_of_interest_ids),
                        AreaOfInterest.domain_id != user_domain_id).count() == 0
    return exists


def does_email_campaign_belong_to_domain(user_row):
    """
    Function retrieves all email campaigns belonging to user's domain
    :rtype: bool
    """
    email_campaign_rows = db.session.query(EmailCampaign).join(User).\
        filter(User.domain_id == user_row.domain_id).first()

    return True if email_campaign_rows else False


def validate_and_parse_request_data(data):
    list_id = data.get('id')
    return_fields = data.get('return').split(',') if data.get('return') else []
    candidate_ids_only = False
    count_only = False
    if 'candidate_ids_only' in return_fields:
        candidate_ids_only = True
    if 'count_only' in return_fields:
        count_only = True
    if not list_id or list_id.strip() == '':
        raise InvalidUsage('list_id is required', 400)

    return {'list_id': long(list_id.strip() if list_id else list_id),
            'candidate_ids_only': candidate_ids_only,
            'count_only': count_only
            }


def validate_list_belongs_to_domain(smart_list, user_id):
    """
    Validates if given list belongs to user's domain
    :param smart_list: smart list database row
    :param user_id:
    :return:False, if list does not belongs to current user's domain else True
    """
    if smart_list.user_id == user_id:
        # if user id is same then smart list belongs to user
        return True
    user = User.query.get(user_id)
    # TODO: Revisit; check for alternate query.
    domain_users = db.session.query(User.id).filter_by(domain_id=user.domain_id).all()
    domain_user_ids = [row[0] for row in domain_users]
    if user_id in domain_user_ids:
        # if user belongs to same domain i.e. smartlist belongs to domain
        return True
    return False


def _validate_and_format_smartlist_post_data(data, user_id):
    """Validates request.form data against required parameters
    strips unwanted whitespaces (if present)
    creates list of candidate ids (if present)
    returns list of candidate ids or search params
    """
    smartlist_name = data.get('name')
    candidate_ids = data.get('candidate_ids')  # comma separated ids
    search_params = data.get('search_params')
    # TODO: check if not and if not smart_list_name.strip() if both are equal. Check 400 error code
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
        formatted_request_data['search_params'] = search_params.strip()
    return formatted_request_data


def validate_candidate_ids_belongs_to_user_domain(candidate_ids, user_id):
    user = User.query.get(user_id)
    return db.session.query(Candidate.id).join(User, Candidate.user_id == User.id).filter(
        and_(User.domain_id == user.domain_id, Candidate.id.in_(candidate_ids))).count() == len(candidate_ids)
