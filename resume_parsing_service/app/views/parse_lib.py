# pylint: disable=wrong-import-position, fixme
# Standard library
from cStringIO import StringIO
from os.path import basename
from os.path import splitext
from time import time
import base64
import json
# Third Party/Framework Specific.
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import process_pdf
from pdfminer.pdfparser import PDFDocument
from pdfminer.pdfparser import PDFParser
# Module Specific
from resume_parsing_service.app import logger, redis_store
from resume_parsing_service.app.views.optic_parse_lib import fetch_optic_response
from resume_parsing_service.app.views.optic_parse_lib import parse_optic_xml
from resume_parsing_service.app.views.utils import gen_hash_from_file
from resume_parsing_service.app.views.ocr_lib import google_vision_ocr
from resume_parsing_service.common.error_handling import InvalidUsage


IMAGE_FORMATS = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx',
                 '.pcx', '.jp2', '.jpc', '.jb2', '.djvu', '.djv']
DOC_FORMATS = ['.pdf', '.doc', '.docx', '.rtf', '.txt']
GOOGLE_API_KEY = "AIzaSyD4i4j-8C5jLvQJeJnLmoFW6boGkUhxSuw"
GOOGLE_CLOUD_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"
RESUME_EXPIRE_TIME = 604800  # one week in seconds.

def parse_resume(file_obj, filename_str):
    """Primary resume parsing function.

    :param cStringIO.StringI file_obj: a StringIO representation of the raw binary.
    :param str filename_str: The file_obj file name.
    :return: A dictionary of processed candidate data or an appropriate error message.
    """
    logger.info("Beginning parse_resume(%s)", filename_str)

    file_ext, is_resume_image = get_resume_file_info(filename_str, file_obj)

    file_obj.seek(0)
    if is_resume_image:
        # If file is an image, OCR it
        start_time = time()
        doc_content = google_vision_ocr(file_obj)
        logger.info(
            "Benchmark: google_vision_ocr for {}: took {}s to process".format(filename_str,
                                                                         time() - start_time)
        )
    else:
        start_time = time()
        doc_content = file_obj.read()
        logger.info(
            "Benchmark: Reading file_obj and magic.from_buffer(%s) took %ss",
            filename_str, time() - start_time
        )
        final_file_ext = file_ext

    if not doc_content:
        raise InvalidUsage("Unable to determine the contents of the document: {}".format(filename_str))

    encoded_resume = base64.b64encode(doc_content)
    optic_response = fetch_optic_response(encoded_resume, filename_str)

    if optic_response:
        candidate_data = parse_optic_xml(optic_response)
        # Consider returning tuple
        return {'raw_response': optic_response, 'candidate': candidate_data}

    else:
        raise InvalidUsage('No XML text received from Optic Response for {}'.format(filename_str))


def convert_pdf_to_text(pdf_file_obj):
    """Converts a PDF file to a usable string."""
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

    # TODO access if this reassignment is needed.
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


def get_or_store_parsed_resume(resume_file, filename_str):
    """
    Tries to retrieve processed resume data from redis or parses it and stores it.
    :param resume_file:
    :param filename_str:
    :return:
    """
    hashed_file_name = gen_hash_from_file(resume_file)
    cached_resume = redis_store.get(hashed_file_name)

    if cached_resume:
        parsed_resume = json.loads(cached_resume)
        logger.info('Resume {} has been loaded from cache and its hashed_key is {}'.format(
            filename_str, hashed_file_name))

    else:
        # Parse the resume if not hashed.
        logger.info('Couldn\'t find Resume {} in cache with hashed_key: {}'.format(filename_str,
                                                                                   hashed_file_name))
        parsed_resume = parse_resume(file_obj=resume_file, filename_str=filename_str)
        redis_store.set(hashed_file_name, json.dumps(parsed_resume))
        redis_store.expire(hashed_file_name, RESUME_EXPIRE_TIME)

    return parsed_resume


def get_resume_file_info(filename_str, file_obj):
    file_ext = basename(splitext(filename_str.lower())[-1]) if filename_str else ""
    is_resume_image = False

    if not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)

    if file_ext not in IMAGE_FORMATS and file_ext not in DOC_FORMATS:
        raise InvalidUsage('File ext \'{}\' not in accepted image or document formats'.format(file_ext))

    # Find out if the file is an image
    if file_ext in IMAGE_FORMATS:
        if file_ext == '.pdf':
            start_time = time()
            text = convert_pdf_to_text(file_obj)
            if not text.strip():
                # pdf is possibly an image
                is_resume_image = True
        else:
            is_resume_image = True
        file_ext = '.pdf' # Question: If it's a jpeg we rename it to a pdf?

    return file_ext, is_resume_image