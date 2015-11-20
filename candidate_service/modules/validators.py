"""
Functions related to candidate_service/candidate_app/api validations
"""
from candidate_service.candidate_app import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User
from candidate_service.common.models.misc import (AreaOfInterest, CustomField)
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.common.models.smart_list import SmartList
from candidate_service.common.error_handling import InvalidUsage

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
        raise InvalidUsage('list_id is required')
    return {'list_id': data.get('id').strip() if data.get('id') else data.get('id'),
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
    domain_id = user.domain_id
    # TODO: Revisit; check for alternate query.
    domain_users = db.session.query(User.id).filter_by(domain_id=user.domain_id).all()
    domain_user_ids = [row[0] for row in domain_users]
    if user_id in domain_user_ids:
        # if user belongs to same domain i.e. smartlist belongs to domain
        return True
    return False
