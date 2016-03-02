# Packages
import re
import json
import time
import email
import imaplib
import requests

# Application Specific
from email_campaign_service.common.models.db import db
from email_campaign_service.email_campaign_app import app
from email_campaign_service.tests.conftest import fake, uuid
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.common.utils.activity_utils import ActivityMessageIds
from email_campaign_service.common.routes import (EmailCampaignUrl, CandidatePoolApiUrl,
                                                  EmailCampaignEndpoints, HEALTH_CHECK)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignBlast)
from email_campaign_service.tests.modules.handy_functions import (create_smartlist_with_candidate,
                                                                  delete_campaign)

__author__ = 'jitesh'


class TestGetCampaigns(object):
    """
    Here are the tests of /v1/email-campaigns
    """

    def test_get_all_campaigns(self, campaign_with_candidate_having_no_email, access_token_first,
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
        response = requests.get(
            url=CandidatePoolApiUrl.TALENT_PIPELINE_CAMPAIGN % talent_pipeline.id,
            headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == 200
        resp = response.json()
        assert 'email_campaigns' in resp


class TestCreateCampaign(object):
    """
    Here are the tests for creating a campaign from endpoint /v1/email-campaigns
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
        delete_campaign(resp_object['campaign'])

    def test_create_email_campaign_whitespace_campaign_name(self, assign_roles_to_user_first,
                                                            access_token_first, talent_pool):
        email_campaign_name = '       '
        email_subject = \
            uuid.uuid4().__str__()[0:8] + '-test_create_email_campaign_whitespace_campaign_name'
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
    Here are the tests for sending a campaign from endpoint /v1/email-campaigns/send
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignUrl.SEND

    def test_campaign_send_with_invalid_token(self, email_campaign_of_user_first):
        """
        Here we try to send email campaign with invalid access token
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD,
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
        """
        CampaignsTestsHelpers.campaign_send_with_no_smartlist(
            self.URL % email_campaign_of_user_first.id, access_token_first)

    def test_post_with_no_smartlist_candidate(self, access_token_first,
                                              email_campaign_of_user_first,
                                              assign_roles_to_user_first):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist .
        """
        with app.app_context():
            CampaignsTestsHelpers.campaign_send_with_no_smartlist_candidate(
                self.URL % email_campaign_of_user_first.id, access_token_first,
                email_campaign_of_user_first)

    def test_post_with_campaign_in_some_other_domain(self, access_token_first,
                                                     email_campaign_in_other_domain):
        """
        User auth token is valid but given campaign does not belong to domain
        of logged-in user. It should get Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % email_campaign_in_other_domain.id, access_token_first)

    def test_post_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)

    def test_post_with_one_smartlist_two_candidates_with_no_email(
            self, access_token_first, campaign_with_candidate_having_no_email):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has one
        candidate having no email associated. So, Custom error should be raised.
        """
        CampaignsTestsHelpers.campaign_test_with_no_valid_candidate(
            self.URL % campaign_with_candidate_having_no_email.id,
            access_token_first, campaign_with_candidate_having_no_email.id)

    def test_campaign_send_to_two_candidates_with_unique_email_addresses(
            self, access_token_first, user_first, campaign_with_valid_candidate):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated (with distinct email addresses). Email Campaign should be sent to
        both candidates.
        """
        campaign = campaign_with_valid_candidate
        response = requests.post(
            self.URL % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_campaign_send(response, campaign, user_first, 2)
        assert_mail(campaign.email_subject)

    def test_campaign_send_to_two_candidates_with_same_email_address_in_same_domain(
            self, access_token_first, user_first, campaign_with_valid_candidate):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated (with same email addresses). Email Campaign should not be sent to
        any candidate. Response should get Invalid usage.
        """
        same_email = fake.email()
        for candidate in user_first.candidates:
            candidate.emails[0].update(address=same_email)
        response = requests.post(
            self.URL % campaign_with_valid_candidate.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_send_to_two_candidates_with_same_email_address_in_diff_domain(
            self, access_token_first, user_first,
            campaign_with_candidates_having_same_email_in_diff_domain):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated. One more candidate exists in some other domain with same email
        address. Email Campaign should be sent to 2 candidates only.
        """
        campaign = campaign_with_candidates_having_same_email_in_diff_domain
        response = requests.post(
            self.URL % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_campaign_send(response, campaign, user_first, 2)
        assert_mail(campaign.email_subject)

    def test_campaign_send_with_email_client_id(
            self, send_email_campaign_by_client_id_response, user_first):
        """
        Email client can be Outlook Plugin, Browser etc.
        User auth token is valid, campaign has one smart list associated. Smartlist has tow
        candidates with email address. Email Campaign should be not be sent to candidate as
        we are providing client_id. Response should be something like
            {
                  "email_campaign_sends": [
                {
                  "candidate_email_address": "basit.qc@gmail.com",
                  "email_campaign_id": 1,
                  "new_html": "email body text",
                  "new_text": "<img src=\"http://127.0.0.1:8014/v1/redirect/10082954\" />\n
                  <html>\n <body>\n  <h1>\n   Welcome to email campaign service\n
                  </h1>\n </body>\n</html>"
                }
                  ]
            }
        """
        response = send_email_campaign_by_client_id_response['response']
        campaign = send_email_campaign_by_client_id_response['campaign']
        assert_campaign_send(response, campaign, user_first, 2, email_client=True)

    def test_redirect_url(self, send_email_campaign_by_client_id_response):
        """
        Test the url which is sent to candidates in email to be valid.
        This is the url which included in email to candidate in order to be
        redirected to the get talent campaign page. After checking that the url is valid,
        this test sends a get request to the url and checks the response to be ok (200).
        After that it checks the database if the hit count in UrlConversion table
        has been updated. It also checks that the relevant fields in
        EmailCampaignBlast table have been updated after getting ok response
        from get request.
        :param send_email_campaign_by_client_id_response:
        """
        response = send_email_campaign_by_client_id_response['response']
        campaign = send_email_campaign_by_client_id_response['campaign']
        json_response = response.json()
        email_campaign_sends = json_response['email_campaign_sends'][0]
        new_html = email_campaign_sends['new_html']
        redirect_url = re.findall('"([^"]*)"', new_html) # get the redirect URL from html
        assert len(redirect_url) > 0
        redirect_url = redirect_url[0]

        # get the url conversion id from the redirect url
        url_conversion_id = re.findall( '[\n\r]*redirect\/\s*([^?\n\r]*)', redirect_url)
        assert len(url_conversion_id) > 0
        url_conversion_id = int(url_conversion_id[0])
        db.session.commit()
        url_conversion = UrlConversion.get(url_conversion_id)
        assert url_conversion
        email_campaign_blast = EmailCampaignBlast.get_latest_blast_by_campaign_id(campaign.id)
        assert email_campaign_blast
        opens_count_before = email_campaign_blast.opens
        hit_count_before = url_conversion.hit_count
        response = requests.get(redirect_url)
        assert response.status_code == 200
        db.session.commit()
        opens_count_after = email_campaign_blast.opens
        hit_count_after = url_conversion.hit_count
        assert opens_count_after == opens_count_before + 1
        assert hit_count_after == hit_count_before + 1
        UrlConversion.delete(url_conversion)


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


def assert_campaign_send(response, campaign, user, expected_count=1, email_client=False):
    """
    This assert that campaign has successfully been sent to candidates and campaign blasts and
    sends have been updated as expected. It then checks the source URL is correctly formed or
    in database table "url_conversion".
    """
    assert response.status_code == 200
    assert response.json()
    if not email_client:
        json_resp = response.json()
        assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    time.sleep(20)
    db.session.commit()
    assert len(campaign.blasts) == 1
    campaign_blast = campaign.blasts[0]
    assert campaign_blast.sends == expected_count
    # assert on sends
    campaign_sends = campaign.sends
    assert len(campaign_sends) == expected_count
    sends_url_conversions = []
    # assert on activity of individual campaign sends
    for campaign_send in campaign_sends:
        # Get "email_campaign_send_url_conversion" records
        sends_url_conversions.extend(campaign_send.url_conversions)
        if not email_client:
            CampaignsTestsHelpers.assert_for_activity(user.id,
                                                      ActivityMessageIds.CAMPAIGN_EMAIL_SEND,
                                                      campaign_send.id)
    if campaign_sends:
        # assert on activity for whole campaign send
        CampaignsTestsHelpers.assert_for_activity(user.id,
                                                  ActivityMessageIds.CAMPAIGN_SEND,
                                                  campaign.id)

    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        assert str(
            send_url_conversion.url_conversion.id) in send_url_conversion.url_conversion.source_url
        UrlConversion.delete(send_url_conversion.url_conversion)


# Test for healthcheck
def test_health_check():
    response = requests.get(EmailCampaignEndpoints.HOST_NAME % HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(EmailCampaignEndpoints.HOST_NAME % HEALTH_CHECK + '/')
    assert response.status_code == 200
