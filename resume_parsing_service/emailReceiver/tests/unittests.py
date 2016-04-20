import email
import os
import pytest

from resume_parsing_service.emailReceiver.email_process import validate_email_file
from resume_parsing_service.emailReceiver.email_process import get_email_attachment

current_dir = os.path.dirname(__file__)
EMAIL_FILES_ROOT = os.path.join(current_dir, 'emailFiles/')
VALID_EMAILS = [
    EMAIL_FILES_ROOT + 'valid1',
    EMAIL_FILES_ROOT + 'valid2',
    EMAIL_FILES_ROOT + 'valid3'
]

def test_validate_email_files():
    """
    Tests that all emails with valid hashes and senders are parsed out successfully.
    :return None:
    """
    for electronic_mail in VALID_EMAILS:
        with open(electronic_mail, 'r') as infile:
            email_file = email.message_from_file(infile)
        sender, hash = validate_email_file(email_file, electronic_mail)
        assert hash
        assert sender


def test_no_hash_fails():
    """
    Asserts that no supplied hash, ie a '+rndmstring' after the email but before the '@', will
    raise a UserWarning.
    :return:
    """
    with pytest.raises(UserWarning):
        with open(EMAIL_FILES_ROOT + 'noHash', 'r') as infile:
            email_file = email.message_from_file(infile)
        valid_sender, invalid_hash = validate_email_file(email_file, 'unused Key')


def test_get_email_attachment_with_content():
    """
    Asserts that with valid emails we are able to parse out a raw attachment of
    email.message.Message.
    :return:
    """
    for electronic_mail in VALID_EMAILS:
        with open(electronic_mail, 'r') as infile:
            email_file = email.message_from_file(infile)
        raw_attachment = get_email_attachment(email_file, 'unused Key')
        assert raw_attachment
        assert isinstance(raw_attachment, email.message.Message)


def test_get_attachment_with_multiples():
    with pytest.raises(UserWarning):
        with open(EMAIL_FILES_ROOT + 'multipleFiles', 'r') as infile:
            email_file = email.message_from_file(infile)
        raw_attachment = get_email_attachment(email_file, 'unused Key')



def test_get_attachment_no_content():
    """
    Tests emails that are sent without content. Includes signature and no signature.
    **Note** in testing a completely blank email has the content of `\r\n`.
    :return:
    """
    for noContentEmail in ['noContent', 'noContent2']:
        with open(EMAIL_FILES_ROOT + noContentEmail, 'r') as infile:
            email_file = email.message_from_file(infile)
        raw_attachment = get_email_attachment(email_file, 'unused Key')
        assert raw_attachment
        assert isinstance(raw_attachment, email.message.Message)


def test_get_attachment_no_file():
    with pytest.raises(UserWarning):
        with open(EMAIL_FILES_ROOT + 'noAttachment', 'r') as infile:
            email_file = email.message_from_file(infile)
        raw_attachment = get_email_attachment(email_file, 'unused Key')


def test_emails_with_forwarding():
    """
    Tests emails that have been forwarded have identical payload structures to single recipient
    messages. The following emails have been directly forwarded or forwarded twice.
    :return:
    """
    for forwardedEmail in ['forwarded', 'secondForward']:
        with open(EMAIL_FILES_ROOT + forwardedEmail, 'r') as infile:
            email_file = email.message_from_file(infile)
        raw_attachment = get_email_attachment(email_file, 'unused Key')
        assert raw_attachment
        assert isinstance(raw_attachment, email.message.Message)