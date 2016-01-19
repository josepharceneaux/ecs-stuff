import json
import social_network_service.common.error_handling


class SocialNetworkApiException(social_network_service.common.error_handling.InternalServerError):
    status_code = 4000

    def to_dict(self):
        error_dict = super(SocialNetworkApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SocialNetworkApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class SocialNetworkError(SocialNetworkApiException):
    status_code = 4052


class EventInputMissing(SocialNetworkApiException):
    status_code = 4053


class EventOrganizerNotFound(SocialNetworkApiException):
    status_code = 4054


class EventNotCreated(SocialNetworkApiException):
    status_code = 4055


class EventNotPublished(SocialNetworkApiException):
    status_code = 4056


class EventNotUnpublished(SocialNetworkApiException):
    status_code = 4057


class EventLocationNotCreated(SocialNetworkApiException):
    status_code = 4058


class TicketsNotCreated(SocialNetworkApiException):
    status_code = 4059


class EventNotSaveInDb(SocialNetworkApiException):
    status_code = 4060


class UserCredentialsNotFound(SocialNetworkApiException):
    status_code = 4061


class SocialNetworkNotImplemented(SocialNetworkApiException):
    status_code = 4062


class InvalidAccessToken(SocialNetworkApiException):
    status_code = 4063


class InvalidDatetime(SocialNetworkApiException):
    status_code = 4064


class VenueNotFound(SocialNetworkApiException):
    status_code = 4065


class AccessTokenHasExpired(SocialNetworkApiException):
    status_code = 4066


class NoUserFound(SocialNetworkApiException):
    status_code = 4067


class MissingFieldsInUserCredentials(SocialNetworkApiException):
    status_code = 4068


class EventNotFound(SocialNetworkApiException):
    status_code = 4069


class ProductNotFound(SocialNetworkApiException):
    status_code = 4070
