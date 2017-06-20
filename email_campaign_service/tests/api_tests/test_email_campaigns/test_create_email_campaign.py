"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoint(s)

    - POST /v1/email-campaigns

This file contains tests for creation of an email-campaign

"""
# Packages
import pytest

# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.tests.conftest import fake
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import EmailClient
from email_campaign_service.tests.modules.__init__ import CAMPAIGN_OPTIONAL_FIELDS
from app_common.common.custom_errors.campaign import (INVALID_REQUEST_BODY, MISSING_FIELD,
                                                      INVALID_DATETIME_VALUE, INVALID_INPUT,
                                                      INVALID_DATETIME_FORMAT, SMARTLIST_NOT_FOUND,
                                                      SMARTLIST_FORBIDDEN)
from email_campaign_service.common.error_handling import (InvalidUsage, UnprocessableEntity)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import (EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS,
                                                                  create_data_for_campaign_creation_with_all_parameters)
from email_campaign_service.common.campaign_services.tests.modules.email_campaign_helper_functions import \
    create_email_campaign_via_api, create_data_for_campaign_creation, create_scheduled_email_campaign_data


class TestCreateCampaign(object):
    """
    Here are the tests for creating a campaign from endpoint /v1/email-campaigns
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.CAMPAIGNS
    BLASTS_URL = EmailCampaignApiUrl.BLASTS

    def test_create_campaign_with_invalid_token(self):
        """
        Here we try to create email campaign with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_create_email_campaign_without_client_id(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        Here we provide valid data to create an email-campaign without email_client_id.
        It should get OK response.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object
        assert resp_object['campaign']['id']

    def test_create_email_campaign_with_client_id(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        Here we provide valid data to create an email-campaign with email_client_id.
        It should get OK response.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        campaign_data['email_client_id'] = EmailClient.get_id_by_name('Browser')
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object

    def test_create_email_campaign_with_outgoing_email_client(self, access_token_first, smartlist_user1_domain1_in_db,
                                                              outgoing_email_client, headers):
        """
        Here we provide valid data to create an email-campaign with email_client_credentials_id.
        It should get OK response.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        # GET email-client-id
        response = requests.get(EmailCampaignApiUrl.EMAIL_CLIENTS + '?type=outgoing', headers=headers)
        assert response.ok
        assert response.json()
        email_client_response = response.json()['email_client_credentials']
        assert len(email_client_response) == 1
        campaign_data['email_client_credentials_id'] = email_client_response[0]['id']
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object and resp_object['campaign']

    def test_create_campaign_and_send_now(self, access_token_first, headers, smartlist_user1_domain1):
        """
        Here we assume user has clicked the button "Send Now" from UI, it should send campaign immediately.
        """
        expected_sends = 2
        subject = '{}-send_campaign_now'.format(fake.uuid4())
        campaign_data = create_data_for_campaign_creation(smartlist_user1_domain1['id'], subject=subject)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object
        assert resp_object['campaign']['id']
        url = EmailCampaignApiUrl.CAMPAIGN % resp_object['campaign']['id']
        response = requests.get(url, headers=headers)
        assert response.status_code == codes.OK
        assert response.json()['email_campaign']
        email_campaign = response.json()['email_campaign']
        campaign_blast = CampaignsTestsHelpers.get_blasts_with_polling(email_campaign, access_token_first,
                                                                       self.BLASTS_URL % email_campaign['id'])
        CampaignsTestsHelpers.assert_blast_sends(email_campaign, expected_sends,
                                                 blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'],
                                                                                        campaign_blast[0]['id']),
                                                 access_token=access_token_first)

    def test_create_email_campaign_with_optional_parameters(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        The test is to examine that the email-campaign is created with optional parameter or not.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_with_optional_parameters' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(smartlist_user1_domain1_in_db['id'], subject=subject)
        for param in EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS:
            campaign_data.update(param)
            response = create_email_campaign_via_api(access_token_first, campaign_data)
            assert response.status_code == requests.codes.CREATED
            resp_object = response.json()
            assert 'campaign' in resp_object
            assert resp_object['campaign']['id']

    def test_create_email_campaign_except_single_parameter(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        Here we provide valid data to create an email-campaign with all parameter except single parameter.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_except_single_parameter' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation_with_all_parameters(smartlist_user1_domain1_in_db['id'],
                                                                              subject=subject)
        for param in CAMPAIGN_OPTIONAL_FIELDS:
            campaign_test_data = campaign_data.copy()
            del campaign_test_data[param]
            response = create_email_campaign_via_api(access_token_first, campaign_test_data)
            assert response.status_code == requests.codes.CREATED
            resp_object = response.json()
            assert 'campaign' in resp_object
            assert resp_object['campaign']['id']

    def test_campaign_creation_with_invalid_data(self, access_token_first):
        """
        Trying to create a campaign with 1) no data and 2) Non-JSON data. It should result in invalid usage error.
        """
        campaign_data = create_scheduled_email_campaign_data()
        for data in (campaign_data, None):
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first,
                                                             data=data, is_json=False,
                                                             expected_error_code=INVALID_REQUEST_BODY[1])

    def test_create_email_campaign_with_incoming_email_client(self, access_token_first, smartlist_user1_domain1_in_db,
                                                              email_clients, headers):
        """
        Here we provide email-client of type "incoming". email-campaign should not be created.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        # GET email-client-id
        response = requests.get(EmailCampaignApiUrl.EMAIL_CLIENTS + '?type=incoming', headers=headers)
        assert response.ok
        assert response.json()
        email_client_response = response.json()['email_client_credentials']
        assert len(email_client_response) == 2
        campaign_data['email_client_credentials_id'] = email_client_response[0]['id']
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.BAD

    def test_create_email_campaign_with_invalid_string_values(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        This tries to create an email campaign with invalid string value of fields `name`, `subject` and `body_html`.
        It should result in invalid usage error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_id=smartlist_user1_domain1_in_db['id'])
        for field in ('name', 'subject', 'body_html'):
            CampaignsTestsHelpers.request_with_invalid_string(self.HTTP_METHOD, self.URL,
                                                              access_token_first, campaign_data,
                                                              field=field, expected_error_code=INVALID_INPUT[1])

    def test_create_email_campaign_without_required_fields(self, access_token_first,
                                                           invalid_data_for_campaign_creation):
        """
        Here we try to create an email-campaign with missing required fields. It should
        result in invalid usage error for each missing field.
        Required fields are 'name', 'subject', 'body_html', 'frequency_id', 'list_ids'.
        """
        campaign_data, missing_key = invalid_data_for_campaign_creation
        response = CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first,
                                                                    data=campaign_data,
                                                                    expected_error_code=MISSING_FIELD[1])
        assert missing_key in response.json()['error']['message']

    def test_create_email_campaign_with_invalid_format_of_smartlist_ids(self, access_token_first):
        """
        Here we try to create an email-campaign with list_ids not in list format. It should
        result in invalid usage error.
        """
        campaign_data = create_scheduled_email_campaign_data()
        campaign_data['list_ids'] = fake.random_number()  # 'list_ids' must be a list
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL, access_token_first,
                                                         data=campaign_data, expected_error_code=INVALID_INPUT[1])

    def test_create_email_campaign_with_invalid_smartlist_ids(self, access_token_first):
        """
        This is a test to create email-campaign with invalid smartlist_ids.
        Invalid smartlist ids include  non-integer id, empty list, duplicate items in list etc.
        Status code should be 400 and campaign should not be created.
        """
        campaign_data = create_scheduled_email_campaign_data()
        CampaignsTestsHelpers.campaign_create_or_update_with_invalid_smartlist(self.HTTP_METHOD, self.URL,
                                                                               access_token_first,
                                                                               campaign_data, key='list_ids',
                                                                               expected_error_code=INVALID_INPUT[1])

    def test_create_email_campaign_with_deleted_smartlist_id(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        This is a test to create email-campaign with deleted smartlist id. It should result in
        Resource not found error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL, access_token_first,
                                                                  campaign_data['list_ids'][0],
                                                                  expected_error_code=SMARTLIST_NOT_FOUND[1],
                                                                  data=campaign_data)

    def test_create_email_campaign_with_smartlist_id_of_other_domain(self, access_token_first, smartlist_other_in_db):
        """
        This is a test to create email-campaign with deleted smartlist id. It should result in
        Resource not found error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_other_in_db['id'])
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL, access_token_first, campaign_data,
                                                          expected_error_code=SMARTLIST_FORBIDDEN[1])

    def test_create_campaign_with_invalid_frequency_id(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        Trying to schedule a campaign with invalid frequency_id. It should result in bad request error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        CampaignsTestsHelpers.campaign_schedule_or_reschedule_with_invalid_frequency_id(
            self.HTTP_METHOD, self.URL, access_token_first, campaign_data, expected_error_code=INVALID_INPUT[1])

    def test_create_campaign_with_invalid_datetime_format(self, access_token_first, smartlist_user1_domain1_in_db):
        """
        This is a test to schedule a campaign with invalid datetime formats. It should result in invalid usage error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        CampaignsTestsHelpers.invalid_datetime_format(self.HTTP_METHOD, self.URL, access_token_first, campaign_data,
                                                      expected_error_code=INVALID_DATETIME_FORMAT[1])

    def test_create_periodic_email_campaign_with_missing_start_and_end_datetime(self, access_token_first,
                                                                                smartlist_user1_domain1_in_db):
        """
        Here we try to create an email-campaign with frequency DAILY for which start_datetime and end_datetime
        will be required fields. But we are not giving those fields. It should result in UnprocessableEntity error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        expected_status_code = UnprocessableEntity.http_status_code()
        campaign_data['frequency_id'] = Frequency.DAILY
        CampaignsTestsHelpers.missing_fields_in_schedule_data(self.HTTP_METHOD, self.URL, access_token_first,
                                                              campaign_data,
                                                              expected_status_code=expected_status_code,
                                                              expected_error_code=MISSING_FIELD[1])

    def test_create_periodic_email_campaign_with_past_start_and_end_datetime(self, access_token_first,
                                                                             smartlist_user1_domain1_in_db):
        """
        Here we try to create an email-campaign with frequency DAILY for which start_datetime and end_datetime
        are expected to be in past. It should result in UnprocessableEntity error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_user1_domain1_in_db['id'])
        expected_status_code = UnprocessableEntity.http_status_code()
        campaign_data['frequency_id'] = Frequency.DAILY
        CampaignsTestsHelpers.request_with_past_start_and_end_datetime(self.HTTP_METHOD, self.URL, access_token_first,
                                                                       campaign_data,
                                                                       expected_status_code=expected_status_code,
                                                                       expected_error_code=INVALID_DATETIME_VALUE[1])

    def test_create_email_campaign_with_start_datetime_ahead_of_end_datetime(self, access_token_first,
                                                                             smartlist_user1_domain1_in_db):
        """
        Here we try to create an email-campaign with frequency DAILY. Here we provide start_datetime
        to be ahead of end_datetime. It should result in UnprocessableEntity error.
        """
        expected_status_code = UnprocessableEntity.http_status_code()
        campaign_data = create_data_for_campaign_creation(smartlist_user1_domain1_in_db['id'])
        campaign_data['frequency_id'] = Frequency.DAILY
        CampaignsTestsHelpers.start_datetime_greater_than_end_datetime(self.HTTP_METHOD, self.URL, access_token_first,
                                                                       data=campaign_data,
                                                                       expected_status_code=expected_status_code,
                                                                       expected_error_code=INVALID_DATETIME_VALUE[1])

    def test_create_email_campaign_with_invalid_email_client_id(self, access_token_first,
                                                                smartlist_user1_domain1_in_db):
        """
        Here we try to create an email-campaign with invalid email-client-id. It should
        result in invalid usage error.
        """
        campaign_data = create_data_for_campaign_creation(smartlist_user1_domain1_in_db['id'])
        campaign_data['email_client_id'] = CampaignsTestsHelpers.get_non_existing_id(EmailClient)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == InvalidUsage.http_status_code()
        json_response = response.json()
        assert 'email_client_id' in json_response['error']['message']
