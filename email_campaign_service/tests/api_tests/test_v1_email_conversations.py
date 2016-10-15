"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    - POST /v1/email-conversations
    - GET /v1/email-conversations

"""
# Third Party
import requests
from redo import retry
from requests import codes

# Application Specific
from email_campaign_service.common.models.user import User
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.tests.modules.handy_functions import assert_and_delete_email

__author__ = 'basit'


class TestEmailConversations(object):
    """
    Here we test /v1/email-conversations
    """
    URL = EmailCampaignApiUrl.EMAIL_CONVERSATIONS

    def test_run_importer_and_get_imported_email_conversation(self, data_for_email_conversation_importer, headers):
        """
        This tests we import email-conversation with a specific subject and body successfully.
        """
        subject, body = data_for_email_conversation_importer
        access_token = User.generate_jw_token()
        headers_for_importer = {'Authorization': access_token}
        # This will run the importer for email-conversations
        response_post = requests.post(self.URL, headers=headers_for_importer)
        assert response_post.status_code == codes.OK
        retry(_get_email_conversations, sleeptime=5, attempts=120, sleepscale=1,
              args=(self.URL, headers, subject, body), retry_exceptions=(AssertionError,))


def _get_email_conversations(url, headers, subject, body):
    """
    This gets email-conversations and asserts that we have imported email-conversation for given subject and body
    """
    # GET email-conversations for user
    print 'Looking for email with subject `%s` form email-conversation importer' % subject
    response_get = requests.get(url, headers=headers)
    assert response_get.status_code == codes.OK
    email_conversations = response_get.json()['email_conversations']
    assert subject in set([email_conversation['subject'] for email_conversation in email_conversations])
    assert body in set([email_conversation['body'].strip() for email_conversation in email_conversations])
    assert_and_delete_email(subject)
