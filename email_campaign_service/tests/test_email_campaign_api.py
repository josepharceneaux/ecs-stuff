import json
import time
import email
import imaplib
import requests

from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.utils.activity_utils import ActivityMessageIds
from email_campaign_service.common.routes import EmailCampaignUrl, CandidatePoolApiUrl, \
    EmailCampaignEndpoints, HEALTH_CHECK
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

    def test_post_with_campaign_in_some_other_domain(self, access_token_first,
                                                     email_campaign_in_other_domain):
        """
        User auth token is valid but given campaign does not belong to domain
        of logged-in user. It should get Forbidden error.
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(self.METHOD,
                                                         self.URL % email_campaign_in_other_domain.id,
                                                         access_token_first)

    def test_post_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsCommonTests.request_with_invalid_campaign_id(EmailCampaign,
                                                              self.METHOD,
                                                              self.URL,
                                                              access_token_first,
                                                              None)

    def test_post_with_one_smartlist_two_candidates_with_no_email(
            self, access_token_first, campaign_with_candidate_having_no_email,
            campaign_with_smartlist):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has one
        candidate having no email associated. So, Custom error should be raised.
        :return:
        """
        CampaignsCommonTests.campaign_test_with_no_valid_candidate(
            self.URL % campaign_with_candidate_having_no_email.id,
            access_token_first, campaign_with_candidate_having_no_email.id)

    def test_campaign_send_to_two_candidate_with_unique_email_addresses(
            self, access_token_first, user_first, campaign_with_valid_candidate):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated (with distinct email addresses). Email Campaign should be sent to
        both candidate.
        :return:
        """
        campaign = EmailCampaign.get_by_id(str(campaign_with_valid_candidate.id))
        response = requests.post(
            self.URL % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_campaign_send(response, campaign, user_first, 2)

    def test_campaign_send_to_two_candidate_with_same_email_addresses(
            self, access_token_first, user_first, campaign_with_valid_candidate):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated (with same email addresses). Email Campaign should be sent to
        one email address.
        :return:
        """
        same_email = fake.email()
        for candidate in user_first.candidates:
            candidate.emails[0].update(address=same_email)
        campaign = EmailCampaign.get_by_id(str(campaign_with_valid_candidate.id))
        response = requests.post(
            self.URL % campaign.id, headers=dict(Authorization='Bearer %s'
                                                               % access_token_first))
        assert_campaign_send(response, campaign, user_first)

    def test_campaign_send_with_email_client_id(
            self, access_token_first, campaign_with_valid_candidate):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has one
        candidate with email address. Email Campaign should be not be sent to candidate as
        we are providing client_id. Response should be something like
            {
                  "email_campaign_sends": [
                {
                  "candidate_email_address": "basit.qc@gmail.com",
                  "email_campaign_id": 1,
                  "new_html": "email body text",
                  "new_text": "<img src=\"http://127.0.0.1:8014/v1/redirect/10082954\" />\n<html>\n <body>\n  <h1>\n   Welcome to email campaign service\n  </h1>\n </body>\n</html>"
                }
                  ]
            }
        """
        campaign = EmailCampaign.get_by_id(str(campaign_with_valid_candidate.id))
        campaign.update(email_client_id=fake.random_digit())
        response = requests.post(
            self.URL % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 200
        json_response = response.json()
        assert 'email_campaign_sends' in json_response
        email_campaign_sends = json_response['email_campaign_sends'][0]
        assert 'new_html' in email_campaign_sends
        assert 'new_text' in email_campaign_sends
        assert 'email_campaign_id' in email_campaign_sends
        assert campaign.id == email_campaign_sends['email_campaign_id']


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


def assert_campaign_send(response, campaign, user, expected_count=1):
    """
    This assert that campaign has successfully been sent to candidates and campaign blasts and
    sends have been updated as expected. It then checks the source URL is correctly formed or
    in database table "url_conversion".
    :param response:
    :param campaign:
    :param user:
    :return:
    """
    assert response.status_code == 200
    assert response.json()
    json_resp = response.json()
    assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    time.sleep(20)
    db.session.commit()
    campaign_blast = campaign.blasts[0]
    assert campaign_blast.sends == expected_count
    # assert on sends
    campaign_sends = campaign.sends
    assert len(campaign_sends) == expected_count
    # assert on activity of individual campaign sends
    for sms_campaign_send in campaign_sends:
        CampaignsCommonTests.assert_for_activity(user.id,
                                                 ActivityMessageIds.CAMPAIGN_EMAIL_SEND,
                                                 sms_campaign_send.id)
    if campaign_sends:
        # assert on activity for whole campaign send
        CampaignsCommonTests.assert_for_activity(user.id,
                                                 ActivityMessageIds.CAMPAIGN_SEND,
                                                 campaign.id)
    sends_url_conversions = []
    # Get "sms_campaign_send_url_conversion" records
    for campaign_send in campaign_sends:
        sends_url_conversions.extend(campaign_send.url_conversions)
    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        assert str(send_url_conversion.url_conversion.id) in send_url_conversion.url_conversion.source_url
        UrlConversion.delete(send_url_conversion.url_conversion)


# Test for healthcheck
def test_health_check():
    response = requests.get(EmailCampaignEndpoints.HOST_NAME % HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(EmailCampaignEndpoints.HOST_NAME % HEALTH_CHECK + '/')
    assert response.status_code == 200
