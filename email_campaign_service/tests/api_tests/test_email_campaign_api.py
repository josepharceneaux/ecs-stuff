"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    1 - GET /v1/email-campaigns
    2 - GET /v1/email-campaigns/:id
    3 - POST /v1/email-campaigns
    4- POST /v1/email-campaigns/:id/send
    5- GET /v1/redirect

"""

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
from email_campaign_service.common.routes import CandidatePoolApiUrl
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.common.models.misc import (UrlConversion, Activity)
from email_campaign_service.common.routes import (EmailCampaignUrl, EmailCampaignEndpoints,
                                                  HEALTH_CHECK)
from email_campaign_service.tests.conftest import fake, uuid, create_email_campaign_smartlist
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignBlast)
from email_campaign_service.tests.modules.handy_functions import (create_smartlist_with_candidate,
                                                                  create_email_campaign_smartlists,
                                                                  delete_campaign,
                                                                  assert_valid_campaign_get,
                                                                  get_campaign_or_campaigns,
                                                                  assert_talent_pipeline_response)


class TestGetCampaigns(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    def test_get_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('get', EmailCampaignUrl.CAMPAIGNS, None)

    def test_get_campaign_of_other_domain(self, email_campaign_in_other_domain, access_token_first):
        """
        Here we try to GET a campaign which is in some other domain. It should result-in
         ForbiddenError.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            'get', EmailCampaignUrl.CAMPAIGN % email_campaign_in_other_domain.id, access_token_first)

    def test_get_by_campaign_id(self, campaign_with_candidate_having_no_email,
                                access_token_first,
                                talent_pipeline):
        """
        This is the test to GET the campaign by providing campaign_id. It should get OK response
        """
        email_campaign = get_campaign_or_campaigns(
            access_token_first, campaign_id=campaign_with_candidate_having_no_email.id)
        assert_valid_campaign_get(email_campaign, campaign_with_candidate_having_no_email)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_by_campaign_id_with_fields(self, campaign_with_candidate_having_no_email,
                                access_token_first,
                                talent_pipeline):
        """
        This is the test to GET the campaign by providing campaign_id & filters. It should get OK response
        """
        fields = ['id', 'subject', 'body_html', 'is_hidden']

        email_campaign = get_campaign_or_campaigns(
            access_token_first,
            campaign_id=campaign_with_candidate_having_no_email.id,
            fields=fields)
        assert_valid_campaign_get(email_campaign, campaign_with_candidate_having_no_email, fields=fields)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first, fields=fields)

    def test_get_all_campaigns_in_user_domain(self, email_campaign_of_user_first,
                                              email_campaign_of_user_second,
                                              email_campaign_in_other_domain,
                                              access_token_first,
                                              talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain.
        Here two campaigns have been created by different users of same domain. Total count
        should be 2. Here we also create another campaign in some other domain but it shouldn't
        be there in GET response.
        """
        # Test GET api of email campaign
        email_campaigns = get_campaign_or_campaigns(access_token_first)
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], email_campaign_of_user_first)
        assert_valid_campaign_get(email_campaigns[1], email_campaign_of_user_second)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_campaigns_with_paginated_response(self, email_campaign_of_user_first,
                                                   email_campaign_of_user_second,
                                                   email_campaign_in_other_domain,
                                                   access_token_first,
                                                   talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain using
        paginated response. Here two campaigns have been created by different users of same domain.
        """
        # Test GET api of email campaign using per_page=1 and default page=1.
        # It should return first campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?per_page=1')
        assert len(email_campaigns) == 1
        assert_valid_campaign_get(email_campaigns[0], email_campaign_of_user_first)
        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

        # Test GET api of email campaign using per_page=1 for page=2. It should
        # return second campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?per_page=1&page=2')
        assert len(email_campaigns) == 1
        assert_valid_campaign_get(email_campaigns[0], email_campaign_of_user_second)

        # Test GET api of email campaign with 2 results per_page
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?per_page=2')
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], email_campaign_of_user_first)
        assert_valid_campaign_get(email_campaigns[1], email_campaign_of_user_second)
        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

        # Test GET api of email campaign with default per_page=10 and page =1.
        # It should get both campaigns in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?&page=1')
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], email_campaign_of_user_first)
        assert_valid_campaign_get(email_campaigns[1], email_campaign_of_user_second)

        # Test GET api of email campaign with page = 2. No campaign should be received in response
        # as we have created only two campaigns so far and default per_page is 10.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?page=2')
        assert len(email_campaigns) == 0


