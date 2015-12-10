"""
Test cases for exceptions when post data in request is incorrect or missing
"""

# Standard imports
import datetime

# Third party imports
import json
import pytest
import requests

# Application imports
from scheduler_service.custom_error_codes import CODE_FIELD_REQUIRED, CODE_TRIGGER_TYPE
from scheduler_service.tests.conftest import APP_URL

__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config')
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
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        # delete frequency from post data and try to create job, should get 500 response
        invalid_job_config = job_config.copy()
        del invalid_job_config['frequency']

        # create job with invalid string
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(invalid_job_config),
                                 headers=auth_header)
        assert response.status_code == 500 and response.json()['error']['code'] == CODE_FIELD_REQUIRED

    def test_incorrect_post_data_exception(self, auth_header, job_config):
        """
            Create a job by posting wrong data and check if exception occur with status code 400
            Args:
                auth_data: Fixture that contains token.
                job_config (dict): Fixture that contains job config to be used as
                POST data while hitting the endpoint.
            :return:
            """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        # create job with invalid string
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
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        # create job with invalid string
        response = requests.post(APP_URL + '/tasks/', data='invalid data',
                                 headers=auth_header)
        assert response.status_code == 400

        # post with invalid task type
        job_config['task_type'] = 'Some invalid type'
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        # Invalid trigger type exception
        assert response.status_code == 500 and response.json()['error']['code'] == CODE_TRIGGER_TYPE
