"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    - POST /v1/email-campaigns/:id/send
    - GET /v1/redirect
"""
# Packages
import re
import json
import imaplib

# Third Party
import requests
from redo import retry

# Application Specific
from email_campaign_service.common.models.db import db
from email_campaign_service.email_campaign_app import app
from email_campaign_service.tests.conftest import (fake, Role)
from email_campaign_service.common.models.candidate import Candidate
from email_campaign_service.modules.utils import do_mergetag_replacements
from email_campaign_service.common.models.misc import (UrlConversion, Activity)
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.routes import EmailCampaignApiUrl, UserServiceApiUrl
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignBlast,
                                                                 EmailCampaignSmartlist)
from email_campaign_service.tests.modules.handy_functions import (send_campaign_with_client_id, assert_and_delete_email,
                                                                  get_mail_connection, fetch_emails, delete_emails)
from email_campaign_service.common.campaign_services.tests.modules.email_campaign_helper_functions import \
    assert_campaign_send

__author__ = 'basit'


class TestSendCampaign(object):
    """
    Here are the tests for sending a campaign from endpoint /v1/email-campaigns/:id/send
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.SEND

    def test_campaign_send_with_invalid_token(self, email_campaign_user1_domain1_in_db):
        """
        Here we try to send email campaign with invalid access token
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD,
                                                         self.URL % email_campaign_user1_domain1_in_db.id)

    def test_campaign_send_with_no_smartlist_associated(self, access_token_first, email_campaign_of_user_first):
        """
        User auth token is valid but given email campaign has no associated smartlist with it. So
        up til this point we only have created a user and email campaign of that user
        (using fixtures passed in as params).
        It should get Invalid usage error.
        Custom error should be NoSmartlistAssociatedWithCampaign.
        """
        CampaignsTestsHelpers.campaign_send_with_no_smartlist(EmailCampaignSmartlist, self.URL, access_token_first,
                                                              campaign_id=email_campaign_of_user_first.id)

    def test_campaign_send_with_deleted_smartlist(self, access_token_first, campaign_with_and_without_client):
        """
        This deletes the smartlist associated with given campaign and then tries to send the campaign.
        It should result in Resource not found error.
        """
        email_campaign = campaign_with_and_without_client
        smartlist_ids = EmailCampaignSmartlist.get_smartlists_of_campaign(email_campaign.id, smartlist_ids_only=True)
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL % email_campaign.id,
                                                                  access_token_first, smartlist_ids[0])

    def test_campaign_send_with_no_smartlist_candidate(self, access_token_first, email_campaign_of_user_first,
                                                       talent_pipeline):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. Campaign sending should fail and no blasts should be
        created.
        """
        with app.app_context():
            response = CampaignsTestsHelpers.campaign_send_with_no_smartlist_candidate(
                self.URL % email_campaign_of_user_first.id, access_token_first,
                email_campaign_of_user_first, talent_pipeline.id)
            CampaignsTestsHelpers.assert_campaign_failure(response, email_campaign_of_user_first)
            if not email_campaign_of_user_first.email_client_id:
                json_resp = response.json()
                assert str(email_campaign_of_user_first.id) in json_resp['message']

    def test_campaign_send_with_campaign_in_some_other_domain(self, access_token_first,
                                                              email_campaign_in_other_domain):
        """
        User auth token is valid but given campaign does not belong to domain
        of logged-in user. It should get Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % email_campaign_in_other_domain.id,
                                                          access_token_first)

    def test_campaign_send_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to send a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign, self.HTTP_METHOD, self.URL,
                                                               access_token_first)

    def test_send_old_archived_campaign(self, access_token_first, email_campaign_of_user_first):
        """
        This is a test to send a campaign which was archived but task was not unscheduled.
        We should get ResourceNotFound error and task should be removed from scheduler-service.
        """
        # Assert that campaign is scheduled
        assert email_campaign_of_user_first.scheduler_task_id
        email_campaign_of_user_first.update(is_hidden=1)
        CampaignsTestsHelpers.request_for_resource_not_found_error(self.HTTP_METHOD,
                                                                   self.URL % email_campaign_of_user_first.id,
                                                                   access_token_first)
        db.session.commit()
        # Assert that scheduled task has been removed
        assert not email_campaign_of_user_first.scheduler_task_id

    def test_send_archived_campaign(self, access_token_first, email_campaign_of_user_first):
        """
        This is a test to send a campaign which was archived by user. We should get ResourceNotFound error.
        """
        campaign_id = email_campaign_of_user_first.id
        data = {'is_hidden': True}
        CampaignsTestsHelpers.request_for_ok_response('patch',
                                                      EmailCampaignApiUrl.CAMPAIGN % campaign_id,
                                                      access_token_first, data)
        CampaignsTestsHelpers.request_for_resource_not_found_error(self.HTTP_METHOD, self.URL % campaign_id,
                                                                   access_token_first)

    def test_campaign_send_with_one_smartlist_one_candidate_with_no_email(self, headers,
                                                                          campaign_with_candidate_having_no_email):
        """
        User auth token is valid, campaign has one smartlist associated. Smartlist has one
        candidate having no email associated. So, sending email campaign should fail.
        """
        response = requests.post(self.URL % campaign_with_candidate_having_no_email.id, headers=headers)
        CampaignsTestsHelpers.assert_campaign_failure(response, campaign_with_candidate_having_no_email,
                                                      requests.codes.OK)
        if not campaign_with_candidate_having_no_email.email_client_id:
            json_resp = response.json()
            assert str(campaign_with_candidate_having_no_email.id) in json_resp['message']

    def test_campaign_send_to_two_candidates_with_unique_email_addresses(self, headers, user_first,
                                                                         email_campaign_of_user_first):
        """
        Tests sending a campaign with one smartlist. That smartlist has, in turn,
        two candidates associated with it. Those candidates have unique email addresses.
        Campaign emails should be sent to 2 candidates so number of sends should be 2.
        """
        campaign = email_campaign_of_user_first
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first.id)

    def test_campaign_send_with_no_href_in_anchor_tag(self, email_campaign_of_user_first, headers, user_first):
        """
        Here we put an empty anchor tag in body_text of email-campaign. It should not result in any error.
        """
        campaign = email_campaign_of_user_first
        campaign.update(body_html='<html><body><a>%s</a></body></html>' % fake.sentence())
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first.id)

    def test_campaign_send_to_two_candidates_with_same_email_address_in_same_domain(self, headers, user_first,
                                                                                    email_campaign_of_user_first):
        """
        User auth token is valid, campaign has one smartlist associated. Smartlist has two
        candidates associated (with same email addresses). Email Campaign should be sent to only
        one candidate.
        """
        same_email = fake.email()
        for candidate in user_first.candidates:
            candidate.emails[0].update(address=same_email)
        response = requests.post(self.URL % email_campaign_of_user_first.id, headers=headers)
        assert_campaign_send(response, email_campaign_of_user_first, user_first.id, blast_sends=1)
        if not email_campaign_of_user_first.email_client_id:
            json_resp = response.json()
            assert str(email_campaign_of_user_first.id) in json_resp['message']

    def test_campaign_send_to_two_candidates_with_same_email_address_in_diff_domain(
            self, headers, user_first, campaign_with_candidates_having_same_email_in_diff_domain):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated. One more candidate exists in some other domain with same email
        address. Email Campaign should be sent to 2 candidates only.
        """
        campaign = campaign_with_candidates_having_same_email_in_diff_domain
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first.id)

    def test_campaign_send_with_outgoing_email_client(self, email_campaign_with_outgoing_email_client, headers,
                                                      user_first):
        """
        This sends email-campaign with SMTP server added by user. It should not get any error.
        """
        campaign = email_campaign_with_outgoing_email_client
        response = requests.post(self.URL % campaign['id'], headers=headers)
        assert_campaign_send(response, campaign, user_first.id, via_amazon_ses=False)

    def test_campaign_send_with_merge_tags(self, headers, user_first, email_campaign_with_merge_tags):
        """
        User auth token is valid, campaign has one smartlist associated. Smartlist has one
        candidate associated. We assert that received email has correctly replaced merge tags.
        If candidate's first name is `John` and last name is `Doe`, and email body is like
        'Hello *|FIRSTNAME|* *|LASTNAME|*,', it will become 'Hello John Doe,'
        """
        campaign, candidate = email_campaign_with_merge_tags
        response = requests.post(self.URL % campaign.id, headers=headers)
        candidate_object = Candidate.get_by_id(candidate['id'])
        candidate_address = candidate_object.emails[0].address
        [modified_subject] = do_mergetag_replacements([campaign.subject], user_first,
                                                      requested_object=candidate_object,
                                                      candidate_address=candidate_address,
                                                      )
        campaign.update(subject=modified_subject)
        assert_campaign_send(response, campaign, user_first.id, blast_sends=1, delete_email=False,
                             via_amazon_ses=False)
        msg_ids = retry(assert_and_delete_email, sleeptime=5, attempts=80, sleepscale=1,
                        args=(modified_subject,), kwargs=dict(delete_email=False),
                        retry_exceptions=(AssertionError, imaplib.IMAP4_SSL.error))
        mail_connection = get_mail_connection(app.config[TalentConfigKeys.GT_GMAIL_ID],
                                              app.config[TalentConfigKeys.GT_GMAIL_PASSWORD])
        email_bodies = fetch_emails(mail_connection, msg_ids)
        assert len(email_bodies) == 1
        assert candidate['first_name'] in email_bodies[0]
        assert candidate['last_name'] in email_bodies[0]
        assert str(candidate['id']) in email_bodies[0]  # This will be in unsubscribe URL.
        delete_emails(mail_connection, msg_ids, modified_subject)

    def test_campaign_send_with_email_client_id(self, send_email_campaign_by_client_id_response, user_first):
        """
        Email client can be Outlook Plugin, Browser etc.
        User auth token is valid, campaign has one smart list associated. Smartlist has two
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
        assert_campaign_send(response, campaign, user_first.id, email_client=True)

    def test_campaign_send_with_email_client_id_using_merge_tags(self, email_campaign_with_merge_tags, user_first,
                                                                 access_token_first):
        """
        This is the test for merge tags. We assert that merge tags has been successfully replaced with
        candidate's info.
        If candidate's first name is `John` and last name is `Doe`, and email body is like
        'Hello *|FIRSTNAME|* *|LASTNAME|*,', it will become 'Hello John Doe,'
        """
        expected_sends = 1
        email_campaign, candidate = email_campaign_with_merge_tags
        send_response = send_campaign_with_client_id(email_campaign, access_token_first)
        response = send_response['response']
        email_campaign_sends = send_response['response'].json()['email_campaign_sends']
        assert len(email_campaign_sends) == 1
        email_campaign_send = email_campaign_sends[0]
        for entity in ('new_text', 'new_html'):
            assert candidate['first_name'] in email_campaign_send[entity]
            assert candidate['last_name'] in email_campaign_send[entity]
            assert str(candidate['id']) in email_campaign_send[entity]  # This will be in unsubscribe URL.
        assert_campaign_send(response, email_campaign, user_first.id, expected_sends, email_client=True)

    def test_redirect_url(self, access_token_first, send_email_campaign_by_client_id_response):
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
        assert response.status_code == requests.codes.OK, response.text
        db.session.commit()
        opens_count_after = email_campaign_blast.opens
        hit_count_after = url_conversion.hit_count
        assert opens_count_after == opens_count_before + 1
        assert hit_count_after == hit_count_before + 1
        CampaignsTestsHelpers.assert_blast_sends(campaign, 2)
        campaign_send = requests.get(EmailCampaignApiUrl.SENDS % campaign.id,
                                     headers=dict(Authorization='Bearer %s' % access_token_first))
        campaign_send = campaign_send.json()
        CampaignsTestsHelpers.assert_for_activity(campaign.user_id, Activity.MessageIds.CAMPAIGN_EMAIL_OPEN,
                                                  campaign_send['sends'][0]['id'])
        UrlConversion.delete(url_conversion)

    def test_campaign_send_with_two_smartlists(self, headers, user_first, campaign_with_two_smartlists):
        """
        This function creates two smartlists with 20 candidates each and associates them
        with a campaign. Sends that campaign and tests if emails are sent to all 40 candidates.
        """
        response = requests.post(self.URL % campaign_with_two_smartlists.id, headers=headers)
        assert_campaign_send(response, campaign_with_two_smartlists, user_first.id, 40)

    def test_campaign_send_with_hundred_sends(self, headers, user_first, campaign_to_ten_candidates_not_sent):
        """
        Here we send one campaign to 10 candidates 10 times. Total sends should be 100.
        """
        campaign = campaign_to_ten_candidates_not_sent
        for number in xrange(1, 11):
            response = requests.post(self.URL % campaign.id, headers=headers)
            assert_campaign_send(response, campaign, user_first.id, blasts_count=number,
                                 blast_sends=10, total_sends=number * 10)

    def test_campaign_send_with_two_smartlists_having_same_candidate(
            self, headers, user_first, campaign_with_same_candidate_in_multiple_smartlists):
        """
        This function creates two smartlists with 1 candidate each, candidate is same in both smartlists and
        associates them with a campaign. Sends that campaign and tests if email is sent to the candidate only once.
        """
        campaign = campaign_with_same_candidate_in_multiple_smartlists
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first.id, blast_sends=1)

    def test_campaign_send_with_archived_candidate(self, headers, user_first, campaign_with_archived_candidate):
        """
        We try to send campaign to a smartlist which contains 2 candidates. One of the candidate is archived, So,
        campaign should only be sent to 1 candidate.
        """
        campaign = campaign_with_archived_candidate
        response = requests.post(self.URL % campaign['id'], headers=headers)
        assert_campaign_send(response, campaign, user_first.id, blast_sends=1)

    def test_campaign_send_in_test_domain(self, headers, domain_first, user_first, email_campaign_of_user_first):
        """
        Here we set user's email address to be test email account used in tests.
        We then set domain of user as test domain and send an email campaign to candidates. It should be
        received in user's inbox.
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()
        data = {'is_test_domain': 1}
        response = requests.patch(url=UserServiceApiUrl.DOMAIN % domain_first.id, headers=headers,
                                  data=json.dumps(data))
        assert response.ok, response.text
        user_first.update(email=app.config[TalentConfigKeys.GT_GMAIL_ID])
        response = requests.post(self.URL % email_campaign_of_user_first.id, headers=headers)
        assert_campaign_send(response, email_campaign_of_user_first, user_first.id)
        retry(assert_and_delete_email, sleeptime=5, attempts=50, sleepscale=1,
              args=(email_campaign_of_user_first.subject,),
              retry_exceptions=(AssertionError, imaplib.IMAP4_SSL.error))
