# pylint: disable=wrong-import-position, fixme
# Standard library
from time import sleep
from time import time
import base64
import json
# Third Party/Framework Specific.
from bs4 import BeautifulSoup
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.app.views.utils import send_abbyy_email
from resume_parsing_service.common.error_handling import ForbiddenError
from resume_parsing_service.common.error_handling import InternalServerError


ABBY_OCR_API_AUTH_TUPLE = ('gettalent', 'lfnJdQNWyevJtg7diX7ot0je')
ABBY_URL = 'http://cloud.ocrsdk.com/processImage'
GOOGLE_API_KEY = "AIzaSyD4i4j-8C5jLvQJeJnLmoFW6boGkUhxSuw"
GOOGLE_CLOUD_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def google_vision_ocr(file_string_io):
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
        google_request = requests.post("{}?key={}".format(GOOGLE_CLOUD_VISION_URL, GOOGLE_API_KEY),
                                       json.dumps(req_data),
                                       timeout=20,
                                       headers={'content-type': 'application/json'})
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("google_vision_ocr: Could not reach Google API")
        raise InternalServerError("Unable to reach Google API in resume OCR")

    if google_request.status_code is not requests.codes.ok:
        logger.info('google_vision_ocr: Google API response error with headers: {} content{}'.format(
            google_request.headers, google_request.content))
        raise InternalServerError('Error in response from candidate service during creation')

    ocr_results = json.loads(google_request.content)
    # Check for errors since even a 'bad' request gives a 200 response. And use Abby in that event.
    google_api_errors = ocr_results['responses'][0].get('error')

    if google_api_errors:
        logger.warn('Error parsing with Google Vision. Trying Abby parse. Param: {}'.format(file_string_io))
        return abbyy_ocr_image(file_string_io)

    logger.info("google_vision_ocr: Google API response JSON: %s", ocr_results)

    return ocr_results['responses'][0]['textAnnotations'][0]['description']


def abbyy_ocr_image(img_file_obj, export_format='pdfSearchable'):
    """
    Posts the image to Abby OCR API, then keeps pinging to check if it's done. Quits if not done in
    certain number of tries.
    :param cStringIO.StringIO img_file_obj: File initially posted to the resume parsing service.
    :param string export_format: Abby OCR param.
    :return: Image file OCR'd in desired format.
    """

    # Post the image to Abby
    files = {'file': img_file_obj}
    response = requests.post(ABBY_URL,
                             auth=ABBY_OCR_API_AUTH_TUPLE,
                             files=files,
                             data={'profile': 'documentConversion', 'exportFormat': export_format}
                             )

    if response.status_code != 200:
        raise ForbiddenError('Error connecting to Abby OCR instance.')

    xml = BeautifulSoup(response.text, 'lxml')
    logger.info("ocr_image() - Abby response to processImage: %s", response.text)

    task = xml.response.task
    task_id = task['id']

    if task.get('status') == 'NotEnoughCredits':
        send_abbyy_email()
        raise InternalServerError(error_message='Error with image/pdf to text conversion.')

    estimated_processing_time = int(xml.response.task['estimatedprocessingtime'])

    if task.get('status') != 'Queued':
        logger.error('ocr_image() - Non queued status in ABBY OCR')

    # Keep pinging Abby to get task status. Quit if tried too many times
    ocr_url = ''
    num_tries = 0
    max_num_tries = 6

    while not ocr_url:
        sleep(estimated_processing_time)

        response = requests.get('http://cloud.ocrsdk.com/getTaskStatus',
                                params=dict(taskId=task_id), auth=ABBY_OCR_API_AUTH_TUPLE)
        xml = BeautifulSoup(response.text, 'lxml')
        ocr_url = xml.response.task.get('resulturl')
        logger.info("ocr_image() - Abby response to getTaskStatus: %s", response.text)

        if not ocr_url:
            if num_tries > max_num_tries:
                logger.error('OCR took > {} tries to process image'.format(
                    max_num_tries))
                raise Exception('OCR took > {} tries to process image'.format(max_num_tries))
            # If not done in originally estimated processing time, wait 2 more seconds.
            estimated_processing_time = 2
            num_tries += 1
            continue

    if response.status_code == requests.codes.ok:
        start_time = time()
        response = requests.get(ocr_url)
        logger.info(
            "Benchmark: ocr_image: requests.get(%s) took %ss to download resume",
            ocr_url, time() - start_time
        )
        return response.content

    else:
        return 0
