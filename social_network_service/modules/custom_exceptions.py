import json
import social_network_service.common.error_handling


class SocialNetworkApiExceptionServer(social_network_service.common.error_handling.InternalServerError):
    """
    Custom exception in case of 500 internal server error
    """
    status_code = 4000

    def to_dict(self):
        error_dict = super(SocialNetworkApiExceptionServer, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SocialNetworkApiExceptionServer, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class SocialNetworkApiInvalidException(social_network_service.common.error_handling.InvalidUsage):
    """
    Custom exception in case of invalid usage of api
    """
    status_code = 4000

    def to_dict(self):
        error_dict = super(SocialNetworkApiInvalidException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SocialNetworkApiInvalidException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class SocialNetworkApiNotFoundException(social_network_service.common.error_handling.ResourceNotFound):
    """
    Custom exception in case of resource not found
    """
    status_code = 4000

    def to_dict(self):
        error_dict = super(SocialNetworkApiNotFoundException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SocialNetworkApiNotFoundException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class SocialNetworkError(SocialNetworkApiExceptionServer):
    status_code = 4052


class EventInputMissing(SocialNetworkApiInvalidException):
    status_code = 4053


class EventOrganizerNotFound(SocialNetworkApiNotFoundException):
    status_code = 4054


class EventNotCreated(SocialNetworkApiExceptionServer):
    status_code = 4055


class EventNotPublished(SocialNetworkApiExceptionServer):
    status_code = 4056


class EventNotUnpublished(SocialNetworkApiExceptionServer):
    status_code = 4057


class EventLocationNotCreated(SocialNetworkApiExceptionServer):
    status_code = 4058


class TicketsNotCreated(SocialNetworkApiExceptionServer):
    status_code = 4059


class EventNotSaveInDb(SocialNetworkApiExceptionServer):
    status_code = 4060


class UserCredentialsNotFound(SocialNetworkApiNotFoundException):
    status_code = 4061


class SocialNetworkNotImplemented(SocialNetworkApiExceptionServer):
    status_code = 4062


class InvalidAccessToken(SocialNetworkApiInvalidException):
    status_code = 4063


class InvalidDatetime(SocialNetworkApiInvalidException):
    status_code = 4064


class VenueNotFound(SocialNetworkApiNotFoundException):
    status_code = 4065


class AccessTokenHasExpired(SocialNetworkApiExceptionServer):
    status_code = 4066


class NoUserFound(SocialNetworkApiNotFoundException):
    status_code = 4067


class MissingFieldsInUserCredentials(SocialNetworkApiInvalidException):
    status_code = 4068


class EventNotFound(SocialNetworkApiNotFoundException):
    status_code = 4069


class ProductNotFound(SocialNetworkApiNotFoundException):
    status_code = 4070


class HitLimitReached(SocialNetworkApiExceptionServer):
    status_code = 4071