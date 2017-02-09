"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have tests for API
    - /v1/base-campaigns
    - /v1/base-campaigns/:base-campaign_id/link-event/:event_id
"""
# Standard Imports
import re
# Packages

import requests
from requests import codes
import pytest

# Service Specific
from ...models.db import db
from ...models.event import Event
from ...tests.sample_data import fake
from ...routes import EmailCampaignApiUrl, SocialNetworkApiUrl
from ...constants import HttpMethods
from ..tests_helpers import CampaignsTestsHelpers, send_request
from ...models.base_campaign import (BaseCampaign, BaseCampaignEvent)
from ...models.email_campaign import EmailCampaignBlast, EmailCampaignSend
from ...models.misc import UrlConversion, Activity
from modules.helper_functions import (get_email_campaign_data, assert_email_campaign_overview,
                                      assert_event_overview, auth_header)
from ..tests.modules.email_campaign_helper_functions import assert_campaign_send

__author__ = 'basit'


class TestCreateBaseCampaigns(object):
    """
    Here are the tests of /v1/base-campaigns
    """
    URL = EmailCampaignApiUrl.BASE_CAMPAIGNS
    HTTP_METHOD = HttpMethods.POST

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_with_valid_data(self, token_first):
        """
        Data is valid. Base campaign should be created
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
        assert response.status_code == codes.CREATED
        assert response.json()['id']

    def test_with_missing_required_fields(self, token_first):
        """
        Data does not contain some required fields. It should result in bad request error.
        """
        for key in ('name', 'description'):
            data = CampaignsTestsHelpers.base_campaign_data()
            del data[key]
            response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
            assert response.status_code == codes.BAD

    def test_with_empty_required_fields(self, token_first):
        """
        Data does not contain valid values for some required fields. It should result in bad request error.
        """
        for key in ('name', 'description'):
            data = CampaignsTestsHelpers.base_campaign_data()
            data[key] = ''
            response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
            assert response.status_code == codes.BAD

    def test_with_same_name(self, token_first, token_same_domain):
        """
        Tries to create base-campaign with existing name. It should not get any error.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
        assert response.status_code == codes.CREATED

        # Create campaign third time with other user of same domain
        response = send_request(self.HTTP_METHOD, self.URL, token_same_domain, data)
        assert response.status_code == codes.CREATED

    def test_with_same_name_in_other_domain(self, token_first, token_second):
        """
        Tries to create base-campaign in other domain with existing name. It should allow creation.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = send_request(self.HTTP_METHOD, self.URL, token_second, data)
        assert response.status_code == codes.CREATED


class TestBaseCampaignEvent(object):
    """
    Here are tests to link an event with base campaign
    """
    URL = EmailCampaignApiUrl.BASE_CAMPAIGN_EVENT
    HTTP_METHOD = HttpMethods.POST

    def test_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD,
                                                         self.URL % (fake.random_int(), fake.random_int()))

    def test_with_valid_data(self, base_campaign, event_in_db, token_first, token_same_domain):
        """
        This hits the API with valid event and base campaign. This requests with two different users of same domain.
        """
        for access_token in (token_first, token_same_domain):
            response = send_request(self.HTTP_METHOD, self.URL % (base_campaign['id'], event_in_db['id']),
                                    access_token)
            assert response.status_code == codes.CREATED, response.text
            assert response.json()['id']
            db.session.commit()
            base_campaign_event = BaseCampaignEvent.get_by_id(response.json()['id'])
            assert base_campaign_event.event_id == event_in_db['id']
            assert base_campaign_event.base_campaign_id == base_campaign['id']

    def test_with_user_of_other_domain(self, base_campaign, event_in_db, token_second):
        """
        Requested event does not belong to user. It should result in Forbidden Error.
        """
        response = send_request(self.HTTP_METHOD, self.URL % (base_campaign['id'], event_in_db['id']), token_second)
        assert response.status_code == codes.FORBIDDEN, response.text

    def test_with_not_owned_base_campaign(self, base_campaign_other, event_in_db, token_first):
        """
        Requested base-campaign does not belong to user's domain. It should result in Forbidden Error.
        """
        response = send_request(self.HTTP_METHOD, self.URL % (base_campaign_other['id'], event_in_db['id']),
                                token_first)
        assert response.status_code == codes.FORBIDDEN, response.text

    def test_with_non_existing_event(self, base_campaign, token_first):
        """
        This should result in resource not found error.
        """
        non_existing_event_id = CampaignsTestsHelpers.get_non_existing_ids(Event)
        response = send_request(self.HTTP_METHOD, self.URL % (base_campaign['id'], non_existing_event_id),
                                token_first)
        assert response.status_code == codes.NOT_FOUND, response.text

    def test_with_non_existing_base_campaign(self, event_in_db, token_first):
        """
        This should result in resource not found error.
        """
        non_existing_base_campaign_id = CampaignsTestsHelpers.get_non_existing_id(BaseCampaign)
        response = send_request(self.HTTP_METHOD, self.URL % (non_existing_base_campaign_id, event_in_db['id']),
                                token_first)
        assert response.status_code == codes.NOT_FOUND, response.text

    def test_link_base_campaign_with_deleted_event(self, new_event_in_db_second, token_first, base_campaign):
        """
        This tests linking of base campaign with deleted event. This should result in a Resource not found.
        """
        response = requests.delete(SocialNetworkApiUrl.EVENT % new_event_in_db_second['id'],
                                   headers=auth_header(token_first))
        event_response = requests.get(SocialNetworkApiUrl.EVENT % new_event_in_db_second['id'],
                                      headers=auth_header(token_first))
        event_content = event_response.json()
        assert event_content['event']['is_deleted_from_vendor'] and event_content['event']['is_hidden']

        response = send_request(self.HTTP_METHOD, self.URL % (base_campaign['id'], new_event_in_db_second['id']),
                                token_first)
        assert response.status_code == codes.NOT_FOUND, response.text

    def test_link_base_campaign_with_deleted_event_form_vendor(self, new_event_in_db_second, token_first, base_campaign):
        """
        This tests linking of base campaign with deleted event from vendor. This should result in a Resource not found
        """
        db.session.commit()
        event = Event.get_by_id(new_event_in_db_second['id'])
        event.update(is_deleted_from_vendor=1)
        event_response = requests.get(SocialNetworkApiUrl.EVENT % new_event_in_db_second['id'],
                                      headers=auth_header(token_first))
        event_content = event_response.json()
        assert event_content['event']['is_deleted_from_vendor'] and not event_content['event']['is_hidden']
        response = send_request(self.HTTP_METHOD, self.URL % (base_campaign['id'], new_event_in_db_second['id']),
                                token_first)
        assert response.status_code == codes.NOT_FOUND, response.text


