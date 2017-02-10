"""Code for use with Google Vision API and Abbyy OCR."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position, fixme, import-error
# Standard library
import json
import re
# Third Party/Framework Specific.
from flask import current_app
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.common.error_handling import InternalServerError


def ocr_image(img_file_obj, filename_str):
    API_KEY = current_app.config['OCR_API_KEY']
    OCR_URL = current_app.config['OCR_URL']
    img_file_obj.seek(0)

    payload = {
        'isOverlayRequired': False,
        'apikey': API_KEY,
        'language': 'eng',
    }

    try:
        ocr_response = requests.post(OCR_URL, files={filename_str: img_file_obj}, data=payload)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                logger.error("Could not reach OCRSpace.")
                raise InternalServerError(
                    error_message=error_constants.OCR_SPACE_UNAVAILABLE['message'],
                    error_code=error_constants.OCR_SPACE_UNAVAILABLE['code']
                )

    decoded_ocr_response = ocr_response.content.decode('utf8')
    json_ocr_response = json.loads(decoded_ocr_response)

    logger.info('ResumeParsingService::Info::OCRSpace response: {}'.format(json_ocr_response))
    ocr_confidence = json_ocr_response.get('OCRExitCode')

    if ocr_confidence in (3, 4):
        logger.error('ResumeParsingService::Error::Error in OCR Response')
        raise InternalServerError(
            error_message=error_constants.OCR_SPACE_ERROR['message'],
            error_code=error_constants.OCR_SPACE_ERROR['code']
        )

    else:
        logger.info('ResumeParsingService::Info::OCR Score {}'.format(ocr_confidence))

    results =  ''.join(result.get('ParsedText') for result in json_ocr_response.get('ParsedResults'))
    unicode_subbed_results = re.sub(u'[^\x00-\x7F]+', ' ', results)
    try:
        logger.info('ResumeParsingService::Info::OCRSpace ParsedText: {}'.format(unicode_subbed_results))
    except Exception as e:
        logger.error('ResumeParsingService::Error::OCRSpace couldn\'t log results')
    return unicode_subbed_results
