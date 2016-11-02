"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have tests for API
    - /v1/base-campaigns
    - /v1/base-campaigns/:base-campaign_id/link-event/:event_id
"""
# Packages
from requests import codes

# Service Specific
from ...models.db import db
from ...models.event import Event
from ...tests.sample_data import fake
from ...routes import EmailCampaignApiUrl
from ...constants import HttpMethods
from ..tests_helpers import CampaignsTestsHelpers, send_request
from ...models.base_campaign import (BaseCampaign, BaseCampaignEvent)
from modules.helper_functions import (create_data_for_campaign_creation, assert_email_campaign_overview,
                                      assert_event_overview)

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
        Tries to create base-campaign with existing name. It should result in bad request error.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = send_request(self.HTTP_METHOD, self.URL, token_first, data)
        assert response.status_code == codes.BAD

        # Create campaign second time with other user of same domain
        response = send_request(self.HTTP_METHOD, self.URL, token_same_domain, data)
        assert response.status_code == codes.BAD

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

    def test_with_valid_data(self, base_campaign, event_in_db, token_first):
        """
        This hits the API with valid event and base campaign.
        """
        response = send_request(self.HTTP_METHOD, self.URL % (base_campaign['id'], event_in_db['id']), token_first)
        assert response.status_code == codes.CREATED, response.text
        assert response.json()['id']
        db.session.commit()
        base_campaign_event = BaseCampaignEvent.get_by_id(response.json()['id'])
        assert base_campaign_event.event_id == event_in_db['id']
        assert base_campaign_event.base_campaign_id == base_campaign['id']

    def test_with_not_owned_event(self, base_campaign, event_in_db, token_second):
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


class TestEventEmailCampaign(object):
    """
    Here we link an email-campaign with event and base-campaign.
    For this we need to create an email-campaign with base_campaign_id.
    """
    URL = EmailCampaignApiUrl.CAMPAIGNS
    HTTP_METHOD = HttpMethods.POST

    def test_create_email_campaign_with_base_id(self, smartlist_first, base_campaign, token_first):
        """
        This creates an email-campaign with base_campaign_id
        """
        campaign_data = create_data_for_campaign_creation(fake.uuid4(), smartlist_first['id'])
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
        campaign_data = create_data_for_campaign_creation(fake.uuid4(), smartlist_first['id'])
        campaign_data['base_campaign_id'] = base_campaign_other['id']
        response = send_request(self.HTTP_METHOD, self.URL, token_first, campaign_data)
        assert response.status_code == codes.FORBIDDEN

    def test_create_email_campaign_with_non_existing_base_campaign(self, smartlist_first, token_first):
        """
        This creates an email-campaign with non-existing base_campaign_id. This should result in ResourceNotFound
        error.
        """
        campaign_data = create_data_for_campaign_creation(fake.uuid4(), smartlist_first['id'])
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
        assert response.status_code == codes.BAD

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
        expected_events = 1
        response = send_request(self.HTTP_METHOD, self.URL % base_campaign['id'], token_first)
        assert_event_overview(response, expected_events=expected_events)
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
