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
from requests import codes

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.custom_errors.campaign import (INVALID_REQUEST_BODY,
                                                                  INVALID_INPUT, ERROR_SENDING_EMAIL)
from email_campaign_service.common.campaign_services.tests_helpers import (send_request,
                                                                           CampaignsTestsHelpers)
from email_campaign_service.modules.utils import do_mergetag_replacements, TEST_PREFERENCE_URL
from email_campaign_service.tests.modules.handy_functions import (TEST_MAIL_DATA, assert_and_delete_email,
                                                                  get_mail_connection, fetch_emails, delete_emails,
                                                                  create_email_campaign_with_merge_tags, )

__author__ = 'basit'


class TestSendTestEmail(object):
    """
    Tests for endpoint that sends Test Email
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.TEST_EMAIL

    def test_with_invalid_token(self):
        """
        Here we try to create email campaign with invalid access token
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_with_invalid_data(self, access_token_first):
        """
        Trying to send Test Email with 1) no data and 2) Non-JSON data. It should result in invalid usage error.
        """
        for data in (TEST_MAIL_DATA, None):
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first,
                                                             data=data, is_json=False,
                                                             expected_error_code=INVALID_REQUEST_BODY[1])

    def test_send_test_email_with_valid_data(self, access_token_first, user_first):
        """
        In this test, we will send a test email to our test email account and then we will confirm by getting that email
        from inbox with that specific subject.
        """
        data = TEST_MAIL_DATA.copy()
        del data['reply_to']  # user's email should be used as default value
        response = send_request(self.HTTP_METHOD, self.URL, access_token_first, data)
        assert response.status_code == requests.codes.OK
        assert retry(assert_and_delete_email, sleeptime=5, attempts=80, sleepscale=1, args=(data['subject'],),
                     kwargs=dict(search_criteria='(HEADER REPLY-TO "{}")'.format(user_first.email)),
                     retry_exceptions=(AssertionError,))

    def test_send_test_mail_without_optional_parameter(self, access_token_first):
        """
        In this test, we will send a test email without optional parameter to test email account and assert we get OK
        response.
        """
        subject = "Test Email %s" % fake.uuid4()
        data = TEST_MAIL_DATA.copy()
        del data['body_text']  # This parameter is optional
        data['subject'] = subject
        response = send_request(self.HTTP_METHOD, self.URL, access_token_first, data)
        assert response.status_code == requests.codes.OK

    def test_send_test_email_with_merge_tags(self, user_first, access_token_first):
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

    def test_send_test_email_with_invalid_reply_to_email_address(self, access_token_first):
        """
        In this test, we will try send a test email with invalid format of reply_to email-address. It should result
        in Bad Request error.
        """
        data = TEST_MAIL_DATA.copy()
        data['reply_to'] = fake.word()
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first,
                                                         data, expected_error_code=INVALID_INPUT[1])

    def test_test_email_with_invalid_email_address(self, access_token_first):
        """
        In this test we will send a test email to an invalid email address which will cause failure while sending email
        via SES (500 Error).
        :param access_token_first: access token
        """
        subject = "Test Email %s" % fake.uuid4()
        data = TEST_MAIL_DATA.copy()
        data['subject'] = subject
        data['email_address_list'] = ['some_invalid_email_%s' % fake.uuid4()]
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first, data=data,
                                                         expected_status_code=codes.INTERNAL_SERVER_ERROR,
                                                         expected_error_code=ERROR_SENDING_EMAIL[1])

    def test_test_email_with_invalid_fields(self, access_token_first):
        """
        In this test, we will send a test email with invalid values of required fields which will cause 400 error.
        :param access_token_first: access token for user_first
        """
        invalid_key_values = [('subject', CampaignsTestsHelpers.INVALID_TEXT_VALUES),
                              ('from', CampaignsTestsHelpers.INVALID_TEXT_VALUES),
                              ('body_html', CampaignsTestsHelpers.INVALID_TEXT_VALUES),
                              ('email_address_list', CampaignsTestsHelpers.INVALID_TEXT_VALUES +
                               ['test@gmail.com', 'test@gmail.com'] +
                               ['test%s@gmail.com' % index for index in xrange(11)])]
        for key, values in invalid_key_values:
            for value in values:
                print "Iterating key:{}, value:{}".format(key, value)
                data = TEST_MAIL_DATA.copy()
                data[key] = value
                CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first,
                                                                 data=data, expected_error_code=INVALID_INPUT[1])
