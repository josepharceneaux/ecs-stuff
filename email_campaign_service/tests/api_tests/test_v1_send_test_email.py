"""
 Author:
        Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>
        Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    - POST /v1/test-email-send
"""
# Standard Library
import imaplib

# Third Party
import requests
from redo import retry

# Application Specific
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.campaign_services.tests_helpers import send_request
from email_campaign_service.modules.utils import do_mergetag_replacements, TEST_PREFERENCE_URL
from email_campaign_service.tests.modules.handy_functions import (TEST_MAIL_DATA, assert_and_delete_email,
                                                                  get_mail_connection, fetch_emails, delete_emails,
                                                                  create_email_campaign_with_merge_tags,)

__author__ = 'basit'


def test_send_test_email_with_valid_data(access_token_first, user_first):
    """
    In this test, we will send a test email to our test email account and then we will confirm by getting that email
    from inbox with that specific subject.
    """
    data = TEST_MAIL_DATA.copy()
    del data['reply_to']  # user's email should be used as default value
    response = send_request('post', EmailCampaignApiUrl.TEST_EMAIL, access_token_first, data)
    assert response.status_code == requests.codes.OK
    assert retry(assert_and_delete_email, sleeptime=5, attempts=80, sleepscale=1, args=(data['subject'],),
                 kwargs=dict(search_criteria='(HEADER REPLY-TO "{}")'.format(user_first.email)),
                 retry_exceptions=(AssertionError,))


def test_send_test_email_with_invalid_reply_to_email_address(access_token_first):
    """
    In this test, we will try send a test email with invalid format of reply_to email-address. It should result
    in Bad Request error.
    """
    data = TEST_MAIL_DATA.copy()
    data['reply_to'] = fake.word()
    response = send_request('post', EmailCampaignApiUrl.TEST_EMAIL, access_token_first, data)
    assert response.status_code == requests.codes.BAD_REQUEST


def test_send_test_mail_without_optional_parameter(access_token_first):
    """
    In this test, we will send a test email without optional parameter to test email account and assert we get OK
    response.
    """
    subject = "Test Email %s" % fake.uuid4()
    data = TEST_MAIL_DATA.copy()
    del data['body_text']  # This parameter is optional
    data['subject'] = subject
    response = send_request('post', EmailCampaignApiUrl.TEST_EMAIL, access_token_first, data)
    assert response.status_code == requests.codes.OK


def test_send_test_email_with_merge_tags(user_first, access_token_first):
    """
    In this test, we will send a test email containing merge tags. Those merge tags should be replaced with
    user's info.
    """
    user_first.update(first_name=fake.first_name())
    user_first.update(last_name=fake.last_name())
    email_campaign = create_email_campaign_with_merge_tags(user_id=user_first.id, in_db_only=True)
    data = TEST_MAIL_DATA.copy()
    data.update({'subject': email_campaign.subject,
                 'body_html': email_campaign.body_html,
                 'body_text': email_campaign.body_text})
    response = send_request('post', EmailCampaignApiUrl.TEST_EMAIL, access_token_first, data)
    assert response.status_code == requests.codes.OK
    [modified_subject] = do_mergetag_replacements([email_campaign.subject], user_first,
                                                  requested_object=user_first)
    msg_ids = retry(assert_and_delete_email, sleeptime=5, attempts=80, sleepscale=1,
                    args=(modified_subject,), kwargs=dict(delete_email=False),
                    retry_exceptions=(AssertionError, imaplib.IMAP4_SSL.error))
    mail_connection = get_mail_connection(app.config[TalentConfigKeys.GT_GMAIL_ID],
                                          app.config[TalentConfigKeys.GT_GMAIL_PASSWORD])
    email_bodies = fetch_emails(mail_connection, msg_ids)
    assert len(email_bodies) == 1
    assert user_first.first_name in email_bodies[0]
    assert user_first.last_name in email_bodies[0]
    assert TEST_PREFERENCE_URL in email_bodies[0]
    try:
        delete_emails(mail_connection, msg_ids, modified_subject)
    except Exception:
        pass


def test_test_email_with_invalid_email_address(access_token_first):
    """
    In this test we will send a test email to an invalid email address which will cause failure while sending email
    via SES (500 Error).
    :param access_token_first: access token
    """
    subject = "Test Email %s" % fake.uuid4()
    data = TEST_MAIL_DATA.copy()
    data['subject'] = subject
    data['email_address_list'] = ['some_invalid_email_%s' % fake.uuid4()]
    response = send_request('post', EmailCampaignApiUrl.TEST_EMAIL, access_token_first, data)
    assert response.status_code == requests.codes.INTERNAL_SERVER_ERROR


def test_test_email_with_invalid_fields(access_token_first):
    """
    In this test, we will send a test email with invalid values of required fields which will cause 400 error.
    :param access_token_first: access token for user_first
    """

    invalid_key_values = [('subject', ('', 0, True, None, {}, [])),
                          ('from', ('', 0, True, None, {}, [])),
                          ('body_html', ('', 0, True, None, {}, [])),
                          ('email_address_list', ('', 0, True, None, {}, [], ['test@gmail.com', 'test@gmail.com'],
                                      ['test%s@gmail.com' % index for index in xrange(11)]))]
    for key, values in invalid_key_values:
        for value in values:
            data = TEST_MAIL_DATA.copy()
            data[key] = value
            response = send_request('post', EmailCampaignApiUrl.TEST_EMAIL, access_token_first, data)
            assert response.status_code == requests.codes.BAD_REQUEST
