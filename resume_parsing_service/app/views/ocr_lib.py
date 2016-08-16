"""Code for use with Google Vision API and Abbyy OCR."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position, fixme, import-error
# Standard library
import base64
import json
# Third Party/Framework Specific.
from contracts import contract
from flask import current_app
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.common.error_handling import InternalServerError


@contract
def google_vision_ocr(file_array):
    """
    Utilizes Google Vision API to OCR image with Abbyy as a fallback.
    Root Docs: https://cloud.google.com/vision/docs/
    Specific JSON responses:
        https://cloud.google.com/vision/reference/rest/v1/images/annotate#annotateimageresponse
        https://cloud.google.com/vision/reference/rest/v1/images/annotate#entityannotation
    :param list file_array: List of resume files in memory.
    :return: The first `description` key from the first `textAnnotations` item in the OCR results.
    :rtype: string
    """
    results = u''
    for f in file_array:
        b64_string = base64.b64encode(f.getvalue())
        req_data = {
            "requests": [
                {
                    "image": {
                        "content": b64_string
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION",
                            "maxResults": 1
                        }
                    ]
                }
            ]
        }

        try:
            google_response = requests.post("{}?key={}".format(current_app.config['GOOGLE_CLOUD_VISION_URL'],
                                                               current_app.config['GOOGLE_API_KEY']),
                                            json.dumps(req_data),
                                            timeout=20,
                                            headers={'content-type': 'application/json'})
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.exception("Could not reach Google API")
            raise InternalServerError(
                error_message=error_constants.GOOGLE_OCR_UNAVAILABLE['message'],
                error_code=error_constants.GOOGLE_OCR_UNAVAILABLE['code'],
            )

        if google_response.status_code is not requests.codes.ok:
            logger.info('google_vision_ocr: Google API response error with headers: {} content{}'.format(
                google_response.headers, google_response.content))
            raise InternalServerError(
                error_message=error_constants.GOOGLE_OCR_ERROR['message'],
                error_code=error_constants.GOOGLE_OCR_ERROR['code'],
            )

        ocr_results = json.loads(google_response.content)
        # Check for errors since even a 'bad' request gives a 200 response. And use Abby in that event.
        google_api_errors = ocr_results['responses'][0].get('error')

        if google_api_errors:
            logger.warn('Error parsing with Google Vision. Trying Abby parse. Errors: {}'.format(google_api_errors))
            raise InternalServerError('Nice Message Needed.')

        logger.info("google_vision_ocr: Google API response JSON: %s", ocr_results)

        text_annotations = ocr_results['responses'][0].get('textAnnotations')

        if text_annotations:
            results += text_annotations[0].get('description', u'') + '\n'
        else:
            results += u'\n'

    return results