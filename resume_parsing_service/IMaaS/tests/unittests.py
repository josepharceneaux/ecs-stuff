"""
Unittests for Image Magick as a Service platform.

Tests ensure that we can handle multiple types of PDF files and that the desired quantity of outout
is returned.

IMaaS will 'chunk' pdf pages into multipl pictures (1-3 pages per picture)

Examples:
    *******************************
    * page ct * pictures returned *
    *******************************
    * 1       * 1                 *
    * 2       * 1                 *
    * 3       * 1                 *
    * 4       * 2 (3, 1)          *
    * 5       * 2 (3, 2)          *
    * 6       * 2 (3, 3)          *
    *******************************
"""
import base64
import os

from resume_parsing_service.IMaaS.lambda_handlers import convert_pdf_to_png


CURRENT_DIR = os.path.dirname(__file__)
RESUMES_ROOT = os.path.join(CURRENT_DIR, 'files/')

PREFIXES_COUNTS = [
    {'input': 'one', 'output': 1}, {'input': 'two', 'output': 1}, {'input': 'three', 'output': 1},
    {'input': 'four', 'output': 2}, {'input': 'five', 'output': 2}, {'input': 'six', 'output': 2}
]

def test_picture_count_returned():
    """
    Tests that we receive the desired quantity of images depending on the PDF page count.
    """

    for test_case in PREFIXES_COUNTS:
        filename = test_case['input'] + '_page.pdf'
        encoded = open_and_encode_file(filename)
        test_payload = {'pdf_bin': encoded}

        # Lambda handlers have two parameters and in our use case the second is unused but we must
        # still pass something.
        result = convert_pdf_to_png(test_payload, None)
        qty = len(result['img_data'])
        assert qty == test_case['output']


def open_and_encode_file(filename):
    with open(RESUMES_ROOT + filename) as infile:
        data = infile.read()

    return base64.b64encode(data)


def test_required_key():
    """
    Tests that the 'pdf_bin' key is required by the function.
    """
    payload = {'bad_key': None}
    result = convert_pdf_to_png(payload, None)
    assert 'error' in result
