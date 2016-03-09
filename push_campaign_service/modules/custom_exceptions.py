"""
This module contains custom exceptions and error codes for Push Campaign Service.
"""
import json
import push_campaign_service.common.error_handling


class PCSErrorCodes(object):
    """
    PCS -> Push Campaign Service
    This class contains error codes that are specific to push campaign service.
    """
    PUSH_NOTIFICATION_ERROR = 7000
    PUSH_NOTIFICATION_NOT_CREATED = 7001
    INVALID_FREQUENCY = 7002
    FAILED_TO_SCHEDULE = 7003
    INVALID_FIELD = 7004


class PushNotificationApiException(push_campaign_service.common.error_handling.InternalServerError):
    error_code = PCSErrorCodes.PUSH_NOTIFICATION_ERROR

    def to_dict(self):
        error_dict = super(PushNotificationApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(PushNotificationApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)
