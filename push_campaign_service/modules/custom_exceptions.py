# TODO comment at the tope of the file
import json
import push_campaign_service.common.error_handling

PUSH_NOTIFICATION_ERROR = 7000
PUSH_NOTIFICATION_NOT_CREATED = 7001
NO_SMARTLIST_ASSOCIATED = 7002
REQUIRED_FIELDS_MISSING = 7003
INVALID_FREQUENCY = 7004
FAILED_TO_SCHEDULE = 7005
INVALID_FIELD = 7006
NO_CANDIDATE_ASSOCIATED = 7007


class PushNotificationApiException(push_campaign_service.common.error_handling.InternalServerError):
    error_code = PUSH_NOTIFICATION_ERROR

    def to_dict(self):
        error_dict = super(PushNotificationApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(PushNotificationApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)
