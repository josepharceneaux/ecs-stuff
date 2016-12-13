"""
File contains helper-functions that will be used for candidate's data
"""

from ..error_handling import NotFoundError, ForbiddenError
from ..models.candidate import Candidate
from ..utils.auth_utils import has_role


def get_candidate_if_validated(user, candidate_id, user_role='TALENT_ADMIN'):
    """
    Function will return candidate if:
        1. it exists
        2. not hidden, and
        3. belongs to user's domain
    :type user: User
    :type candidate_id: int | long
    :rtype: Candidate
    """
    candidate = Candidate.get(candidate_id)
    if not candidate:
        raise NotFoundError(error_message='Candidate not found: {}'.format(candidate_id))
        # TODO: error_code=custom_error.CANDIDATE_NOT_FOUND

    if candidate.is_archived:
        raise NotFoundError(error_message='Candidate not found: {}'.format(candidate_id))
        # TODO: error_code=custom_error.CANDIDATE_IS_HIDDEN

    if has_role(user, user_role) and candidate.user.domain_id != user.domain_id:
        raise ForbiddenError("Not authorized")
        # TODO: custom_error.CANDIDATE_FORBIDDEN

    return candidate


def replace_tabs_with_spaces(obj):
    """
    Function will recursively replace all \t (tabs) with spaces
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if value:
                if isinstance(value, list):
                    for i in xrange(len(value)):
                        value[i] = replace_tabs_with_spaces(value[i])
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if v and isinstance(v, basestring):
                            value[k] = v.replace("\t", " ")
                else:
                    obj[key] = value.replace("\t", " ") if isinstance(value, basestring) else value
    else:
        pass
    return obj
