# Standard Lib.
from StringIO import StringIO
from time import sleep
import base64
import json
import os
# Third party.
import requests as r
from BeautifulSoup import BeautifulSoup
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import process_pdf
from pdfminer.pdfparser import PDFDocument
from pdfminer.pdfparser import PDFParser
from xhtml2pdf import pisa
import magic
# JSON outputs.
from .resume_json import DOCX
from .resume_json import GET_642
from .resume_json import GET_646
from .resume_json import JPG
from .resume_json import PDF
from .resume_json import PDF_13
from .resume_json import PDF_14
# Modules being tested.
from resume_service.resume_parsing_app.views.optic_parse_lib import fetch_optic_response
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_name
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_emails
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_phones
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_educations

EDUCATIONS_KEYS = ('city', 'degrees', 'state', 'country', 'school_name')

JSON_MAPS = [
    {'dict_name': DOCX, 'name': 'VEENA NITHOO', 'email_len': 0, 'phone_len': 1, 'education_len': 1},
    {'dict_name': GET_642, 'name': 'Bobby Breland', 'email_len': 1, 'phone_len': 2, 'education_len': 1},
    {'dict_name': GET_646, 'name': 'Patrick Kaldawy', 'email_len': 3, 'phone_len': 6, 'education_len': 2},
    {'dict_name': JPG, 'name': 'Erik Farmer', 'email_len': 0, 'phone_len': 2, 'education_len': 0},
    {'dict_name': PDF, 'name': 'MARK GREENE', 'email_len': 1, 'phone_len': 1, 'education_len': 1},
    {'dict_name': PDF_13, 'name': 'BRUCE PARKEY', 'email_len': 1, 'phone_len': 1, 'education_len': 1},
    # This PDF currently does not get its email/phone parsed out of the footer.
    # This PDF currently parses out the wrong education count
    {'dict_name': PDF_14, 'name': 'Jose Chavez', 'email_len': 0, 'phone_len': 0, 'education_len': 2}
]

RESUME_TO_NAMES_MAPS = [
    {'file_name': 'Get-642.doc', 'name': 'Bobby Breland'},
    {'file_name': 'Get-646.doc', 'name': 'Patrick Kaldawy'},
    {'file_name': 'test_bin.docx', 'name': 'VEENA NITHOO'},
    {'file_name': 'test_bin.jpg', 'name': 'Erik Farmer'},
    {'file_name': 'test_bin.pdf', 'name': 'MARK GREENE'},
    {'file_name': 'test_bin_13.pdf', 'name': 'BRUCE PARKEY'},
    {'file_name': 'test_bin_14.pdf', 'name': 'Jose Chavez'},
]


def test_candidate_name_parsing():
    """
        Tests name parsing using API
    """
    for resume_dict in RESUME_TO_NAMES_MAPS:
        resume = convert_file_to_encoded_binary(resume_dict['file_name'])
        optic_response = fetch_optic_response(resume)
        name = parse_candidate_name(optic_response['resume']['contact'])
        assert name == resume_dict['name']


def test_name_parsing_with_json():
    for j in JSON_MAPS:
        resume = j['dict_name']
        name = parse_candidate_name(resume['resume']['contact'])
        assert name == j['name']


def test_email_parsing_with_json():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the 'address' key.
        3. If it's the first/only email assert the label is 'Primary'.
        4. If it is not the first email asser the label is 'Other'.
    """
    for j in JSON_MAPS:
        resume = j['dict_name']
        emails = parse_candidate_emails(resume['resume']['contact'])
        # Test count
        assert len(emails)== j['email_len']
        for i, e in enumerate(emails):
            assert 'address' in e.keys()
            if i == 0:
                assert emails[i]['label'] == 'Primary'
            else:
                assert emails[i]['label'] == 'Other'


def test_phone_parsing_from_json():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the 'value' key.
    """
    for j in JSON_MAPS:
        resume = j['dict_name']
        phones = parse_candidate_phones(resume['resume']['contact'])
        assert len(phones)== j['phone_len']
        for p in phones:
            assert 'value' in p.keys()

