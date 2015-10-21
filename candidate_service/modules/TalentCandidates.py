from candidate_service.common.models.candidate import db
from candidate_service.common.models.candidate import (
    Candidate, EmailLabel, CandidateEmail
)
from candidate_service.common.models.user import User
from candidate_service.app import logger


def does_candidate_belong_to_user(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    """
    candidate_row = db.session.query(Candidate).join(User).filter(
        Candidate.id == candidate_id, Candidate.user_id == user_row.id,
        User.domain_id == user_row.domain_id
    ).first()

    return True if candidate_row else False


def fetch_candidate_info(candidate_id, fields=None):
    """
    Fetched for candidate object via candidate's id
    :type       candidate_id: int
    :type       fields: None | str

    :return:    Candidate dict
    :rtype:     dict[str, T]
    """
    candidate = db.session.query(Candidate).get(candidate_id)
    if not candidate:
        logger.error('Candidate not found, candidate_id: %s', candidate_id)
        return None

    get_all_fields = fields is None  # if fields is None, then get ALL the fields

    full_name = None
    if get_all_fields or 'full_name' in fields:
        first_name = candidate.first_name or ''
        last_name = candidate.last_name or ''
        full_name = (first_name.capitalize() + ' ' + last_name.capitalize()).strip()

    email = None
    if get_all_fields or 'emails' in fields:
        email = email_label_and_address(candidate_id=candidate_id)

    return_dict = {
        'id': candidate_id,
        'full_name': full_name,
        'emails': email
    }

    # Remove all values that are empty
    return_dict = dict((k, v) for k, v in return_dict.iteritems() if v is not None)
    return return_dict


def email_label_and_address(candidate_id):
    return [{
        'label': db.session.query(EmailLabel).get(email.email_label_id).description,
        'address': email.address
    } for email in db.session.query(CandidateEmail).filter_by(candidate_id=candidate_id)]
