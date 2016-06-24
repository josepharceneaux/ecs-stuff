"""Functions associated with resume parsing flow (generally based on file type."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position, fixme, import-error
# Standard library
from cStringIO import StringIO
from os.path import basename
from os.path import splitext
from time import time
import base64
import json
# Third Party/Framework Specific.
from flask import current_app
import PyPDF2
# Module Specific
from resume_parsing_service.app import logger, redis_store
from resume_parsing_service.app.views.optic_parse_lib import fetch_optic_response
from resume_parsing_service.app.views.optic_parse_lib import parse_optic_xml
from resume_parsing_service.app.views.utils import gen_hash_from_file
from resume_parsing_service.app.views.ocr_lib import google_vision_ocr
from resume_parsing_service.common.error_handling import InvalidUsage, InternalServerError
from resume_parsing_service.common.utils.talent_s3 import boto3_put


IMAGE_FORMATS = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx',
                 '.pcx', '.jp2', '.jpc', '.jb2', '.djvu', '.djv']
DOC_FORMATS = ['.pdf', '.doc', '.docx', '.rtf', '.txt']
RESUME_EXPIRE_TIME = 60 * 60 * 24 * 7  # one week in seconds.

def parse_resume(file_obj, filename_str):
    """Primary resume parsing function.

    :param cStringIO.StringI file_obj: a StringIO representation of the raw binary.
    :param str filename_str: The file_obj file name.
    :return: A dictionary of processed candidate data or an appropriate error message.
    """
    logger.info("Beginning parse_resume(%s)", filename_str)

    file_ext = basename(splitext(filename_str.lower())[-1]) if filename_str else ""

    if file_ext == '.pdf':
        file_obj = unencrypt_pdf(file_obj)


    if is_resume_image(file_ext, file_obj):
        # If file is an image, OCR it
        start_time = time()
        doc_content = google_vision_ocr(file_obj)
        logger.info(
            "Benchmark: google_vision_ocr for {}: took {}s to process".format(
                filename_str, time() - start_time)
        )

    else:
        doc_content = file_obj.getvalue()

    if not doc_content:
        bucket = current_app.config['S3_BUCKET_NAME']
        boto3_put(file_obj.getvalue(), bucket, filename_str, 'FailedResumes')
        raise InvalidUsage("Unable to determine the contents of the document: {}".format(filename_str))

    try:
        encoded_resume = base64.b64encode(doc_content)

    except Exception:
        logger.exception('Error encoding resume before sending to BG Optic.')
        raise InvalidUsage('Issue encoding resume text. Please ensure the file is of a resume and not blurry.')

    optic_response = fetch_optic_response(encoded_resume, filename_str)

    if optic_response:
        candidate_data = parse_optic_xml(optic_response)
        return {'raw_response': optic_response, 'candidate': candidate_data}

    else:
        raise InvalidUsage('No XML text received from Optic Response for {}'.format(filename_str))


def convert_pdf_to_text(pdf_file_obj):
    """
    Attempts to extract text from an unencrypted PDF file. This is to see if the PDF has text
    contents or if it is an embedded picture.
    :param cStringIO.StringIO pdf_file_obj:
    :return str:
    """
    text = ''
    pdf_file_obj.seek(0)
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
    page_count = pdf_reader.numPages

    for i in xrange(page_count):
        new_text = pdf_reader.getPage(i).extractText()

        if new_text:
            text += new_text

    return text


def unencrypt_pdf(pdf_file_obj):
    """
    Returns an unencrypted pdf_file, if encrypted , or the original file.
    :param cStringIO.StringIO pdf_file_obj:
    :return cStringIO.StringIO:
    """
    pdf_file_obj.seek(0)
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

    if pdf_reader.isEncrypted:
        decrypted = pdf_reader.decrypt('')
        if not decrypted:
            raise InternalServerError(
                'The PDF appears to be encrypted and could not be read. Please try using an un-encrypted PDF')

        unencrypted_pdf_io = StringIO()
        pdf_writer = PyPDF2.PdfFileWriter()
        page_count = pdf_reader.numPages

        for page_no in xrange(page_count):
            pdf_writer.addPage(pdf_reader.getPage(page_no))
            pdf_writer.write(unencrypted_pdf_io)

        return unencrypted_pdf_io

    else:
        pdf_file_obj.seek(0)
        return pdf_file_obj

def get_or_store_parsed_resume(resume_file, filename_str):
    """
    Tries to retrieve processed resume data from redis or parses it and stores it.
    :param resume_file:
    :param filename_str:
    :return:
    """
    hashed_file_name = 'parsedResume_{}'.format(gen_hash_from_file(resume_file))
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


def is_resume_image(file_ext, file_obj):
    resume_is_image = False

    if not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)

    if file_ext not in IMAGE_FORMATS and file_ext not in DOC_FORMATS:
        raise InvalidUsage('File ext \'{}\' not in accepted image or document formats'.format(file_ext))

    # Find out if the file is an image
    if file_ext in IMAGE_FORMATS:
        if file_ext == '.pdf':
            text = convert_pdf_to_text(file_obj)
            if not text.strip():
                # pdf is possibly an image
                resume_is_image = True
        else:
            resume_is_image = True

    return resume_is_image
