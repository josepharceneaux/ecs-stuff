"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have tests for API
    - /v1/base-campaigns
    - /v1/base-campaigns/:base-campaign_id/link-event/:event_id
"""
# Packages
import json
import requests
from requests import codes

# Service Specific
from ...models.db import db
from ...models.event import Event
from ...tests.sample_data import fake
from ...routes import EmailCampaignApiUrl
from ..tests_helpers import CampaignsTestsHelpers
from ...models.base_campaign import (BaseCampaign, BaseCampaignEvent)

__author__ = 'basit'


class TestCreateBaseCampaigns(object):
    """
    Here are the tests of /v1/base-campaigns
    """
    URL = EmailCampaignApiUrl.BASE_CAMPAIGNS

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('post', self.URL)

    def test_with_valid_data(self, headers):
        """
        Data is valid. Base campaign should be created
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.CREATED
        assert response.json()['id']

    def test_with_missing_required_fields(self, headers):
        """
        Data does not contain some required fields. It should result in bad request error.
        """
        for key in ('name', 'description'):
            data = CampaignsTestsHelpers.base_campaign_data()
            del data[key]
            response = requests.post(self.URL, headers=headers, data=json.dumps(data))
            assert response.status_code == codes.BAD

    def test_with_empty_required_fields(self, headers):
        """
        Data does not contain valid values for some required fields. It should result in bad request error.
        """
        for key in ('name', 'description'):
            data = CampaignsTestsHelpers.base_campaign_data()
            data[key] = ''
            response = requests.post(self.URL, headers=headers, data=json.dumps(data))
            assert response.status_code == codes.BAD

    def test_with_same_name(self, headers):
        """
        Tries to create base-campaign with existing name. It should result in bad request error.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.BAD

    def test_with_same_name_in_other_domain(self, headers, headers_other):
        """
        Tries to create base-campaign in other domain with existing name. It should allow creation.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = requests.post(self.URL, headers=headers_other, data=json.dumps(data))
        assert response.status_code == codes.CREATED


class TestBaseCampaignEvent(object):
    """
    Here are tests to link an event with base campaign
    """
    URL = EmailCampaignApiUrl.BASE_CAMPAIGN_EVENT

    def test_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('post', self.URL % (fake.random_int(), fake.random_int()))

    def test_with_valid_data(self, base_campaign, meetup_event, headers):
        """
        This hits the API with valid event and base campaign.
        """
        response = requests.post(self.URL % (base_campaign['id'], meetup_event['id']), headers=headers)
        assert response.status_code == codes.CREATED, response.text
        assert response.json()['id']
        db.session.commit()
        base_campaign_event = BaseCampaignEvent.get_by_id(response.json()['id'])
        assert base_campaign_event.event_id == meetup_event['id']
        assert base_campaign_event.base_campaign_id == base_campaign['id']

    def test_with_not_owned_event(self, base_campaign, meetup_event, headers_other):
        """
        This hits the API with valid event and base campaign.
        """
        response = requests.post(self.URL % (base_campaign['id'], meetup_event['id']), headers=headers_other)
        assert response.status_code == codes.FORBIDDEN, response.text

    def test_with_non_existing_event(self, base_campaign, headers):
        """
        This should result in resource not found error.
        """
        non_existing_event_id = CampaignsTestsHelpers.get_non_existing_ids(Event)
        response = requests.post(self.URL % (base_campaign['id'], non_existing_event_id), headers=headers)
        assert response.status_code == codes.NOT_FOUND, response.text

    def test_with_non_existing_base_campaign(self, meetup_event, headers):
        """
        This should result in resource not found error.
        """
        non_existing_base_campaign_id = CampaignsTestsHelpers.get_non_existing_ids(BaseCampaign)
        response = requests.post(self.URL % (non_existing_base_campaign_id, meetup_event['id']), headers=headers)
        assert response.status_code == codes.NOT_FOUND, response.text
