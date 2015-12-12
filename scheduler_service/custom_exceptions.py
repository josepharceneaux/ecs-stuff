"""
Custom exceptions to throw error code when internal server error occurs.
These exceptions are raised when:
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
    CODE_ALREADY_PAUSED = 6053
    CODE_PENDING = 6052
    CODE_ALREADY_RUNNING = 6054
    CODE_FIELD_REQUIRED = 6055
    CODE_TRIGGER_TYPE = 6056
    CODE_NOT_CREATED_TYPE = 6057

    def to_dict(self):
        error_dict = super(SchedulerServiceApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(SchedulerServiceApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class JobAlreadyPausedError(SchedulerServiceApiException):
    error_code = SchedulerServiceApiException.CODE_ALREADY_PAUSED


class PendingJobError(SchedulerServiceApiException):
    error_code = SchedulerServiceApiException.CODE_PENDING


class JobAlreadyRunningError(SchedulerServiceApiException):
    error_code = SchedulerServiceApiException.CODE_ALREADY_RUNNING


class FieldRequiredError(SchedulerServiceApiException):
    error_code = SchedulerServiceApiException.CODE_FIELD_REQUIRED


class TriggerTypeError(SchedulerServiceApiException):
    error_code = SchedulerServiceApiException.CODE_TRIGGER_TYPE


class JobNotCreatedError(SchedulerServiceApiException):
    error_code = SchedulerServiceApiException.CODE_NOT_CREATED_TYPE
