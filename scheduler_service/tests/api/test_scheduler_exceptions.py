"""
Test cases for exceptions when post data in request is incorrect or missing
"""

# Third party imports
import json

import datetime
import pytest
import requests

# Application imports
from scheduler_service.custom_exceptions import SchedulerServiceApiException
from scheduler_service.tests.conftest import APP_URL

__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config', 'job_config_one_time')
class TestSchedulerExceptions:

    def test_incomplete_post_data_exception(self, auth_header, job_config):
        """
            Create a job by missing data and check if exception occur with status code 500 and error code 6055

            Args:
                auth_data: Fixture that contains token.
                job_config (dict): Fixture that contains job config to be used as
                POST data while hitting the endpoint.
            :return:
            """
        # Delete frequency from post data and try to create job, should get 500 response
        invalid_job_config = job_config.copy()
        del invalid_job_config['frequency']

        # Create job with invalid string
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(invalid_job_config),
                                 headers=auth_header)
        assert response.status_code == 500 and response.json()['error']['code'] == SchedulerServiceApiException.CODE_FIELD_REQUIRED

    def test_incorrect_post_data_exception(self, auth_header):
        """
            Create a job by posting wrong data and check if exception occurs with status code 400
            Args:
                auth_data: Fixture that contains token.
                job_config (dict): Fixture that contains job config to be used as
                POST data while hitting the endpoint.
            :return:
            """
        # Create job with invalid string
        response = requests.post(APP_URL + '/tasks/', data='invalid data',
                                 headers=auth_header)
        assert response.status_code == 400

    def test_invalid_task_type_exception(self, auth_header, job_config):
        """
            Create a job using incorrect task_type, it should throw 500 exception with error code

            Args:
                auth_data: Fixture that contains token.
                job_config (dict): Fixture that contains job config to be used as
                POST data while hitting the endpoint.
            :return:
            """
        # Create job with invalid string
        response = requests.post(APP_URL + '/tasks/', data='invalid data',
                                 headers=auth_header)
        assert response.status_code == 400

        # Post with invalid task type
        job_config['task_type'] = 'Some invalid type'
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        # Invalid trigger type exception
        assert response.status_code == 500 and response.json()['error']['code'] == SchedulerServiceApiException.CODE_TRIGGER_TYPE

    def test_invalid_frequency_job(self, auth_header, job_config):
        """
        Create a job by hitting the endpoint and make sure response
        is correct.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        temp_job_config = job_config.copy()
        temp_job_config['frequency'] = 'abc'
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(temp_job_config),
                                 headers=auth_header)

        assert response.status_code == 400

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201

        data = response.json()
        assert data['id'] is not None
        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_already_passed_time_exception(self, auth_header, job_config_one_time):
        """
        Create a job using expired run_datetime and it should raise exception

        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        job_config = job_config_one_time.copy()
        run_datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        job_config['run_datetime'] = run_datetime.strftime('%Y-%m-%d %H:%M:%S')
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        # Time expired exception
        assert response.status_code == 500 and \
               response.json()['error']['code'] == SchedulerServiceApiException.CODE_TIME_ALREADY_PASSED

    def test_invalid_job_time_interval_exception(self, auth_header, job_config):
        """
        Create a job using expired end_datetime and it should raise exception

        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        job_config = job_config.copy()
        end_datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        job_config['end_datetime'] = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        # Time expired exception
        assert response.status_code == 500 and \
               response.json()['error']['code'] == SchedulerServiceApiException.CODE_INVALID_TIME_INTERVAL_PASSED

    def test_already_passed_time_interval_exception(self, auth_header, job_config):
        """
        Create a job using expired end_datetime and it should raise exception

        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        job_config = job_config.copy()
        end_datetime = datetime.datetime.utcnow() - datetime.timedelta(seconds=8)
        job_config['end_datetime'] = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        # Time expired exception
        assert response.status_code == 500 and \
               response.json()['error']['code'] == SchedulerServiceApiException.CODE_TIME_ALREADY_PASSED