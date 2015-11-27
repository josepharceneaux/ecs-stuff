import json
from scheduler_service.common.error_handling import InternalServerError


class SchedulerApiException(InternalServerError):
    status_code = 6000

    def to_dict(self):
        error_dict = super(SchedulerApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SchedulerApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class NoJobFound(SchedulerApiException):
    status_code = 6052


class PendingStatus(SchedulerApiException):
    status_code = 6052


class JobAlreadyPaused(SchedulerApiException):
    status_code = 6053


class JobAlreadyRunning(SchedulerApiException):
    status_code = 6054


