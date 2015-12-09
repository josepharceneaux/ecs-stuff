"""
Custom exceptions to throw error code when internal server error occurred
raise exception when
- job is already running
- paused
- any mandatory field missing in post request
- Trigger is not correct when scheduling job
"""
import json
import scheduler_service.common.error_handling

__author__ = 'saad'


class SchedulerServiceApiException(scheduler_service.common.error_handling.InternalServerError):
    error_code = 6000

    def to_dict(self):
        error_dict = super(SchedulerServiceApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(SchedulerServiceApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class JobAlreadyPausedError(SchedulerServiceApiException):
    error_code = 6053


class PendingJobError(SchedulerServiceApiException):
    error_code = 6052


class JobAlreadyRunningError(SchedulerServiceApiException):
    error_code = 6054


class FieldRequiredError(SchedulerServiceApiException):
    error_code = 6055


class TriggerTypeError(SchedulerServiceApiException):
    error_code = 6056
