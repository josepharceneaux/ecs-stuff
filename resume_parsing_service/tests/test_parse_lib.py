import os
from cStringIO import StringIO

from resume_parsing_service.app.modules.parse_lib import is_resume_image


def test_image_files_are_images():
    """
    Tests that the known extensions (with the exception of .pdf) return true in our function call.
    """
    extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx', '.pcx', '.jp2',
                  '.jpc', '.jb2', '.djvu', '.djv']

    for ext in extensions:
        assert is_resume_image(ext, StringIO())


def test_text_files_are_not_images():
    """
    Test that accepted doc types (with the exception of .pdf) return false in our function call.
    """
    extensions = ['.doc', '.docx', '.rtf', '.txt']

    for ext in extensions:
        assert is_resume_image(ext, StringIO()) is False


def test_text_only_pdfs_are_not_images():
    current_dir = os.path.dirname(__file__)
    text_pdfs = ['test_bin.pdf', 'test_bin_13.pdf', 'test_bin_14.pdf']
    for pdf in text_pdfs:
        with open(os.path.join(current_dir, 'files/{}'.format(pdf)), 'rb') as infile:
            data = StringIO(infile.read())
            assert is_resume_image('.pdf', data) is False


def test_pdfs_with_images_are_images():
    current_dir = os.path.dirname(__file__)
    text_pdfs = ['GET-1319.pdf', 'pic_in_encrypted.pdf']
    for pdf in text_pdfs:
        with open(os.path.join(current_dir, 'files/{}'.format(pdf)), 'rb') as infile:
            data = StringIO(infile.read())
            assert is_resume_image('.pdf', data)
