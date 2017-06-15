"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    - GET /v1/email-campaigns
"""
# Packages
import time
from random import randint

# Third Party
import requests

# Application Specific
from email_campaign_service.tests.conftest import fake
from email_campaign_service.common.models.user import Role
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.utils.api_utils import SORT_TYPES
from email_campaign_service.common.utils.test_utils import (INVALID_PAGINATION_PARAMS,
                                                            PAGINATION_EXCEPT_SINGLE_FIELD)
from email_campaign_service.common.custom_errors.campaign import (EMAIL_CAMPAIGN_FORBIDDEN,
                                                                  NOT_NON_ZERO_NUMBER,
                                                                  INVALID_VALUE_OF_QUERY_PARAM,
                                                                  INVALID_VALUE_OF_PAGINATION_PARAM)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import (assert_valid_campaign_get,
                                                                  get_campaign_or_campaigns,
                                                                  assert_talent_pipeline_response,
                                                                  create_email_campaign_in_db)


class TestGetCampaigns(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.CAMPAIGNS
    HTTP_METHOD = 'get'

    def test_get_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_get_all_campaigns_in_user_domain(self, email_campaign_user1_domain1_in_db,
                                              email_campaign_user2_domain1_in_db, access_token_first, talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain.
        Here two campaigns have been created by different users of same domain. Total count
        should be 2. Here we also create another campaign in some other domain but it shouldn't
        be there in GET response.
        """
        # Test GET api of email campaign
        email_campaigns = get_campaign_or_campaigns(access_token_first)
        assert len(email_campaigns) == 2
        reference_campaigns = [email_campaign_user1_domain1_in_db, email_campaign_user2_domain1_in_db]
        assert_valid_campaign_get(email_campaigns[0], reference_campaigns)
        assert_valid_campaign_get(email_campaigns[1], reference_campaigns)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_campaigns_with_paginated_response(self, email_campaign_user1_domain1_in_db,
                                                   email_campaign_user2_domain1_in_db,
                                                   access_token_first, talent_pipeline):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain using
        paginated response. Here two campaigns have been created by different users of same domain.
        """
        # Test GET api of email campaign using per_page=1 and default page=1.
        # It should return first campaign in response.
        email_campaigns = get_campaign_or_campaigns(access_token_first, query_params='?per_page=1')
        assert len(email_campaigns) == 1
        reference_campaigns = [email_campaign_user1_domain1_in_db, email_campaign_user2_domain1_in_db]
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

    def test_get_campaigns_with_invalid_user_id(self, access_token_first):
        """
        Test GET API of email_campaigns for getting all campaigns for particular user_id where user_id
        is not in valid format. i.e. we are passing string rather that integer value. It should result in Bad Request
        Error.
        """
        for user_id in CampaignsTestsHelpers.INVALID_IDS:
            url = self.URL + '?user_id={}'.format(user_id)
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, url, access_token_first,
                                                             expected_error_code=NOT_NON_ZERO_NUMBER[1])

    def test_get_campaigns_with_user_id_of_same_domain(self, email_campaign_user1_domain1_in_db, access_token_first,
                                                       email_campaign_user2_domain1_in_db, user_same_domain):
        """
        Test GET API of email_campaigns for getting all campaigns for a particular user_id of same domain.
        It should return one campaign.
        """
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    query_params='?user_id={}'.format(user_same_domain.id))
        assert len(email_campaigns) == 1  # As we have only 1 campaign created by other user of same domain
        assert email_campaigns[0]['id'] == email_campaign_user2_domain1_in_db.id
        assert email_campaigns[0]['user_id'] == user_same_domain.id

    def test_get_campaigns_with_user_id_of_other_domain(self, access_token_first, user_from_diff_domain):
        """
        Test GET API of email_campaigns for getting all campaigns for a particular user_id of some other domain.
        It should result in Forbidden Error.
        """
        url = self.URL + '?user_id={}'.format(user_from_diff_domain.id)
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, url, access_token_first,
                                                          expected_error_code=EMAIL_CAMPAIGN_FORBIDDEN[1])

    def test_get_campaigns_with_user_id_of_other_domain_with_talent_admin_role(self, user_first, access_token_first,
                                                                               user_from_diff_domain,
                                                                               email_campaign_user1_domain2_in_db):
        """
        Test GET API of email_campaigns for getting all campaigns for a particular user_id of some other domain.
        It should return the campaign created by that user as requested user has appropriate role.
        """
        user_first.update(role_id=Role.get_by_name(Role.TALENT_ADMIN).id)
        email_campaigns = get_campaign_or_campaigns(access_token_first,
                                                    query_params='?user_id={}'.format(user_from_diff_domain.id))
        assert len(email_campaigns) == 1  # As we have only 1 campaign created by the user of other domain
        assert email_campaigns[0]['id'] == email_campaign_user1_domain2_in_db.id
        assert email_campaigns[0]['user_id'] == user_from_diff_domain.id

    def test_get_campaigns_with_invalid_sort_type(self, access_token_first):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain with invalid value
        of parameter sort_type. Valid values are "ASC" or "DESC". This should result in invalid usage error.
        """
        url = self.URL + '?sort_type=%s' % fake.word()
        response = CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, url, access_token_first,
                                                                    expected_error_code=INVALID_VALUE_OF_QUERY_PARAM[1])
        for sort_type in SORT_TYPES:
            assert sort_type in response.json()['error']['message']

    def test_get_campaigns_with_invalid_value_of_sort_by(self, access_token_first):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain with invalid value
        of parameter sort_by. Valid values are "name" and "added_datetime".
        This should result in invalid usage error.
        """
        url = self.URL + '?sort_by=%s' % fake.sentence()
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, url, access_token_first,
                                                         expected_error_code=INVALID_VALUE_OF_QUERY_PARAM[1])

    def test_get_campaigns_with_invalid_value_of_is_hidden(self, access_token_first):
        """
        Test GET API of email_campaigns for getting all campaigns in logged-in user's domain with invalid value
        of parameter is_hidden. Valid values are 0 or 1.
        This should result in invalid usage error.
        """
        url = self.URL + '?is_hidden=%d' % randint(2, 10)
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, url, access_token_first,
                                                         expected_error_code=INVALID_VALUE_OF_QUERY_PARAM[1])

    # TODO: GET-1608: Add test for large value of param "page"
    def test_get_campaigns_with_invalid_pagination_params(self, access_token_first):
        """
        Test GET API of getting email_campaign using paginated response. Here we use invalid value of "per_page" to
        be 1) greater than maximum allowed value 2) Negative. It should result in invalid usage error.
        """
        for param in INVALID_PAGINATION_PARAMS:
            url = self.URL + param
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, url, access_token_first,
                                                             expected_error_code=INVALID_VALUE_OF_PAGINATION_PARAM[1])

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

    def test_get_campaigns_except_single_field(self, headers):
        """
        This test certify that data of campaign is retrieved with url having all fields except single field.
        Should return 200 ok status.
        """
        for param in PAGINATION_EXCEPT_SINGLE_FIELD:
            # sort_by name is for email campaign pagination
            response = requests.get(url=self.URL + param % 'name', headers=headers)
            assert response.status_code == requests.codes.OK