class TestEventEmailCampaign(object):
    """
    Here we link an email-campaign with event and base-campaign.
    For this we need to create an email-campaign with base_campaign_id.
    """
    URL = EmailCampaignApiUrl.CAMPAIGNS
    HTTP_METHOD = HttpMethods.POST

    def test_create_email_campaign_with_base_id(self, smartlist_first, base_campaign, token_first):
        """
        This creates an email-campaign with base_campaign_id.
        """
        campaign_data = get_email_campaign_data(fake.uuid4(), smartlist_first['id'])
        campaign_data['base_campaign_id'] = base_campaign['id']
        response = send_request(self.HTTP_METHOD, self.URL, token_first, campaign_data)
        assert response.status_code == codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object
        assert resp_object['campaign']['id']

    def test_create_email_campaign_with_not_owned_base_campaign(self, smartlist_first, base_campaign_other,
                                                                token_first):
        """
        This creates an email-campaign with not owned base_campaign_id. This should result in Forbidden error.
        """
        campaign_data = get_email_campaign_data(fake.uuid4(), smartlist_first['id'])
        campaign_data['base_campaign_id'] = base_campaign_other['id']
        response = send_request(self.HTTP_METHOD, self.URL, token_first, campaign_data)
        assert response.status_code == codes.FORBIDDEN

    def test_create_email_campaign_with_non_existing_base_campaign(self, smartlist_first, token_first):
        """
        This creates an email-campaign with non-existing base_campaign_id. This should result in ResourceNotFound
        error.
        """
        campaign_data = get_email_campaign_data(fake.uuid4(), smartlist_first['id'])
        non_existing_base_campaign_id = CampaignsTestsHelpers.get_non_existing_id(BaseCampaign)
        campaign_data['base_campaign_id'] = non_existing_base_campaign_id
        response = send_request(self.HTTP_METHOD, self.URL, token_first, campaign_data)
        assert response.status_code == codes.NOT_FOUND


