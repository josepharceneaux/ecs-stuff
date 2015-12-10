"""
Test cases for creating schedule job with and without token.
"""
# Standard imports
import datetime

# Third party imports
import json
import pytest
import requests

# Application imports
from scheduler_service.tests.conftest import APP_URL


__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config_periodic')
class TestSchedulerCreate:

    def test_single_schedule_job(self, auth_header, job_config_periodic):
        """
        Create a job by hitting the endpoint and make sure response
        is correct.
        Args:
            auth_data: Fixture that contains token.
            job_config_periodic (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config_periodic['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config_periodic['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_multiple_schedule_job(self, auth_header, job_config_periodic):
        """
        Create multiple jobs. Then schedule jobs and finally remove all jobs.
         Args:
            auth_data: Fixture that contains token.
            job_config_periodic (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config_periodic['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config_periodic['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
        jobs = []

        # schedule some jobs and remove all of them
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs = requests.delete(APP_URL + '/tasks/',
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=auth_header)

        assert response_remove_jobs.status_code == 200

    def test_single_schedule_job_without_token(self, job_config_periodic):
        """
        Create a job without a token, it shouldn't be created and we should get a
        401 when endpoint hit
        Args:
            job_config_periodic (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config_periodic['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config_periodic['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer invalid_token',
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                 headers=headers)
        # TODO may be not hard code error codes and see if we can use them from requests
        assert response.status_code == 401