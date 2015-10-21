from candidate_service.common.models.candidate import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User


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
    pass
