"""
Decorators to be used in the Resume Parsing Service.
"""
__author__ = 'erik@getTalent.com'
# STD Lib
from functools import wraps
# Module Specific
from flask import current_app
from resume_parsing_service.app import logger
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
                logger.exception('Uncaught error occured during Resume Processing: {}'.format(e.message))
                fileIO = args[0]
                key = args[1]
                fileIO.seek(0)
                boto3_put(fileIO.read(), current_app.config['S3_BUCKET_NAME'], key, 'FailedResumes')
                raise InternalServerError(error_message='An error has occured during this process. The development team has been notified.')

            else:
                raise e
    return wrapper
