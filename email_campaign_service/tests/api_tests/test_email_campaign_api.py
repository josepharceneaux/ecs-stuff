"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    1 - GET /v1/email-campaigns
    2 - GET /v1/email-campaigns/:id
    3 - POST /v1/email-campaigns

"""
# Packages
import time
import pytest
from random import randint
from datetime import datetime, timedelta

# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.tests.conftest import fake
from email_campaign_service.common.models.user import Role
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.models.email_campaign import EmailClient
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.tests.modules.__init__ import CAMPAIGN_OPTIONAL_FIELDS
from email_campaign_service.common.utils.api_utils import MAX_PAGE_SIZE, SORT_TYPES
from email_campaign_service.common.routes import (EmailCampaignApiUrl, HEALTH_CHECK)
from email_campaign_service.common.utils.test_utils import (PAGINATION_INVALID_FIELDS,
                                                            PAGINATION_EXCEPT_SINGLE_FIELD)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.error_handling import (InvalidUsage, UnprocessableEntity, ForbiddenError)
from email_campaign_service.tests.modules.handy_functions import (assert_valid_campaign_get,
                                                                  get_campaign_or_campaigns,
                                                                  assert_talent_pipeline_response,
                                                                  create_email_campaign_in_db,
                                                                  EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS,
                                                                  create_data_for_campaign_creation_with_all_parameters)
from email_campaign_service.common.campaign_services.tests.modules.email_campaign_helper_functions import \
    create_email_campaign_via_api, create_data_for_campaign_creation, create_scheduled_email_campaign_data


class TestGetCampaigns(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.CAMPAIGNS

    def test_get_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('get', EmailCampaignApiUrl.CAMPAIGNS, None)

    def test_get_campaign_of_other_domain(self, email_campaign_in_other_domain, access_token_first):
        """
        Here we try to GET a campaign which is in some other domain. It should result-in
         ForbiddenError.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            'get', EmailCampaignApiUrl.CAMPAIGN % email_campaign_in_other_domain.id,
            access_token_first)

    def test_get_by_campaign_id(self, campaign_with_candidate_having_no_email, access_token_first, talent_pipeline):
        """
        This is the test to GET the campaign by providing campaign_id. It should get OK response
        """
        email_campaign = get_campaign_or_campaigns(
            access_token_first, campaign_id=campaign_with_candidate_having_no_email.id)
        assert_valid_campaign_get(email_campaign, [campaign_with_candidate_having_no_email])

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_by_campaign_id_with_fields(self, campaign_with_candidate_having_no_email, access_token_first,
                                            talent_pipeline):
        """
        This is the test to GET the campaign by providing campaign_id & filters.
        It should get OK response
        """
        fields = ['id', 'subject', 'body_html', 'body_text', 'is_hidden']

        email_campaign = get_campaign_or_campaigns(
            access_token_first,
            campaign_id=campaign_with_candidate_having_no_email.id,
            fields=fields)
        assert_valid_campaign_get(email_campaign, [campaign_with_candidate_having_no_email],
                                  fields=fields)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first, fields=fields)

    def test_get_all_campaigns_in_user_domain(self, email_campaign_user1_domain1_in_db, email_campaign_of_user_second,
                                              email_campaign_in_other_domain, access_token_first, talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain.
        Here two campaigns have been created by different users of same domain. Total count
        should be 2. Here we also create another campaign in some other domain but it shouldn't
        be there in GET response.
        """
        # Test GET api of email campaign
        email_campaigns = get_campaign_or_campaigns(access_token_first)
        assert len(email_campaigns) == 2
        reference_campaigns = [email_campaign_user1_domain1_in_db, email_campaign_of_user_second]
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_campaign_with_email_client(self, email_campaign_with_outgoing_email_client, access_token_first):
        """
        Here we try to GET a campaign which is created by email-client. It should not get any error.
        """
        campaign = email_campaign_with_outgoing_email_client
        fields = ['email_client_credentials_id']
        email_campaign = get_campaign_or_campaigns(access_token_first,
                                                   campaign_id=campaign['id'],
                                                   fields=fields)
        assert_valid_campaign_get(email_campaign, [campaign], fields=fields)

    def test_get_campaigns_with_paginated_response(self, email_campaign_user1_domain1_in_db,
                                                   email_campaign_of_user_second,
                                                   access_token_first, talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain using
        paginated response. Here two campaigns have been created by different users of same domain.
        """
        # Test GET api of email campaign using per_page=1 and default page=1.
        # It should return first campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?per_page=1')
        assert len(email_campaigns) == 1
        reference_campaigns = [email_campaign_user1_domain1_in_db, email_campaign_of_user_second]
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

        # Test GET api of email campaign using per_page=1 for page=2. It should
        # return second campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?per_page=1&page=2')
        assert len(email_campaigns) == 1
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)

        # Test GET api of email campaign with 2 results per_page
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?per_page=2')
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)
        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

        # Test GET api of email campaign with default per_page=10 and page =1.
        # It should get both campaigns in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?&page=1')
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)

        # Test GET api of email campaign with page = 2. No campaign should be received in response
        # as we have created only two campaigns so far and default per_page is 10.
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?page=2')
        assert len(email_campaigns) == 0

    def test_get_campaigns_with_invalid_user_id(self, headers):
        """
        Test GET API of email_campaigns for getting all campaigns for particular user_id where user_id
        is not in valid format. i.e. we are passing string rather that integer value. It should result in Bad Request 
        Error.
        """
        url = EmailCampaignApiUrl.CAMPAIGNS + '?user_id={}'.format(fake.word())
        response = requests.get(url, headers=headers)
        assert response.status_code == requests.codes.BAD, response.text

    def test_get_campaigns_with_user_id_of_same_domain(self, email_campaign_user1_domain1_in_db, access_token_first,
                                                       email_campaign_of_user_second, user_same_domain):
        """
        Test GET API of email_campaigns for getting all campaigns for a particular user_id of same domain.
        It should return one campaign.
        """
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    query_params='?user_id={}'.format(user_same_domain.id))
        assert len(email_campaigns) == 1  # As we have only 1 campaign created by other user of same domain
        assert email_campaigns[0]['user_id'] == user_same_domain.id

    def test_get_campaigns_with_user_id_of_other_domain(self, headers, user_from_diff_domain):
        """
        Test GET API of email_campaigns for getting all campaigns for a particular user_id of some other domain.
        It should result in Forbidden Error.
        """
        url = EmailCampaignApiUrl.CAMPAIGNS + '?user_id={}'.format(user_from_diff_domain.id)
        response = requests.get(url, headers=headers)
        assert response.status_code == ForbiddenError.http_status_code()

    def test_get_campaigns_with_user_id_of_other_domain_with_talent_admin_role(self, user_first, access_token_first,
                                                                               user_from_diff_domain,
                                                                               email_campaign_in_other_domain):
        """
        Test GET API of email_campaigns for getting all campaigns for a particular user_id of some other domain.
        It should return the campaign created by that user as requested user has appropriate role.
        """
        user_first.update(role_id=Role.get_by_name(Role.TALENT_ADMIN).id)
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    query_params='?user_id={}'.format(user_from_diff_domain.id))
        assert len(email_campaigns) == 1  # As we have only 1 campaign created by the user of other domain
        assert email_campaigns[0]['user_id'] == user_from_diff_domain.id

    def test_get_campaigns_with_invalid_sort_type(self, headers):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain with invalid value
        of parameter sort_type. Valid values are "ASC" or "DESC"
        This should result in invalid usage error.
        """
        url = EmailCampaignApiUrl.CAMPAIGNS + '?sort_type=%s' % fake.word()
        response = requests.get(url, headers=headers)
        assert response.status_code == requests.codes.BAD
        for sort_type in SORT_TYPES:
            assert sort_type in response.json()['error']['message']

    def test_get_campaigns_with_invalid_value_of_sort_by(self, headers):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain with invalid value
        of parameter sort_by. Valid values are "name" and "added_datetime".
        This should result in invalid usage error.
        """
        url = EmailCampaignApiUrl.CAMPAIGNS + '?sort_by=%s' % fake.sentence()
        response = requests.get(url, headers=headers)
        assert response.status_code == requests.codes.BAD

    def test_get_campaigns_with_invalid_value_of_is_hidden(self, headers):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain with invalid value
        of parameter is_hidden. Valid values are 0 or 1.
        This should result in invalid usage error.
        """
        url = EmailCampaignApiUrl.CAMPAIGNS + '?is_hidden=%d' % randint(2, 10)
        response = requests.get(url, headers=headers)
        assert response.status_code == requests.codes.BAD

    def test_get_campaigns_with_paginated_response_using_invalid_per_page(self, headers):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain using
        paginated response. Here we use per_page to be greater than maximum allowed value. It should
        result in invalid usage error.
        """
        url = EmailCampaignApiUrl.CAMPAIGNS + '?per_page=%d' % randint(MAX_PAGE_SIZE + 1, 2 * MAX_PAGE_SIZE)
        response = requests.get(url, headers=headers)
        assert response.status_code == requests.codes.BAD
        assert str(MAX_PAGE_SIZE) in response.json()['error']['message']

    @pytest.mark.qa
    def test_get_campaign_with_invalid_field_one_by_one(self, headers):
        """
         This test make sure that data is not retrieved with invalid fields and also
         assure us of all possible checks are handled for every field. That's why the
         test is executed with one by one invalid field.
        """
        for param in PAGINATION_INVALID_FIELDS:
            response = requests.get(url=self.URL + param, headers=headers)
            assert response.status_code == requests.codes.BAD_REQUEST

    @pytest.mark.qa
    def test_get_all_campaigns_in_desc(self, user_first, user_same_domain, access_token_first):

        """
        This test is to make sure the GET endpoint get_all_email_campaigns
        is retrieving all campaigns in descending order according of added_datetime'
        """
        # Test GET api of email campaign
        create_email_campaign_in_db(user_first.id)
        time.sleep(2)
        create_email_campaign_in_db(user_same_domain.id)
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?sort_type=DESC')
        assert email_campaigns[0]['added_datetime'] > email_campaigns[1]['added_datetime']

    @pytest.mark.qa
    def test_get_all_campaigns_in_asc(self, user_first, user_same_domain, access_token_first):
        """
        This test is to make sure the GET endpoint get_all_email_campaigns
        is retrieving all campaigns in ascending order according of added_datetime'
        """
        # Test GET api of email campaign
        create_email_campaign_in_db(user_first.id)
        time.sleep(2)
        create_email_campaign_in_db(user_same_domain.id)
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?sort_type=ASC')
        assert email_campaigns[0]['added_datetime'] < email_campaigns[1]['added_datetime']

    @pytest.mark.qa
    def test_get_campaign_except_single_field(self, headers):
        """
        This test certify that data of campaign is retrieved with url having all fields except single field.
        Should return 200 ok status.
        """
        for param in PAGINATION_EXCEPT_SINGLE_FIELD:
            # sort_by name is for email campaign pagination
            response = requests.get(url=EmailCampaignApiUrl.CAMPAIGNS + param % 'name', headers=headers)
            assert response.status_code == requests.codes.OK


