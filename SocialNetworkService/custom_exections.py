
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

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class EventNotCreated(ApiException):
    status_code = 441


class SocialNetworkError(ApiException):
    status_code = 441


class EventInputMissing(ApiException):
    status_code = 442


class EventNotSaved(ApiException):
    status_code = 443


class EventNotCreated(ApiException):
    status_code = 444


class EventNotPublished(ApiException):
    status_code = 445


class EventNotUnpublished(ApiException):
    status_code = 446


class EventLocationNotCreated(Exception):
    status_code = 447


class TicketsNotCreated(Exception):
    status_code = 448


class EventNotSaveInDb(Exception):
    status_code = 449


class UserCredentialsNotFound(Exception):
    status_code = 450


class SocialNetworkNotImplemented(Exception):
    status_code = 451


class InvalidAccessToken(Exception):
    status_code = 452


class InvalidDatetime(Exception):
    status_code = 453

