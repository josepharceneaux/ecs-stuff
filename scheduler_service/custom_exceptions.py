"""
TODO comment here
"""
import json
import scheduler_service.common.error_handling

__author__ = 'saad'


class SchedulerServiceApiException(scheduler_service.common.error_handling.InternalServerError):
    status_code = 6000

    def to_dict(self):
        error_dict = super(SchedulerServiceApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SchedulerServiceApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class JobAlreadyPaused(SchedulerServiceApiException):
    status_code = 6053


class PendingStatus(SchedulerServiceApiException):
    status_code = 6052


class JobAlreadyRunning(SchedulerServiceApiException):
    status_code = 6054


class NoJobFound(SchedulerServiceApiException):
    status_code = 6050

