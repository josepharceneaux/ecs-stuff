from candidate_service.candidate_app import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User
from candidate_service.common.models.misc import (AreaOfInterest, CustomField)
from candidate_service.common.models.email_marketing import EmailCampaign


def does_candidate_belong_to_user(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    :rtype: bool
    """
    candidate_row = db.session.query(Candidate).join(User).filter(
        Candidate.id == candidate_id, Candidate.user_id == user_row.id,
        User.domain_id == user_row.domain_id
    ).first()

    return True if candidate_row else False


def is_custom_field_authorized(user_domain_id, custom_field_ids):
    """
    :type   user_domain_id:   int
    :type   custom_field_ids: [int]
    :rtype: bool
    """
    exists = db.session.query(CustomField).\
                 filter(CustomField.id.in_(custom_field_ids),
                        CustomField.domain_id != user_domain_id).count() == 0
    return exists


def is_area_of_interest_authorized(user_domain_id, area_of_interest_ids):
    """
    :type   user_domain_id:       int
    :type   area_of_interest_ids: [int]
    :rtype: bool
    """
    exists = db.session.query(AreaOfInterest).\
                 filter(AreaOfInterest.id.in_(area_of_interest_ids),
                        AreaOfInterest.domain_id != user_domain_id).count() == 0
    return exists


def does_email_campaign_belong_to_domain(user_row):
    """ Function retrieves all email campaigns belonging to user's domain
    :rtype: bool
    """
    email_campaing_rows = db.session.query(EmailCampaign).join(User).\
        filter(User.domain_id == user_row.domain_id).first()

    return True if email_campaing_rows else False

