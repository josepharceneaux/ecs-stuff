from candidate_service.common.error_handling import (
    TalentError, NotFoundError, ForbiddenError, InvalidUsage
)


class CandidateApiException(TalentError):
    status_code = 3000

    def to_dict(self):
        error_dict = super(CandidateApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

# ***** NotFound Errors *****
class CandidateNotFound(CandidateApiException, NotFoundError):
    status_code = 3010


class CandidateIsHidden(CandidateApiException, NotFoundError):
    status_code = 3011

# ***** Forbidden Errors *****
class CandidateForbidden(CandidateApiException, ForbiddenError):
    status_code = 3030

class CustomFieldForbidden(CandidateApiException, ForbiddenError):
    status_code = 3031

class AOIForbidden(CandidateApiException, ForbiddenError):
    status_code = 3032


# ***** Invalid Errors *****
class InvalidInput(CandidateApiException, InvalidUsage):
    status_code = 3050

class InvalidEmail(CandidateApiException, InvalidUsage):
    status_code = 3051

class CandidateAlreadyExists(CandidateApiException, InvalidUsage):
    status_code = 3052

class RequiredFieldError(CandidateApiException, InvalidUsage):
    status_code = 3053
