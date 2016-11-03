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
import pytest
import time
from redo import retry
from random import randint
from datetime import datetime, timedelta

# Third Party
import requests

# Application Specific
from email_campaign_service.common.utils.test_utils import (PAGINATION_INVALID_FIELDS,
                                                            PAGINATION_EXCEPT_SINGLE_FIELD)
from email_campaign_service.tests.modules.__init__ import CAMPAIGN_OPTIONAL_FIELDS
from email_campaign_service.common.models.candidate import Candidate
from email_campaign_service.common.models.db import db
from email_campaign_service.modules.utils import do_mergetag_replacements
from email_campaign_service.tests.conftest import fake
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.campaign_services.tests_helpers import send_request
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.common.models.misc import (UrlConversion, Frequency)
from email_campaign_service.common.utils.api_utils import MAX_PAGE_SIZE, SORT_TYPES
from email_campaign_service.common.error_handling import (InvalidUsage, UnprocessableEntity,
                                                          ForbiddenError)
from email_campaign_service.common.routes import (EmailCampaignApiUrl, HEALTH_CHECK)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignBlast,
                                                                 EmailClient, EmailCampaignSmartlist)
from email_campaign_service.tests.modules.handy_functions import (assert_valid_campaign_get,
                                                                  get_campaign_or_campaigns,
                                                                  assert_talent_pipeline_response,
                                                                  assert_campaign_send,
                                                                  create_email_campaign,
                                                                  create_email_campaign_via_api,
                                                                  EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS,
                                                                  create_data_for_campaign_creation,
                                                                  create_email_campaign_smartlists,
                                                                  send_campaign_with_client_id,
                                                                  create_data_for_campaign_creation_with_all_parameters)


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

    def test_get_all_campaigns_in_user_domain(self, email_campaign_of_user_first, email_campaign_of_user_second,
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
        reference_campaigns = [email_campaign_of_user_first, email_campaign_of_user_second]
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_campaign_with_email_client(self, email_campaign_with_outgoing_email_client, access_token_first):
        """
        Here we try to GET a campaign which is created by email-client. It should not get any error.
        """
        fields = ['email_client_credentials_id']
        email_campaign = get_campaign_or_campaigns(access_token_first,
                                                   campaign_id=email_campaign_with_outgoing_email_client.id,
                                                   fields=fields)
        assert_valid_campaign_get(email_campaign, [email_campaign_with_outgoing_email_client], fields=fields)

    def test_get_campaigns_with_paginated_response(self, email_campaign_of_user_first,
                                                   email_campaign_of_user_second, email_campaign_in_other_domain,
                                                   access_token_first, talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain using
        paginated response. Here two campaigns have been created by different users of same domain.
        """
        # Test GET api of email campaign using per_page=1 and default page=1.
        # It should return first campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?per_page=1')
        assert len(email_campaigns) == 1
        reference_campaigns = [email_campaign_of_user_first, email_campaign_of_user_second]
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

        # Test GET api of email campaign using per_page=1 for page=2. It should
        # return second campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?per_page=1&page=2')
        assert len(email_campaigns) == 1
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)

        # Test GET api of email campaign with 2 results per_page
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?per_page=2')
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)
        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

        # Test GET api of email campaign with default per_page=10 and page =1.
        # It should get both campaigns in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?&page=1')
        assert len(email_campaigns) == 2
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)

        # Test GET api of email campaign with page = 2. No campaign should be received in response
        # as we have created only two campaigns so far and default per_page is 10.
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    pagination_query='?page=2')
        assert len(email_campaigns) == 0

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
        url = EmailCampaignApiUrl.CAMPAIGNS + '?per_page=%d' % randint(MAX_PAGE_SIZE+1, 2*MAX_PAGE_SIZE)
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
        create_email_campaign(user_first)
        time.sleep(2)
        create_email_campaign(user_same_domain)
        email_campaigns = get_campaign_or_campaigns(access_token_first, pagination_query='?sort_type=DESC')
        assert email_campaigns[0]['added_datetime'] > email_campaigns[1]['added_datetime']

    @pytest.mark.qa
    def test_get_all_campaigns_in_asc(self, user_first, user_same_domain, access_token_first):
        """
        This test is to make sure the GET endpoint get_all_email_campaigns
        is retrieving all campaigns in ascending order according of added_datetime'
        """
        # Test GET api of email campaign
        create_email_campaign(user_first)
        time.sleep(2)
        create_email_campaign(user_same_domain)
        email_campaigns = get_campaign_or_campaigns(access_token_first, pagination_query='?sort_type=ASC')
        assert email_campaigns[0]['added_datetime'] < email_campaigns[1]['added_datetime']

    @pytest.mark.qa
    def test_get_campaign_except_single_field(self, headers):
        """
        This test certify that data of campaign is retrieved with url having all fields except single field.
        Should return 200 ok status.
        """
        for param in PAGINATION_EXCEPT_SINGLE_FIELD:
            # sort_by name is for email campaign pagination
            param % 'name'
            response = requests.get(url=EmailCampaignApiUrl.CAMPAIGNS + param, headers=headers)
            assert response.status_code == requests.codes.OK


class TestCreateCampaign(object):
    """
    Here are the tests for creating a campaign from endpoint /v1/email-campaigns
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.CAMPAIGNS

    def test_create_campaign_with_invalid_token(self):
        """
        Here we try to create email campaign with invalid access token
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_create_email_campaign_without_client_id(self, access_token_first, talent_pipeline):
        """
        Here we provide valid data to create an email-campaign without email_client_id.
        It should get OK response.
        """
        subject =  '%s-test_create_email_campaign' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object
        assert resp_object['campaign']['id']

    def test_create_email_campaign_with_client_id(self, access_token_first, talent_pipeline):
        """
        Here we provide valid data to create an email-campaign with email_client_id.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_with_client_id' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
        campaign_data['email_client_id'] = EmailClient.get_id_by_name('Browser')
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == requests.codes.CREATED
        resp_object = response.json()
        assert 'campaign' in resp_object

    def test_create_email_campaign_with_outgoing_email_client(self, access_token_first, talent_pipeline,
                                                              outgoing_email_client, headers):
        """
        Here we provide valid data to create an email-campaign with email_client_credentials_id.
        It should get OK response.
        """
        subject = '%s-test_email_campaign_with_outgoing_email_client' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
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

    def test_create_email_campaign_with_incoming_email_client(self, access_token_first, talent_pipeline,
                                                              email_clients, headers):
        """
        Here we provide email-client of type "incoming". email-campaign should not be created.
        """
        subject = '%s-test_create_email_campaign_with_incoming_email_client' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
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

    def test_create_email_campaign_with_whitespace_campaign_name(self, access_token_first, talent_pipeline):
        """
        This tries to create an email campaign with whitespace as campaign name.
        It should result in invalid usage error as campaign_name is required field.
        """
        name = '       '
        subject = '%s-test_create_email_campaign_whitespace_campaign_name' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, name, assert_candidates=False)
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

    def test_create_email_campaign_with_invalid_format_of_smartlist_ids(self, access_token_first,
                                                                        talent_pipeline):
        """
        Here we try to create an email-campaign with list_ids not in list format. It should
        result in invalid usage error.
        """
        subject = '%s-test_with_non_list_smartlist_ids' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
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
        campaign_data = create_data_for_campaign_creation('', '', fake.sentence(), create_smartlist=False)
        CampaignsTestsHelpers.campaign_create_or_update_with_invalid_smartlist(self.HTTP_METHOD, self.URL,
                                                                               access_token_first,
                                                                               campaign_data, key='list_ids')

    def test_create_email_campaign_with_deleted_smartlist_id(self, access_token_first, talent_pipeline):
        """
        This is a test to create email-campaign with deleted smartlist id. It should result in
        Resource not found error.
        """
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, fake.sentence())
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL, access_token_first,
                                                                  campaign_data['list_ids'][0], campaign_data)

    def test_create_email_campaign_with_no_start_datetime(self, access_token_first, talent_pipeline):
        """
        Here we try to create an email-campaign with frequency DAILY for which start_datetime will be
        a required field. But we are not giving start_datetime. It should result in
        UnprocessableEntity error.
        """
        subject = '%s-test_with_no_start_datetime' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
        campaign_data['frequency_id'] = Frequency.DAILY
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == UnprocessableEntity.http_status_code()

    def test_create_email_campaign_with_invalid_start_and_end_datetime(self, access_token_first,
                                                                       talent_pipeline):
        """
        Here we try to create an email-campaign with frequency DAILY. Here we provide start_datetime
        to be ahead of end_datetime. It should result in UnprocessableEntity error.
        """
        subject = '%s-test_with_invalid_start_and_end_datetime' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
        campaign_data['frequency_id'] = Frequency.DAILY
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow())
        campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(
            datetime.utcnow() - timedelta(minutes=2))
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == UnprocessableEntity.http_status_code()

    def test_create_email_campaign_with_invalid_email_client_id(self, access_token_first,
                                                                talent_pipeline):
        """
        Here we try to create an email-campaign with invalid email-client-id. It should
        result in invalid usage error.
        """
        subject = '%s-test_with_invalid_email_client_id' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject, assert_candidates=False)
        campaign_data['email_client_id'] = CampaignsTestsHelpers.get_non_existing_id(EmailClient)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == InvalidUsage.http_status_code()
        json_response = response.json()
        assert 'email_client_id' in json_response['error']['message']

    def test_create_email_campaign_with_smartlist_id_of_other_domain(self,
                                                                     talent_pipeline_other,
                                                                     access_token_first,
                                                                     access_token_other):
        """
        Here we try to create an email-campaign with smartlist_ids belonging to some other domain.
        It should result in ForbiddenError.
        """
        subject = '%s-test_email_campaign_with_list_id_of_other_domain' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_other, talent_pipeline_other,
                                                          subject, assert_candidates=False)
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == ForbiddenError.http_status_code()

    @pytest.mark.qa
    def test_create_email_campaign_with_optional_parameters(self, access_token_first, talent_pipeline):
        """
        The test is to examine that the email-campaign is created with optional parameter or not.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_with_optional_parameters' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline,
                                                          subject)
        for param in EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS:
            campaign_data.update(param)
            response = create_email_campaign_via_api(access_token_first, campaign_data)
            assert response.status_code == requests.codes.CREATED
            resp_object = response.json()
            assert 'campaign' in resp_object
            assert resp_object['campaign']['id']

    @pytest.mark.qa
    def test_create_email_campaign_except_single_parameter(self, access_token_first, talent_pipeline):
        """
        Here we provide valid data to create an email-campaign with all parameter except single parameter.
        It should get OK response.
        """
        subject = '%s-test_create_email_campaign_except_single_parameter' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation_with_all_parameters(access_token_first, talent_pipeline,
                                                                              subject)
        for param in CAMPAIGN_OPTIONAL_FIELDS:
            campaign_test_data = campaign_data.copy()
            del campaign_test_data[param]
            response = create_email_campaign_via_api(access_token_first, campaign_test_data)
            assert response.status_code == requests.codes.CREATED
            resp_object = response.json()
            assert 'campaign' in resp_object
            assert resp_object['campaign']['id']

    @pytest.mark.qa
    def test_update_email_campaign_with_allowed_parameter(self, access_token_first, email_campaign_of_user_first):
        """
         The test is to make sure that email campaign update functionality with allowed parameters/fields
         is working properly or not. Should return 200 status ok.
        """
        campaign_id = email_campaign_of_user_first.id
        for param in [True, 1, False, 0]:
            data = {'is_hidden': param}
            CampaignsTestsHelpers.request_for_ok_response('patch', EmailCampaignApiUrl.CAMPAIGN % campaign_id,
                                                          access_token_first, data)
            email_campaign = get_campaign_or_campaigns(access_token_first, campaign_id=campaign_id)
            assert email_campaign['is_hidden'] == param

    @pytest.mark.qa
    def test_update_email_campaign_with_invalid_data(self, access_token_first, email_campaign_of_user_first):
        """
         This test to make sure that update email campaign with invalid data is not
         possible, only valid data is acceptable. Should return 400 bad request on invalid data.
        """
        campaign_id = email_campaign_of_user_first.id
        update_with_invalid_data = [fake.word(), fake.random_int(2,)]
        for param in update_with_invalid_data:
            data = {'is_hidden': param}
            response = send_request('patch', EmailCampaignApiUrl.CAMPAIGN % campaign_id, access_token_first, data)
            CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=requests.codes.BAD_REQUEST)


class TestSendCampaign(object):
    """
    Here are the tests for sending a campaign from endpoint /v1/email-campaigns/:id/send
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.SEND

    def test_campaign_send_with_invalid_token(self, email_campaign_of_user_first):
        """
        Here we try to send email campaign with invalid access token
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % email_campaign_of_user_first.id)

    def test_campaign_send_with_no_smartlist_associated(self, access_token_first, email_campaign_of_user_first):
        """
        User auth token is valid but given email campaign has no associated smartlist with it. So
        up til this point we only have created a user and email campaign of that user
        (using fixtures passed in as params).
        It should get Invalid usage error.
        Custom error should be NoSmartlistAssociatedWithCampaign.
        """
        CampaignsTestsHelpers.campaign_send_with_no_smartlist(self.URL % email_campaign_of_user_first.id,
                                                              access_token_first)

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
        This is a test to update a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign, self.HTTP_METHOD, self.URL,
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
                                                                         campaign_with_two_candidates):
        """
        Tests sending a campaign with one smartlist. That smartlist has, in turn,
        two candidates associated with it. Those candidates have unique email addresses.
        Campaign emails should be sent to 2 candidates so number of sends should be 2.
        """
        no_of_sends = 2
        campaign = campaign_with_two_candidates
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first, no_of_sends)

    def test_campaign_send_to_two_candidates_with_same_email_address_in_same_domain(self, headers, user_first,
                                                                                    campaign_with_two_candidates):
        """
        User auth token is valid, campaign has one smartlist associated. Smartlist has two
        candidates associated (with same email addresses). Email Campaign should be sent to only
        one candidate.
        """
        same_email = fake.email()
        for candidate in user_first.candidates:
            candidate.emails[0].update(address=same_email)
        response = requests.post(self.URL % campaign_with_two_candidates.id, headers=headers)
        assert_campaign_send(response, campaign_with_two_candidates, user_first, 1)
        if not campaign_with_two_candidates.email_client_id:
            json_resp = response.json()
            assert str(campaign_with_two_candidates.id) in json_resp['message']

    def test_campaign_send_to_two_candidates_with_same_email_address_in_diff_domain(
            self, headers, user_first, campaign_with_candidates_having_same_email_in_diff_domain):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates associated. One more candidate exists in some other domain with same email
        address. Email Campaign should be sent to 2 candidates only.
        """
        campaign = campaign_with_candidates_having_same_email_in_diff_domain
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first, 2)

    def test_campaign_send_with_outgoing_email_client(self, email_campaign_with_outgoing_email_client, headers,
                                                      user_first):
        """
        This sends email-campaign with SMTP server added by user. It should not get any error.
        """
        campaign = email_campaign_with_outgoing_email_client
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first, via_amazon_ses=False)

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

        [modified_subject] = do_mergetag_replacements([campaign.subject], candidate_object, candidate_address)
        campaign.update(subject=modified_subject)
        msg_ids = assert_campaign_send(response, campaign, user_first, 1, delete_email=False, via_amazon_ses=False)
        # TODO: Emails are being delayed, commenting for now
        # mail_connection = get_mail_connection(app.config[TalentConfigKeys.GT_GMAIL_ID],
        #                                       app.config[TalentConfigKeys.GT_GMAIL_PASSWORD])
        # email_bodies = fetch_emails(mail_connection, msg_ids)
        # assert len(email_bodies) == 1
        # assert candidate['first_name'] in email_bodies[0]
        # assert candidate['last_name'] in email_bodies[0]
        # assert str(candidate['id']) in email_bodies[0]  # This will be in unsubscribe URL.
        # delete_emails(mail_connection, msg_ids, modified_subject)

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
        assert_campaign_send(response, campaign, user_first, 2, email_client=True)

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
        assert_campaign_send(response, email_campaign, user_first, expected_sends, email_client=True)

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
        assert response.status_code == requests.codes.OK
        db.session.commit()
        opens_count_after = email_campaign_blast.opens
        hit_count_after = url_conversion.hit_count
        assert opens_count_after == opens_count_before + 1
        assert hit_count_after == hit_count_before + 1
        UrlConversion.delete(url_conversion)

    def test_campaign_send_with_two_smartlists(self, access_token_first, headers, user_first, talent_pipeline,
                                               email_campaign_of_user_first):
        """
        This function creates two smartlists with 20 candidates each and associates them
        with a campaign. Sends that campaign and tests if emails are sent to all 40 candidates.
        :param access_token_first: Access token of user_first
        :param user_first: Valid user from fist domain
        :param talent_pipeline: valid talent pipeline
        :param email_campaign_of_user_first: email campaign associated with user first
        """
        smartlist_id1, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first, talent_pipeline,
                                                                                 count=20, emails_list=True)
        smartlist_id2, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first, talent_pipeline,
                                                                                 count=20, emails_list=True)
        campaign = email_campaign_of_user_first
        create_email_campaign_smartlists(smartlist_ids=[smartlist_id1, smartlist_id2], email_campaign_id=campaign.id)
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first, 40)

    def test_campaign_send_with_two_smartlists_having_same_candidate(
            self, headers, user_first, campaign_with_same_candidate_in_multiple_smartlists):
        """
        This function creates two smartlists with 1 candidate each, candidate is same in both smartlists and
        associates them with a campaign. Sends that campaign and tests if email is sent to the candidate only once.
        """
        campaign = campaign_with_same_candidate_in_multiple_smartlists
        response = requests.post(self.URL % campaign.id, headers=headers)
        assert_campaign_send(response, campaign, user_first, expected_count=1)


# Test for healthcheck
def test_health_check():
    response = requests.get(EmailCampaignApiUrl.HOST_NAME % HEALTH_CHECK)
    assert response.status_code == requests.codes.OK

    # Testing Health Check URL with trailing slash
    response = requests.get(EmailCampaignApiUrl.HOST_NAME % HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.OK
