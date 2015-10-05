
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


class ApiException(Exception):
    status_code = 500

    def __init__(self, message, detail=None, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        self.detail = detail
        if status_code:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        if self.detail:
            rv['detail'] = self.detail
        return rv


class SocialNetworkError(ApiException):
    status_code = 452


class EventInputMissing(ApiException):
    status_code = 453


class EventNotSaveInDb(ApiException):
    status_code = 460


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
