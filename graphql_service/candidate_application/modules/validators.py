"""

"""
from graphql_service.common.models.user import User
from graphql_service.common.models.candidate import Candidate
from graphql_service.common.utils.auth_utils import has_role


def is_candidate_validated(user, candidate_id, user_role='TALENT_ADMIN'):
    """
    Function will return true if candidate is 1. found & 2. validated per user's permission(s)
    :type user: User
    :type candidate_id: int | long
    :type user_role: str
    :rtype: bool
    """
    candidate = Candidate.get(candidate_id)
    if not candidate:
        return False

    # Return False if user is not authorized to get candidate
    if has_role(user=user, role=user_role) and candidate.user.domain_id != user.domain_id:
        return False

    return True
