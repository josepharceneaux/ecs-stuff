# Standard Lib
from cStringIO import StringIO
import base64
import json
import zlib
# Third Party/Common
from contracts import contract
from flask import current_app
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.common.error_handling import InternalServerError
import PyPDF2
import requests


@contract
def convert_pdf_to_text(pdf_file_obj):
    """
    Attempts to extract text from an unencrypted PDF file. This is to see if the PDF has text
    contents or if it is an embedded picture.
    :param cStringIO pdf_file_obj: PDF file object to be converted
    :rtype: string
    """
    pdf_file_obj.seek(0)
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
    page_count = pdf_reader.numPages
    pages_with_text = 0
    text = ''

    for i in xrange(page_count):
        new_text = pdf_reader.getPage(i).extractText()

        if new_text:
            text += new_text
            pages_with_text =+ 1

    """
    For the time being (8/13/16) we are assuming it is a picture based resume.
    Abbyy OCR can handle PDFs with images and text and deals with encrypted files.
    See GET-1463 for more info.
    """
    if pages_with_text < page_count:
        return ''

    return text


@contract
def decrypt_pdf(pdf_file_obj):
    """
    Returns an unencrypted pdf_file, if encrypted , or the original file.
    :param cStringIO pdf_file_obj: PDF file to be decrypted
    :rtype: cStringIO
    """
    pdf_file_obj.seek(0)
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

    if pdf_reader.isEncrypted:
        decrypted = pdf_reader.decrypt('')
        if not decrypted:
            raise InternalServerError(
                error_message=error_constants.ENCRYPTED_PDF['message'],
                error_code=error_constants.ENCRYPTED_PDF['code']
            )

        unencrypted_pdf_io = StringIO()
        pdf_writer = PyPDF2.PdfFileWriter()
        page_count = pdf_reader.numPages

        for page_no in xrange(page_count):
            pdf_writer.addPage(pdf_reader.getPage(page_no))
            pdf_writer.write(unencrypted_pdf_io)

        return unencrypted_pdf_io

    else:
        return pdf_file_obj


def convert_pdf_to_png(file_obj):
    logger.info('Converting pdf to png')
    api_key, api_url = current_app.config['IMAAS_KEY'], current_app.config['IMAAS_URL']
    headers = {'x-api-key': api_key}

    pdf_data = file_obj.getvalue()
    #file_obj.close()
    encoded = base64.b64encode(pdf_data)
    payload = json.dumps({'pdf_bin': encoded})

    try:
        conversion_response = requests.post(api_url, headers=headers, data=payload, timeout=30)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("Could not reach IMaaS Lambda")
        raise InternalServerError(
            error_message=error_constants.IMAAS_UNAVAILABLE['message'],
            error_code=error_constants.IMAAS_UNAVAILABLE['code']
        )

    if conversion_response.status_code != requests.codes.ok:
        raise InternalServerError(
            error_message=error_constants.IMAAS_ERROR['message'],
            error_code=error_constants.IMAAS_ERROR['code']
        )

    content = json.loads(conversion_response.content)
    img_data = content.get('img_data')

    if not img_data:
        raise InternalServerError(
            error_message=error_constants.IMAAS_NO_DATA['message'],
            error_code=error_constants.IMAAS_NO_DATA['code']
        )

    return StringIO(zlib.decompress(base64.b64decode(img_data)))
