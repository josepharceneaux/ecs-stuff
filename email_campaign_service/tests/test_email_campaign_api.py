import json
import time
import email
import imaplib
import requests

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.routes import EmailCampaignUrl, CandidatePoolApiUrl
from email_campaign_service.common.campaign_services.common_tests import CampaignsCommonTests
from email_campaign_service.tests.conftest import (create_smartlist_with_candidate, fake, uuid)


__author__ = 'jitesh'


class TestGetCampaigns(object):
    """
    Here are the tests of /v1/campaigns
    """
    def test_get_all_campaigns(self, campaign_with_smartlist, access_token_first,
                               talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns
        """
        # Test GET api of email campaign
        response = requests.get(url=EmailCampaignUrl.CAMPAIGNS,
                                headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == 200
        resp = response.json()
        assert 'email_campaigns' in resp
        email_campaigns = resp['email_campaigns']
        assert resp['email_campaigns']
        assert 'id' in email_campaigns[0]
        # Test GET api of talent-pipelines/:id/campaigns
        response = requests.get(url=CandidatePoolApiUrl.TALENT_PIPELINE_CAMPAIGN % talent_pipeline.id,
                                headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == 200
        resp = response.json()
        assert 'email_campaigns' in resp


class TestCreateCampaign(object):
    """
    Here are the tests for creating a campaign from endpoint /v1/campaigns
    """

    def test_create_email_campaign(self, access_token_first, talent_pool,
                                   assign_roles_to_user_first):
        email_campaign_name = fake.name()
        email_subject = uuid.uuid4().__str__()[0:8] + '-test_create_email_campaign'
        email_from = fake.name()
        email_reply_to = fake.safe_email()
        email_body_text = fake.sentence()
        email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
        smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token_first,
                                                                      talent_pool)
        data = {
            "email_campaign_name": email_campaign_name,
            "email_subject": email_subject,
            "email_from": email_from,
            "email_reply_to": email_reply_to,
            "email_body_html": email_body_html,
            "email_body_text": email_body_text,
            "list_ids": [smartlist_id],
            # "email_client_id": 1
        }
        # add_role_to_test_user(user_first, ['CAN_GET_CANDIDATES'])
        r = requests.post(
            url=EmailCampaignUrl.CAMPAIGNS,
            data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % access_token_first,
                     'content-type': 'application/json'}
        )
        assert r.status_code == 201
        resp_object = r.json()
        assert 'campaign' in resp_object
        # Wait for 10 seconds for scheduler to execute it and then assert mail.
        time.sleep(10)
        # Check for email received.
        assert_mail(email_subject)

    def test_create_email_campaign_whitespace_campaign_name(self, assign_roles_to_user_first,
                                                            access_token_first, talent_pool):
        email_campaign_name = '       '
        email_subject = uuid.uuid4().__str__()[0:8] + \
                        '-test_create_email_campaign_whitespace_campaign_name'
        email_from = 'no-reply@gettalent.com'
        email_reply_to = fake.safe_email()
        email_body_text = fake.sentence()
        email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
        smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token_first,
                                                                      talent_pool)
        data = {'email_campaign_name': email_campaign_name,
                'email_subject': email_subject,
                'email_from': email_from,
                'email_reply_to': email_reply_to,
                'email_body_html': email_body_html,
                'email_body_text': email_body_text,
                'list_ids': [smartlist_id]
                }
        r = requests.post(
            url=EmailCampaignUrl.CAMPAIGNS,
            data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % access_token_first,
                     'content-type': 'application/json'}
        )
        resp_object = r.json()
        assert 'error' in resp_object
        assert resp_object['error']['message'] == 'email_campaign_name is required'


class TestSendCampaign(object):
    """
    Here are the tests for sending a campaign from endpoint /v1/campaigns/send
    """
    METHOD = 'post'
    URL = EmailCampaignUrl.SEND

    def test_campaign_send_with_invalid_token(self, email_campaign_of_user_first):
        """
        Here we try to send email campaign with invalid access token
        """
        CampaignsCommonTests.request_with_invalid_token(self.METHOD,
                                                        self.URL % email_campaign_of_user_first.id,
                                                        None)

    def test_post_with_no_smartlist_associated(self, access_token_first,
                                               email_campaign_of_user_first):
        """
        User auth token is valid but given email campaign has no associated smartlist with it. So
        up til this point we only have created a user and email campaign of that user
        (using fixtures passed in as params).
        It should get Invalid usage error.
        Custom error should be NoSmartlistAssociatedWithCampaign.
        :return:
        """
        CampaignsCommonTests.campaign_send_with_no_smartlist(
            self.URL % email_campaign_of_user_first.id, access_token_first)

    def test_post_with_no_smartlist_candidate(self, access_token_first,
                                              email_campaign_of_user_first,
                                              assign_roles_to_user_first):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist .
        :return:
        """
        with app.app_context():
            CampaignsCommonTests.campaign_send_with_no_smartlist_candidate(
                self.URL % email_campaign_of_user_first.id, access_token_first,
                email_campaign_of_user_first)


# def test_create_email_campaign_with_email_client(user_first, access_token_first):
#

def assert_mail(email_subject):
    """
    Asserts that the user received the email in his inbox which has the email_subject as subject,


    :param email_subject:       Email subject
    :return:
    """
    abort_after = 60
    start = time.time()
    mail_found = False
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('gettalentmailtest@gmail.com', 'GetTalent@1234')
    # mail.list()  # Out: list of "folders" aka labels in gmail.
    print "Check for mail with subject: %s" % email_subject
    header_subject = '(HEADER Subject "%s")' % email_subject
    # Wait for 10 seconds then start the loop for 60 seconds
    time.sleep(10)
    while True:
        delta = time.time() - start
        mail.select("inbox")  # connect to inbox.
        result, data = mail.uid('search', None, header_subject)

        for latest_email_uid in data[0].split():
            result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
            raw_email = data[0][1]

            email_message = email.message_from_string(raw_email)

            raw_mail_subject_ = ''.join(email_message['Subject'].split())
            test_email_subject = ''.join(email_subject.split())
            if raw_mail_subject_ == test_email_subject:
                mail_found = True
                break

        if mail_found:
            break

        if delta >= abort_after:
            break

    assert mail_found, "Mail with subject %s was not found." % email_subject