class TestCampaignOverview(object):
    """
    Here are the tests for Campaign Overview.
    """
    URL = EmailCampaignApiUrl.BASE_CAMPAIGN
    HTTP_METHOD = HttpMethods.GET
    EXPECTED_BLASTS = 1
    EXPECTED_SENDS = 1
    SENT_ONE_EMAIL_CAMPAIGN = 1
    EXPECTED_EVENTS = 1
    EXPECTED_INVITES = 1

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int())

    def test_orphaned_base_campaign(self, base_campaign, token_first):
        """
        This gets overview of an orphaned base campaign. It should result in bad request error.
        """
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert response.status_code == codes.BAD, response.text

    def test_with_email_campaign(self, base_campaign, token_first, email_campaign_with_base_id):
        """
        This gets overview of a base campaign associated with an email-campaign. It should get email-campaign's
        statistics.
        """
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert_email_campaign_overview(response, sent_campaigns_count=self.SENT_ONE_EMAIL_CAMPAIGN,
                                       expected_blasts=self.EXPECTED_BLASTS, expected_sends=self.EXPECTED_SENDS)

    def test_with_two_email_campaigns(self, base_campaign, token_first, email_campaign_with_base_id,
                                      email_campaign_same_domain):
        """
        This gets overview of a base campaign associated with two email campaigns. It should get email-campaigns'
        statistics.
        """
        associated_campaigns = len([email_campaign_same_domain, email_campaign_with_base_id])
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert_event_overview(response)
        assert_email_campaign_overview(response, sent_campaigns_count=associated_campaigns,
                                       expected_blasts=self.EXPECTED_BLASTS, expected_sends=self.EXPECTED_SENDS)

    def test_with_linked_event_with_no_rsvp(self, base_campaign, token_first, base_campaign_event):
        """
        This gets overview of a base campaign associated with one event. It should get event's statistics.
        """
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert_event_overview(response, expected_events=self.EXPECTED_EVENTS)
        assert_email_campaign_overview(response)

    def test_with_linked_event_with_one_rsvp(self, base_campaign, token_first, base_campaign_event_with_rsvp):
        """
        This gets overview of a base campaign associated with one event. It should get event's statistics.
        """
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert_event_overview(response, expected_events=self.EXPECTED_EVENTS, expected_invites=self.EXPECTED_INVITES)
        assert_email_campaign_overview(response)

    def test_with_linked_event_and_email_campaign(self, base_campaign, token_first, base_campaign_event_with_rsvp,
                                                  email_campaign_with_base_id):
        """
        This gets overview of a base campaign associated with one event and an email-campaign.
        It should get event's and email-campaign's statistics.
        """
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert_event_overview(response, expected_events=self.EXPECTED_EVENTS, expected_invites=self.EXPECTED_INVITES)
        assert_email_campaign_overview(response, sent_campaigns_count=self.SENT_ONE_EMAIL_CAMPAIGN,
                                       expected_blasts=self.EXPECTED_BLASTS, expected_sends=self.EXPECTED_SENDS)


class TestDeleteEventWithCampaign(object):
    """
    Here are the tests for deleting events and campaigns associated with them.
    """

    def test_delete_event_and_associated_campaigns(self, base_campaign, token_first, base_campaign_event_second,
                                                  email_campaign_with_base_id, new_event_in_db_second):
        """
        This tests if we delete an event through api then campaigns associated with it should be deleted or archived.
        """
        response = requests.delete(SocialNetworkApiUrl.EVENT % new_event_in_db_second['id'],
                                   headers=auth_header(token_first))
        campaign_response = requests.get(EmailCampaignApiUrl.CAMPAIGN % email_campaign_with_base_id['id'],
                                         headers=auth_header(token_first))
        campaign_content = campaign_response.json()
        assert campaign_content['email_campaign']['is_hidden']

        event_response = requests.get(SocialNetworkApiUrl.EVENT % new_event_in_db_second['id'],
                                      headers=auth_header(token_first))
        event_content = event_response.json()
        assert event_content['event']['is_deleted_from_vendor'] and event_content['event']['is_hidden']


class TestEventCampaignActivity(object):
    """
    Here are the tests for activity of event campaign
    """

    @pytest.mark.wy
    def test_event_campaign_with_client_id(self, event_campaign_with_client_id):
        """
        This gets an event campaign with client id, tests its open activity.
        """
        response = event_campaign_with_client_id['response']
        campaign = event_campaign_with_client_id['campaign']
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
        assert response.status_code == requests.codes.OK
        db.session.commit()
        opens_count_after = email_campaign_blast.opens
        hit_count_after = url_conversion.hit_count
        assert opens_count_after == opens_count_before + 1
        assert hit_count_after == hit_count_before + 1
        campaign_send = EmailCampaignSend.query.filter(EmailCampaignSend.campaign_id == campaign.id).first()
        CampaignsTestsHelpers.assert_for_activity(campaign.user_id, Activity.MessageIds.CAMPAIGN_EVENT_OPEN,
                                                  campaign_send.id)
        UrlConversion.delete(url_conversion)

    @pytest.mark.wy
    def test_activity_send_event_campaign(self, token_first, event_campaign):
        """
        This gets an event campaign, tests its send activity.
        """
        response = send_request('post', EmailCampaignApiUrl.SEND % event_campaign.id, token_first)
        assert response.status_code == codes.OK, response.text
        db.session.commit()
        assert_campaign_send(response, event_campaign, event_campaign.user_id)
