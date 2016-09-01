import os
from cStringIO import StringIO
import PyPDF2
from resume_parsing_service.app.views.pdf_utils import convert_pdf_to_text, decrypt_pdf


CURRENT_DIR = os.path.dirname(__file__)


def test_text_extracted_from_text_pdfs():
    """
    Test that text based pdfs get their contents extracted.
    """
    text_pdfs = ['test_bin.pdf', 'test_bin_13.pdf', 'test_bin_14.pdf']

    for pdf in text_pdfs:
        with open(os.path.join(CURRENT_DIR, 'files/{}'.format(pdf)), 'rb') as infile:
            data = StringIO(infile.read())
            assert convert_pdf_to_text(data)


def test_image_based_pdfs_return_no_text():
    """
    Test that img based pdfs return an empty string.
    """
    text_pdfs = ['GET-1319.pdf', 'pic_in_encrypted.pdf']

    for pdf in text_pdfs:
        with open(os.path.join(CURRENT_DIR, 'files/{}'.format(pdf)), 'rb') as infile:
            data = StringIO(infile.read())
            assert convert_pdf_to_text(data) == ''

def test_encrypted_pdfs_can_be_decrypted():
    """
    Test that pdfs can be decrypted and return a decrypted file for future use. This assumes
    the password is an empty string.
    """
    encrypted_pds = ['jDiMaria.pdf']

    for pdf in encrypted_pds:
        with open(os.path.join(CURRENT_DIR, 'files/{}'.format(pdf)), 'rb') as infile:
            data = StringIO(infile.read())

        pdf_reader = PyPDF2.PdfFileReader(data)
        assert pdf_reader.isEncrypted == 1

        decrypted_pdf = decrypt_pdf(data)
        pdf_reader = PyPDF2.PdfFileReader(decrypted_pdf)
        assert pdf_reader.isEncrypted == 0
