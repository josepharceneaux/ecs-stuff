import json
from push_notification_service.common.error_handling import InternalServerError

PUSH_NOTIFICATION_ERROR = 7000
PUSH_NOTIFICATION_NOT_CREATED = 7001
NO_SMARTLIST_ASSOCIATED = 7002
REQUIRED_FIELDS_MISSING = 7003
INVALID_FREQUENCY = 7004
FAILED_TO_SCHEDULE = 7005

class PushNotificationApiException(InternalServerError):
    error_code = PUSH_NOTIFICATION_ERROR

    def to_dict(self):
        error_dict = super(PushNotificationApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(PushNotificationApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class PushNotificationNotCreated(PushNotificationApiException):
    error_code = PUSH_NOTIFICATION_NOT_CREATED


class NoSmartlistAssociated(PushNotificationApiException):
    error_code = NO_SMARTLIST_ASSOCIATED


class RequiredFieldsMissing(PushNotificationApiException):
    error_code = REQUIRED_FIELDS_MISSING


class InvalidFrequency(PushNotificationApiException):
    error_code = INVALID_FREQUENCY


class FailedToSchedule(PushNotificationApiException):
    error_code = FAILED_TO_SCHEDULE