# TODO: ERROR
def test_education_parsing_from_json():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the correct education keys.
    """
    for j in JSON_MAPS:
        # print '\n' + j['name']
        resume = j['dict_name']
        if resume['resume'].get('education'):
            educations = parse_candidate_educations((resume)['resume']['education'])
            # Verify Expected Length
            assert len(educations) == j['education_len']
            # Very each dict in list has proper keys
            for e in educations:
                assert all(k in e for k in EDUCATIONS_KEYS if e)


###################################################################################################
# Helper functions extracted out of app due to logging and not wanting to run app/have app context#
# (unit tests)
###################################################################################################
def convert_file_to_encoded_binary(filename_str):
    file_ext = os.path.basename(os.path.splitext(filename_str.lower())[-1]) if filename_str else ""

    if not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)

    image_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx',
                     '.pcx', '.jp2', '.jpc', '.jb2', '.djvu', '.djv']

    is_resume_image = False
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(filename_str)), 'rb') as resume_file:
        if file_ext in image_formats:
            if file_ext == '.pdf':
                text = convert_pdf_to_text(resume_file)
                if not text.strip():
                    is_resume_image = True
            else:
                is_resume_image = True
            final_file_ext = '.pdf'

        resume_file.seek(0)
        if is_resume_image:
            doc_content = ocr_image(resume_file)
        else:
            doc_content = resume_file.read()
            mime_type = magic.from_buffer(doc_content, mime=True)
            final_file_ext = file_ext

            if mime_type == 'text/html':
                file_obj = StringIO()
                try:
                    create_pdf_status = pisa.CreatePDF(doc_content, file_obj)
                    if create_pdf_status.err:
                        return None
                except:
                    return None
                file_obj.seek(0)
                doc_content = file_obj.read()
                final_file_ext = '.pdf'

    if not doc_content:
        return {}
    encoded_resume = base64.b64encode(doc_content)
    return encoded_resume


def convert_pdf_to_text(pdf_file_obj):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

    fp = pdf_file_obj

    parser = PDFParser(fp)
    doc = PDFDocument()
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize('')
    if not doc.is_extractable:
        return ''

    process_pdf(rsrcmgr, device, fp)
    device.close()

    text = retstr.getvalue()
    retstr.close()
    return text


def ocr_image(img_file_obj, export_format='pdfSearchable'):
    """Posts the image to Abby OCR API, then keeps pinging to check if it's done.
       Quits if not done in certain number of tries.

    Return:
        Image file OCR'd in desired format.
    """

    ABBY_OCR_API_AUTH_TUPLE = ('gettalent', 'lfnJdQNWyevJtg7diX7ot0je')

    # Post the image to Abby
    files = {'file': img_file_obj}
    response = r.post('http://cloud.ocrsdk.com/processImage',
                             auth=ABBY_OCR_API_AUTH_TUPLE,
                             files=files,
                             data={'profile': 'documentConversion', 'exportFormat': export_format}
                             )
    if response.status_code != 200:
        return 0

    xml = BeautifulSoup(response.text)

    task_id = xml.response.task['id']
    estimated_processing_time = int(xml.response.task['estimatedprocessingtime'])

    if xml.response.task['status'] != 'Queued':
        pass

    # Keep pinging Abby to get task status. Quit if tried too many times
    ocr_url = ''
    num_tries = 0
    max_num_tries = 6
    while not ocr_url:
        sleep(estimated_processing_time)

        response = r.get('http://cloud.ocrsdk.com/getTaskStatus', params=dict(taskId=task_id),
                                auth=ABBY_OCR_API_AUTH_TUPLE)
        xml = BeautifulSoup(response.text)
        ocr_url = xml.response.task.get('resulturl')

        if not ocr_url:
            if num_tries > max_num_tries:
                raise Exception('OCR took > {} tries to process image'.format(max_num_tries))
            estimated_processing_time = 2  # If not done in originally estimated processing time, wait 2 more seconds
            num_tries += 1
            continue

    if response.status_code == r.codes.ok:
        response = r.get(ocr_url)
        return response.content
    else:
        return 0