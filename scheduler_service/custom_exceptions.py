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
from scheduler_service.custom_error_codes import CODE_TRIGGER_TYPE, CODE_FIELD_REQUIRED, CODE_PENDING, \
    CODE_ALREADY_PAUSED, CODE_ALREADY_RUNNING, CODE_NOTCREATED_TYPE

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
    error_code = CODE_ALREADY_PAUSED


class PendingJobError(SchedulerServiceApiException):
    error_code = CODE_PENDING


class JobAlreadyRunningError(SchedulerServiceApiException):
    error_code = CODE_ALREADY_RUNNING


class FieldRequiredError(SchedulerServiceApiException):
    error_code = CODE_FIELD_REQUIRED


class TriggerTypeError(SchedulerServiceApiException):
    error_code = CODE_TRIGGER_TYPE


class JobNotCreatedError(SchedulerServiceApiException):
    error_code = CODE_NOTCREATED_TYPE
