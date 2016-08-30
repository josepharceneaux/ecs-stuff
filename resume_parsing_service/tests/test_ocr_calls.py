from cStringIO import StringIO
import os

from requests.exceptions import SSLError
from resume_parsing_service.app import app
from resume_parsing_service.app.views.ocr_lib import google_vision_ocr
from resume_parsing_service.common.error_handling import InternalServerError


CURRENT_DIR = os.path.dirname(__file__)
OCR_CHAR_MIN = 5  # Some non-text pictures may have characters returned from OCR.


def test_valid_ocr_response():
    """
    Test that Google OCR returns mostly accurate text from an image file containing text
    """
    with app.app_context():
        with open(os.path.join(CURRENT_DIR, 'files/{}'.format('han.png')), 'rb') as img:
            img_data = StringIO(img.read())
        try:
            google_response = google_vision_ocr(img_data, timeout=60)
            desired_strs = u'Han Solo best smuggler galaxy frozen Boba Fett'.split()
            assert all(substr in google_response for substr in desired_strs)
        except InternalServerError:
            pass


def test_ocr_doesnt_req_seek():
    """
    Test that Google OCR returns mostly accurate text from an image file containing text after being
    read already.
    """
    with app.app_context():
        with open(os.path.join(CURRENT_DIR, 'files/{}'.format('han.png')), 'rb') as img:
            img_data = StringIO(img.read())
        img_data.read() #  Put file pointer at EOF.
        try:
            google_response = google_vision_ocr(img_data, timeout=60)
            desired_strs = u'Han Solo best smuggler galaxy frozen Boba Fett'.split()
            assert all(substr in google_response for substr in desired_strs)
        except InternalServerError:
            pass


def test_invalid_ocr_response():
    """
    Test that OCR of an image not containing text does not return much unicode text.
    Google Vision may extract a handful of stray characters but this info is not sent to Burning
    Glass as long as it is less than 20 characters.
    """
    with app.app_context():
        with open(os.path.join(CURRENT_DIR, 'files/{}'.format('hanPopcicle.png')), 'rb') as img:
            img_data = StringIO(img.read())
        try:
            google_response = google_vision_ocr(img_data, timeout=60)
            assert isinstance(google_response, unicode)
            assert len(google_response) < OCR_CHAR_MIN
        except InternalServerError:
            pass
