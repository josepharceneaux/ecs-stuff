"""
Decorators to be used in the Resume Parsing Service.
"""
__author__ = 'erik@getTalent.com'
# STD Lib
from functools import wraps
# Module Specific
from flask import current_app
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.common.error_handling import InternalServerError, TalentError
from resume_parsing_service.common.utils.talent_s3 import boto3_put


def upload_failed_IO(f):
    """Catch all decorator for handling unexpected errors in the Resume Parsing Service.
    If an uncaught exception occurs the resume will be uploaded to the s3 bucket associated
    with the environment in the FailedResume bucket.
    :param function f:
    :rtype function:
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, TalentError):
                fileIO = args[0]
                key = args[1]
                logger.exception('ResumeParsingService::UncaughtError::upload_failed_IO Key {} Exception'.format(key, e.message))
                boto3_put(fileIO.getvalue(), current_app.config['S3_BUCKET_NAME'], key, 'FailedResumes')
                fileIO.close()
                raise InternalServerError(
                    error_message=error_constants.RESUME_UNCAUGHT_EXCEPTION['message'],
                    error_code=error_constants.RESUME_UNCAUGHT_EXCEPTION['code']
                )

            else:
                raise e
    return wrapper
