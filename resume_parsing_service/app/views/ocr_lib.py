"""Code for use with Google Vision API and Abbyy OCR."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position, fixme, import-error
# Standard library
from time import sleep
from time import time
import base64
import json
# Third Party/Framework Specific.
from bs4 import BeautifulSoup
from contracts import contract
from flask import current_app
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.app.views.utils import send_abbyy_email
from resume_parsing_service.common.error_handling import ForbiddenError
from resume_parsing_service.common.error_handling import InternalServerError


ABBY_OCR_API_AUTH_TUPLE = ('gettalent', 'lfnJdQNWyevJtg7diX7ot0je')
ABBY_URL = 'http://cloud.ocrsdk.com/processImage'


@contract
def google_vision_ocr(file_string_io, timeout=20):
    """
    Utilizes Google Vision API to OCR image with Abbyy as a fallback.
    Root Docs: https://cloud.google.com/vision/docs/
    Specific JSON responses:
        https://cloud.google.com/vision/reference/rest/v1/images/annotate#annotateimageresponse
        https://cloud.google.com/vision/reference/rest/v1/images/annotate#entityannotation
    :param cStringIO file_string_io: Resume file in memory.
    :return: The first `description` key from the first `textAnnotations` item in the OCR results.
    :rtype: string
    """
    b64_string = base64.b64encode(file_string_io.getvalue())
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
                                        timeout=timeout,
                                        headers={'content-type': 'application/json'}, verify=True)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout)as exc:
        logger.exception("Could not reach Google API")
        print 'Message - '.format(exc)
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
        return abbyy_ocr_image(file_string_io)

    logger.info("google_vision_ocr: Google API response JSON: %s", ocr_results)

    text_annotations = ocr_results['responses'][0].get('textAnnotations')

    if text_annotations:
        return text_annotations[0].get('description', u'')
    else:
        return u''


@contract
def abbyy_ocr_image(img_file_obj, export_format='pdfSearchable'):
    """
    Posts the image to Abby OCR API, then keeps pinging to check if it's done. Quits if not done in
    certain number of tries.
    :param cStringIO img_file_obj: (Image) File posted to the resume parsing service.
    :param string export_format: Abby OCR param.
    :return: Image file OCR text parsed from Abbyy.
    :rtype string:
    """

    # Post the image to Abby
    img_file_obj.seek(0)
    files = {'file': img_file_obj}
    abbyy_response = requests.post(ABBY_URL, auth=ABBY_OCR_API_AUTH_TUPLE, files=files,
                                   data={'profile': 'documentConversion', 'exportFormat': export_format})

    if abbyy_response.status_code != 200:
        raise ForbiddenError(
            error_message=error_constants.ABBYY_UNABLE_TO_QUEUE['message'],
            error_code=error_constants.ABBYY_UNABLE_TO_QUEUE['code']
        )

    xml = BeautifulSoup(abbyy_response.text, 'lxml')
    logger.info("ocr_image() - Abby response to processImage: %s", abbyy_response.text)

    task = xml.response.task
    task_id = task['id']

    if task.get('status') == 'NotEnoughCredits':
        send_abbyy_email()
        raise InternalServerError(
            error_message=error_constants.ABBYY_CREDITS['message'],
            error_code=error_constants.ABBYY_CREDITS['code']
        )

    estimated_processing_time = int(xml.response.task['estimatedprocessingtime'])

    if task.get('status') != 'Queued':
        logger.error('ocr_image() - Non queued status in ABBY OCR')

    # Keep pinging Abby to get task status. Quit if tried too many times
    ocr_url = ''
    num_tries = 0
    max_num_tries = 6

    while not ocr_url:
        sleep(estimated_processing_time)

        status_response = requests.get('http://cloud.ocrsdk.com/getTaskStatus',
                                       params=dict(taskId=task_id), auth=ABBY_OCR_API_AUTH_TUPLE)
        xml = BeautifulSoup(status_response.text, 'lxml')
        ocr_url = xml.response.task.get('resulturl')
        logger.info("ocr_image() - Abby response to getTaskStatus: %s", status_response.text)

        if not ocr_url:
            if num_tries > max_num_tries:
                logger.error('OCR took > {} tries to process image'.format(
                    max_num_tries))
                raise InternalServerError(
                    error_message=error_constants.ABBYY_MAX_ATTEMPTS['message'],
                    error_code=error_constants.ABBYY_MAX_ATTEMPTS['code']
                )

            # If not done in originally estimated processing time, wait 2 more seconds.
            estimated_processing_time = 2
            num_tries += 1
            continue

    if status_response.status_code == requests.codes.ok:
        start_time = time()
        status_response = requests.get(ocr_url)
        logger.info(
            "Benchmark: ocr_image: requests.get(%s) took %ss to download resume",
            ocr_url, time() - start_time
        )
        return status_response.content

    else:
        raise InternalServerError(
            error_message=error_constants.ABBYY_UNAVAILABLE['message'],
            error_code=error_constants.ABBYY_UNAVAILABLE['code']
        )