class TestCreateCampaign(object):
    """
    Here are the tests for creating a campaign from endpoint /v1/email-campaigns
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.CAMPAIGNS
    BLASTS_URL = EmailCampaignApiUrl.BLASTS

    def test_create_campaign_with_invalid_token(self):
        """
        Here we try to create email campaign with invalid access token
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_create_email_campaign_without_client_id(self, access_token_first, smartlist_first):
        """
        Here we provide valid data to create an email-campaign without email_client_id.
        It should get OK response.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_first['id'])
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object
        assert resp_object['campaign']['id']

    def test_create_email_campaign_with_client_id(self, access_token_first, smartlist_first):
        """
        Here we provide valid data to create an email-campaign with email_client_id.
        It should get OK response.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_first['id'])
        campaign_data['email_client_id'] = EmailClient.get_id_by_name('Browser')
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object

    def test_create_email_campaign_with_outgoing_email_client(self, access_token_first, smartlist_first,
                                                              outgoing_email_client, headers):
        """
        Here we provide valid data to create an email-campaign with email_client_credentials_id.
        It should get OK response.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_first['id'])
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

    def test_create_email_campaign_with_incoming_email_client(self, access_token_first, smartlist_first,
                                                              email_clients, headers):
        """
        Here we provide email-client of type "incoming". email-campaign should not be created.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_first['id'])
        # GET email-client-id
        response = requests.get(EmailCampaignApiUrl.EMAIL_CLIENTS + '?type=incoming', headers=headers)
        assert response.ok
        assert response.json()
        email_client_response = response.json()['email_client_credentials']
        assert len(email_client_response) == 2
        campaign_data['email_client_credentials_id'] = email_client_response[0]['id']
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.BAD

    def test_create_campaign_with_non_json_data(self, access_token_first):
        """
        Here we try to create email campaign with non-JSON data. It should result in
        invalid usage error.
        """
        response = create_email_campaign_via_api(access_token_first,
                                                 {'campaign_data': 'data'}, is_json=False)
        assert response.status_code == InvalidUsage.http_status_code()

    def test_create_email_campaign_with_whitespace_campaign_name(self, access_token_first):
        """
        This tries to create an email campaign with whitespace as campaign name.
        It should result in invalid usage error as campaign_name is required field.
        """
        name = '       '
        campaign_data = create_scheduled_email_campaign_data(smartlist_id=None, campaign_name=name)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        resp_object = response.json()
        assert response.status_code == InvalidUsage.http_status_code()
        assert 'error' in resp_object
        assert resp_object['error']['message'] == 'name is required'

    def test_create_email_campaign_with_missing_required_fields(self, access_token_first,
                                                                invalid_data_for_campaign_creation):
        """
        Here we try to create an email-campaign with missing required fields. It should
        result in invalid usage error for each missing field.
        Required fields are 'name', 'subject', 'body_html', 'frequency_id', 'list_ids'.
        """
        campaign_data, missing_key = invalid_data_for_campaign_creation
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == InvalidUsage.http_status_code()
        json_response = response.json()
        assert missing_key in json_response['error']['message']

    def test_create_email_campaign_with_invalid_format_of_smartlist_ids(self, access_token_first):
        """
        Here we try to create an email-campaign with list_ids not in list format. It should
        result in invalid usage error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_id=None)
        campaign_data['list_ids'] = fake.random_number()  # 'list_ids' must be a list
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == InvalidUsage.http_status_code()
        json_response = response.json()
        assert 'list_ids' in json_response['error']['message']

    def test_create_email_campaign_with_invalid_smartlist_ids(self, access_token_first):
        """
        This is a test to create email-campaign with invalid smartlist_ids.
        Invalid smartlist ids include Non-existing id, non-integer id, empty list, duplicate items in list etc.
        Status code should be 400 and campaign should not be created.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_id=None)
        CampaignsTestsHelpers.campaign_create_or_update_with_invalid_smartlist(self.HTTP_METHOD, self.URL,
                                                                               access_token_first,
                                                                               campaign_data, key='list_ids')

    def test_create_email_campaign_with_deleted_smartlist_id(self, access_token_first, smartlist_first):
        """
        This is a test to create email-campaign with deleted smartlist id. It should result in
        Resource not found error.
        """
        campaign_data = create_scheduled_email_campaign_data(smartlist_first['id'])
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL, access_token_first,
                                                                  campaign_data['list_ids'][0], campaign_data)

    def test_create_email_campaign_with_no_start_datetime(self, access_token_first, smartlist_first):
        """
        Here we try to create an email-campaign with frequency DAILY for which start_datetime will be
        a required field. But we are not giving start_datetime. It should result in
        UnprocessableEntity error.
        """
        campaign_data = create_data_for_campaign_creation(smartlist_first['id'])
        campaign_data['frequency_id'] = Frequency.DAILY
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == UnprocessableEntity.http_status_code()

    def test_create_email_campaign_with_invalid_start_and_end_datetime(self, access_token_first,
                                                                       smartlist_first):
        """
        Here we try to create an email-campaign with frequency DAILY. Here we provide start_datetime
        to be ahead of end_datetime. It should result in UnprocessableEntity error.
        """
        campaign_data = create_data_for_campaign_creation(smartlist_first['id'])
        campaign_data['frequency_id'] = Frequency.DAILY
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow())
        campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() - timedelta(minutes=2))
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == UnprocessableEntity.http_status_code()

    def test_create_email_campaign_with_invalid_email_client_id(self, access_token_first,
                                                                smartlist_first):
        """
        Here we try to create an email-campaign with invalid email-client-id. It should
        result in invalid usage error.
        """
        campaign_data = create_data_for_campaign_creation(smartlist_first['id'])
        campaign_data['email_client_id'] = CampaignsTestsHelpers.get_non_existing_id(EmailClient)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == InvalidUsage.http_status_code()
        json_response = response.json()
        assert 'email_client_id' in json_response['error']['message']

    def test_create_email_campaign_with_smartlist_id_of_other_domain(self, smartlist_other, access_token_first):
        """
        Here we try to create an email-campaign with smartlist_ids belonging to some other domain.
        It should result in ForbiddenError.
        """
        campaign_data = create_data_for_campaign_creation(smartlist_other['id'])
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == ForbiddenError.http_status_code()

    def test_create_campaign_and_send_now(self, access_token_first, headers, smartlist_first):
        """
        Here we assume user has clicked the button "Send Now" from UI, it should send campaign immediately.
        """
        expected_sends = 2
        subject = '%s-send_campaign_now' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(smartlist_first['id'], subject=subject)
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

    @pytest.mark.qa
    def test_create_email_campaign_with_optional_parameters(self, access_token_first, smartlist_first):
        """
        The test is to examine that the email-campaign is created with optional parameter or not.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_with_optional_parameters' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(smartlist_first['id'], subject=subject)
        for param in EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS:
            campaign_data.update(param)
            response = create_email_campaign_via_api(access_token_first, campaign_data)
            assert response.status_code == requests.codes.CREATED
            resp_object = response.json()
            assert 'campaign' in resp_object
            assert resp_object['campaign']['id']

    @pytest.mark.qa
    def test_create_email_campaign_except_single_parameter(self, access_token_first, smartlist_first):
        """
        Here we provide valid data to create an email-campaign with all parameter except single parameter.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_except_single_parameter' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation_with_all_parameters(smartlist_first['id'], subject=subject)
        for param in CAMPAIGN_OPTIONAL_FIELDS:
            campaign_test_data = campaign_data.copy()
            del campaign_test_data[param]
            response = create_email_campaign_via_api(access_token_first, campaign_test_data)
            assert response.status_code == requests.codes.CREATED
            resp_object = response.json()
            assert 'campaign' in resp_object
            assert resp_object['campaign']['id']


# Test for healthcheck
def test_health_check():
    response = requests.get(EmailCampaignApiUrl.HOST_NAME % HEALTH_CHECK)
    assert response.status_code == requests.codes.OK

    # Testing Health Check URL with trailing slash
    response = requests.get(EmailCampaignApiUrl.HOST_NAME % HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.OK
