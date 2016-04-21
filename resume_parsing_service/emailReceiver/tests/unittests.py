"""
Unittests for all lambda email receiver functions.
"""
import email
import os
import pytest

from sqlalchemy.exc import SQLAlchemyError

from resume_parsing_service.emailReceiver.email_process import get_desired_talent_pool
from resume_parsing_service.emailReceiver.email_process import get_email_attachment
from resume_parsing_service.emailReceiver.email_process import get_user_access_token
from resume_parsing_service.emailReceiver.email_process import send_resume_to_service
from resume_parsing_service.emailReceiver.email_process import refresh_token
from resume_parsing_service.emailReceiver.email_process import validate_email_file
from resume_parsing_service.tests.test_fixtures import client_fixture
from resume_parsing_service.tests.test_fixtures import client_fixture2
from resume_parsing_service.tests.test_fixtures import culture_fixture
from resume_parsing_service.tests.test_fixtures import domain_fixture
from resume_parsing_service.tests.test_fixtures import expired_token_fixture
from resume_parsing_service.tests.test_fixtures import org_fixture
from resume_parsing_service.tests.test_fixtures import talent_pool_fixture
from resume_parsing_service.tests.test_fixtures import talent_pool_group_fixture
from resume_parsing_service.tests.test_fixtures import token_fixture
from resume_parsing_service.tests.test_fixtures import user_fixture
from resume_parsing_service.tests.test_fixtures import user_group_fixture

from resume_parsing_service.common.models.user import DomainRole
from resume_parsing_service.common.utils.handy_functions import add_role_to_test_user


CURRENT_DIR = os.path.dirname(__file__)
EMAIL_FILES_ROOT = os.path.join(CURRENT_DIR, 'emailFiles/')
VALID_EMAILS = [
    EMAIL_FILES_ROOT + 'valid1',
    EMAIL_FILES_ROOT + 'valid2',
    EMAIL_FILES_ROOT + 'valid3'
]
####################################
# No database connections required
####################################
def test_validate_email_files():
    """
    Tests that all emails with valid hashes and senders are parsed out successfully.
    :return None:
    """
    for electronic_mail in VALID_EMAILS:
        with open(electronic_mail, 'r') as infile:
            email_file = email.message_from_file(infile)
        sender, simple_hash = validate_email_file(email_file, electronic_mail)
        assert simple_hash
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
    """
    Tests that multiple files raises a UserWarning. Emails can only be parsed when they have one
    attachment.
    :return:
    """
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
    """
    Test that an email with no file raises a UserWarning.
    :return:
    """
    with pytest.raises(UserWarning):
        with open(EMAIL_FILES_ROOT + 'noAttachment', 'r') as infile:
            email_file = email.message_from_file(infile)
        unused_attachemnt = get_email_attachment(email_file, 'unused Key')


def test_emails_with_forwarding():
    """
    Tests emails that have been forwarded have identical payload structures to single recipient
    messages. The following emails have been directly forwarded or forwarded twice.
    :return:
    """
    for forwarded_email in ['forwarded', 'secondForward']:
        with open(EMAIL_FILES_ROOT + forwarded_email, 'r') as infile:
            email_file = email.message_from_file(infile)
        raw_attachment = get_email_attachment(email_file, 'unused Key')
        assert raw_attachment
        assert isinstance(raw_attachment, email.message.Message)


####################################
# Database connections required
####################################
def test_get_user_access_token(user_fixture, token_fixture):
    """
    Test that we can retrieve tokens with our helper.
    :param user_fixture:
    :param token_fixture:
    :return:
    """
    token = get_user_access_token(user_fixture.email)
    assert token


def test_get_token_with_bad_email(token_fixture):
    """
    Test that a not registered email raises an error (no spam/outsiders!).
    :param token_fixture:
    :return:
    """
    with pytest.raises(UserWarning):
        unused_token = get_user_access_token('invalid@nevervalid.com')


def test_get_valid_hash(talent_pool_fixture):
    """
    Test that we can retrive an id based on a valid hash.
    :param talent_pool_fixture:
    :return:
    """
    simple_hash = talent_pool_fixture.simple_hash
    desired_id = talent_pool_fixture.id
    retrieved_id = get_desired_talent_pool(simple_hash)
    assert desired_id == retrieved_id


def test_raise_invalid_hash(talent_pool_fixture):
    """
    Test that a hash not in our database raises an error.
    :param talent_pool_fixture:
    :return:
    """
    with pytest.raises(SQLAlchemyError):
        simple_hash = 'potato'
        unused_id = get_desired_talent_pool(simple_hash)


####################################
# Auth Service required
####################################
def test_refresh_token_refreshes(expired_token_fixture):
    """
    Test that we can refresh an expired token.
    :param expired_token_fixture:
    :return:
    """
    old_access_token = expired_token_fixture.access_token
    new_access_token = refresh_token(expired_token_fixture)
    assert old_access_token != new_access_token


####################################
# Auth and Resume services required
####################################
def test_lambda_handler(token_fixture, talent_pool_fixture, user_fixture):
    """
    Test that after we've validated our inputs we can communicate with the resume parsing service.
    :param token_fixture:
    :param talent_pool_fixture:
    :param user_fixture:
    :return:
    """
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS,
                                         DomainRole.Roles.CAN_GET_CANDIDATES])
    with open(EMAIL_FILES_ROOT + 'valid1', 'r') as infile:
        email_file = email.message_from_file(infile)
    raw_attachment = get_email_attachment(email_file, 'unused Key')
    assert send_resume_to_service(token_fixture.access_token, raw_attachment,
                                  talent_pool_fixture.id, 'test')
