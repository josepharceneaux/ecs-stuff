"""
Decorators to be used in the Resume Parsing Service.
"""
__author__ = 'erik@getTalent.com'
# STD Lib
from functools import wraps
# Module Specific
from flask import current_app
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InternalServerError
from resume_parsing_service.common.utils.talent_s3 import boto3_put


def upload_failed_IO(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception('Uncaught error occured during Resume Processing: {}'.format(e.message))
            fileIO = args[0]
            key = args[1]
            fileIO.seek(0)
            boto3_put(fileIO.read(), current_app.config['S3_BUCKET_NAME'], key, 'FailedResumes')
            raise InternalServerError(error_message='An error has occured during this process. The development team has been notified.')
    return wrapper