class TestCreateCampaign(object):
    """
    Here are the tests for creating a campaign from endpoint /v1/email-campaigns
    """

    def test_create_email_campaign(self, access_token_first, talent_pipeline,
                                   assign_roles_to_user_first):
        name = fake.name()
        subject = uuid.uuid4().__str__()[0:8] + '-test_create_email_campaign'
        email_from = fake.name()
        reply_to = fake.safe_email()
        body_text = fake.sentence()
        body_html = "<html><body><h1>%s</h1></body></html>" % body_text
        smartlist_id = create_smartlist_with_candidate(access_token_first,
                                                                      talent_pipeline)
        data = {
            "name": name,
            "subject": subject,
            "from": email_from,
            "reply_to": reply_to,
            "body_html": body_html,
            "body_text": body_text,
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
        # Wait for 30 seconds for scheduler to execute it and then assert mail.
        time.sleep(30)
        # Check for email received.
        assert_mail(subject)
        delete_campaign(resp_object['campaign'])

    def test_create_email_campaign_whitespace_campaign_name(self, assign_roles_to_user_first,
                                                            access_token_first, talent_pipeline):
        name = '       '
        subject = \
            uuid.uuid4().__str__()[0:8] + '-test_create_email_campaign_whitespace_campaign_name'
        email_from = 'no-reply@gettalent.com'
        reply_to = fake.safe_email()
        body_text = fake.sentence()
        body_html = "<html><body><h1>%s</h1></body></html>" % body_text
        smartlist_id = create_smartlist_with_candidate(access_token_first,
                                                                      talent_pipeline)
        data = {'name': name,
                'subject': subject,
                'from': email_from,
                'reply_to': reply_to,
                'body_html': body_html,
                'body_text': body_text,
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
        assert resp_object['error']['message'] == 'name is required'


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
                                              assign_roles_to_user_first, talent_pipeline):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist .
        """
        with app.app_context():
            CampaignsTestsHelpers.campaign_send_with_no_smartlist_candidate(
                self.URL % email_campaign_of_user_first.id, access_token_first,
                email_campaign_of_user_first, talent_pipeline.id)

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
        assert_mail(campaign.subject)

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
        assert_mail(campaign.subject)

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
        redirect_url = re.findall('"([^"]*)"', new_html)  # get the redirect URL from html
        assert len(redirect_url) > 0
        redirect_url = redirect_url[0]

        # get the url conversion id from the redirect url
        url_conversion_id = re.findall('[\n\r]*redirect\/\s*([^?\n\r]*)', redirect_url)
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

    def test_send_campaign_with_two_smartlists(
            self, access_token_first, user_first, talent_pipeline, email_campaign_of_user_first, assign_roles_to_user_first):
        """
        This function create two smartlists with 20 candidates each and associate them
        with a campaign. Sends that campaign and tests if emails are sent to all 40 candidates.
        :param access_token_first: Access token of user_first
        :param user_first: Valid user from fist domain
        :param talent_pipeline: valid talent pipeline
        :param email_campaign_of_user_first: email campaign associated with user first
        :return:
        """
        smartlist_id1 = create_smartlist_with_candidate(access_token_first,
                                                        talent_pipeline,
                                                        emails_list=True,
                                                        count=20)
        smartlist_id2 = create_smartlist_with_candidate(access_token_first,
                                                        talent_pipeline,
                                                        emails_list=True,
                                                        count=20)
        campaign = email_campaign_of_user_first
        create_email_campaign_smartlists(smartlist_ids=[smartlist_id1, smartlist_id2],
                                        email_campaign_id=campaign.id)
        response = requests.post(
            self.URL % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        time.sleep(30)
        assert_campaign_send(response, campaign, user_first, 40)
        assert_mail(campaign.subject)


def assert_mail(subject):
    """
    Asserts that the user received the email in his inbox which has the subject as subject,


    :param subject:       Email subject
    :return:
    """
    abort_after = 60
    start = time.time()
    mail_found = False
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('gettalentmailtest@gmail.com', 'GetTalent@1234')
    # mail.list()  # Out: list of "folders" aka labels in gmail.
    print "Check for mail with subject: %s" % subject
    header_subject = '(HEADER Subject "%s")' % subject
    # Wait for 10 seconds then start the loop for 60 seconds
    time.sleep(30)
    while True:
        delta = time.time() - start
        mail.select("inbox")  # connect to inbox.
        result, data = mail.uid('search', None, header_subject)

        for latest_email_uid in data[0].split():
            result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
            raw_email = data[0][1]

            email_message = email.message_from_string(raw_email)

            raw_mail_subject_ = ''.join(email_message['Subject'].split())
            test_subject = ''.join(subject.split())
            if raw_mail_subject_ == test_subject:
                mail_found = True
                break

        if mail_found:
            break

        if delta >= abort_after:
            break

    assert mail_found, "Mail with subject %s was not found." % subject


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
    time.sleep(30)
    db.session.commit()
    assert len(campaign.blasts.all()) == 1
    campaign_blast = campaign.blasts[0]
    assert campaign_blast.sends == expected_count
    # assert on sends
    campaign_sends = campaign.sends.all()
    assert len(campaign_sends) == expected_count
    sends_url_conversions = []
    # assert on activity of individual campaign sends
    for campaign_send in campaign_sends:
        # Get "email_campaign_send_url_conversion" records
        sends_url_conversions.extend(campaign_send.url_conversions)
        if not email_client:
            CampaignsTestsHelpers.assert_for_activity(user.id,
                                                      Activity.MessageIds.CAMPAIGN_EMAIL_SEND,
                                                      campaign_send.id)
    if campaign_sends:
        # assert on activity for whole campaign send
        CampaignsTestsHelpers.assert_for_activity(user.id,
                                                  Activity.MessageIds.CAMPAIGN_SEND,
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
