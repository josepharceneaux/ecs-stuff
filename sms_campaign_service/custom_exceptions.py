from sms_campaign_service.common.error_handling import TalentError


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class ApiException(TalentError):
    status_code = 500


class SocialNetworkError(ApiException):
    status_code = 452


class EventInputMissing(ApiException):
    status_code = 453


class EventNotCreated(ApiException):
    status_code = 455


class EventNotPublished(ApiException):
    status_code = 456


class EventNotUnpublished(ApiException):
    status_code = 457


class EventLocationNotCreated(ApiException):
    status_code = 458


class TicketsNotCreated(ApiException):
    status_code = 459


class EventNotSaveInDb(ApiException):
    status_code = 460


class UserCredentialsNotFound(ApiException):
    status_code = 461


class SocialNetworkNotImplemented(ApiException):
    status_code = 462


class InvalidAccessToken(ApiException):
    status_code = 463


class InvalidDatetime(ApiException):
    status_code = 464


class VenueNotFound(ApiException):
    status_code = 465


class AccessTokenHasExpired(ApiException):
    status_code = 466


class NoUserFound(ApiException):
    status_code = 467


class MissingFieldsInUserCredentials(ApiException):
    status_code = 468


class EventNotFound(ApiException):
    status_code = 469


class ProductNotFound(ApiException):
    status_code = 470
