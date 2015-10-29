import json
from common.error_handling import TalentError, InternalServerError


class ApiException(InternalServerError):
    status_code = 500

    def to_dict(self):
        error_dict = super(ApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(ApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class SocialNetworkError(ApiException):
    status_code = 4052


class EventInputMissing(ApiException):
    status_code = 4053


class EventNotCreated(ApiException):
    status_code = 4055


class EventNotPublished(ApiException):
    status_code = 4056


class EventNotUnpublished(ApiException):
    status_code = 4057


class EventLocationNotCreated(ApiException):
    status_code = 4058


class TicketsNotCreated(ApiException):
    status_code = 4059


class EventNotSaveInDb(ApiException):
    status_code = 460


class UserCredentialsNotFound(ApiException):
    status_code = 4061


class SocialNetworkNotImplemented(ApiException):
    status_code = 4062


class InvalidAccessToken(ApiException):
    status_code = 4063


class InvalidDatetime(ApiException):
    status_code = 4064


class VenueNotFound(ApiException):
    status_code = 4065


class AccessTokenHasExpired(ApiException):
    status_code = 4066


class NoUserFound(ApiException):
    status_code = 4067


class MissingFieldsInUserCredentials(ApiException):
    status_code = 4068


class EventNotFound(ApiException):
    status_code = 4069


class ProductNotFound(ApiException):
    status_code = 4070
