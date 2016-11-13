"""
Here we have test for scheduling an email-campaign.
"""
# Packages
import requests
from requests import codes
from datetime import datetime, timedelta

# Application Specific
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.common.tests.fake_testing_data_generator import fake
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from ...tests.modules.handy_functions import (create_data_for_campaign_creation, create_email_campaign_via_api)

__author__ = 'basit'


class TestCampaignSchedule(object):
    """
    This is the test for scheduling a campaign and verify it is sent to candidate as per send time.
    """
    EXPECTED_SENDS = 1
    BLASTS_URL = EmailCampaignApiUrl.BLASTS
    START_DATETIME_OFFSET = 15

    def test_one_time_schedule_campaign_and_validate_task_run(self, access_token_first, headers, talent_pipeline):
        """
        Here we schedule an email campaign one time with all valid parameters. Then we check
        that task is run fine and assert the blast, sends and activity have been created
        in database.
        """
        subject = '%s-test_schedule_one_time' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, subject)
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow()
                                                                   + timedelta(seconds=self.START_DATETIME_OFFSET))
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
        CampaignsTestsHelpers.assert_blast_sends(
            email_campaign, self.EXPECTED_SENDS,
            blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'], campaign_blast[0]['id']),
            access_token=access_token_first)

    def test_periodic_schedule_campaign_and_validate_run(self, headers, access_token_first, talent_pipeline):
        """
        This is test to schedule an email campaign with all valid parameters. This should get OK
        response. We also assert that scheduler is sending email-campaigns on expected time.
        """
        subject = '%s-test_schedule_periodic' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, subject)
        campaign_data['frequency_id'] = Frequency.CUSTOM
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow()
                                                                   + timedelta(seconds=self.START_DATETIME_OFFSET))
        campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(days=10))
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

        # assert that scheduler has sent the campaign for the first time
        campaign_blast = CampaignsTestsHelpers.get_blasts_with_polling(email_campaign, access_token_first,
                                                                       self.BLASTS_URL % email_campaign['id'],
                                                                       count=1)
        CampaignsTestsHelpers.assert_blast_sends(email_campaign, self.EXPECTED_SENDS,
                                                 blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'],
                                                                                        campaign_blast[0]['id']),
                                                 access_token=access_token_first)
        # assert that scheduler has sent the campaign for the second time
        campaign_blast = CampaignsTestsHelpers.get_blasts_with_polling(email_campaign, access_token_first,
                                                                       self.BLASTS_URL % email_campaign['id'],
                                                                       count=2)
        CampaignsTestsHelpers.assert_blast_sends(email_campaign, self.EXPECTED_SENDS,
                                                 blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'],
                                                                                        campaign_blast[1]['id']),
                                                 access_token=access_token_first)

    def test_schedule_campaign_daily_and_validate_run(self, headers, access_token_first, talent_pipeline):
        """
        This is test to schedule an email campaign on daily basis. This should get OK
        response. We also assert that scheduler is sending email-campaigns on expected time.
        """
        subject = '%s-test_schedule_daily' % fake.uuid4()
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, subject)
        campaign_data['frequency_id'] = Frequency.DAILY
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow()
                                                                   + timedelta(seconds=self.START_DATETIME_OFFSET))
        campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(days=10))
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

        # assert that scheduler has sent the campaign for the first time
        campaign_blast = CampaignsTestsHelpers.get_blasts_with_polling(email_campaign, access_token_first,
                                                                       self.BLASTS_URL % email_campaign['id'],
                                                                       count=1)
        CampaignsTestsHelpers.assert_blast_sends(
            email_campaign, self.EXPECTED_SENDS,
            blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'], campaign_blast[0]['id']),
            access_token=access_token_first)

    def test_schedule_campaign_with_no_start_datetime(self, access_token_first, talent_pipeline):
        """
        This is test to schedule an email campaign periodically with no start_datetime. It should result in
        unprocessable entity.
        """
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, fake.uuid4())
        campaign_data['frequency_id'] = Frequency.DAILY
        campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(seconds=10))
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == codes.unprocessable_entity

    def test_schedule_campaign_with_no_end_datetime(self, access_token_first, talent_pipeline):
        """
        This is test to schedule an email campaign periodically with no end_datetime. It should result in
        unprocessable entity.
        """
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, fake.uuid4())
        campaign_data['frequency_id'] = Frequency.DAILY
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(seconds=10))
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == codes.unprocessable_entity

    def test_with_start_datetime_greater_than_end_datetime(self, access_token_first, talent_pipeline):
        """
        This is test to schedule an email campaign periodically with start_datetime to be greater than end_datetime.
        It should result in unprocessable entity.
        """
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, fake.uuid4())
        campaign_data['frequency_id'] = Frequency.DAILY
        campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(days=10))
        campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(seconds=10))
        response = create_email_campaign_via_api(access_token_first, campaign_data)
        assert response.status_code == codes.unprocessable_entity
