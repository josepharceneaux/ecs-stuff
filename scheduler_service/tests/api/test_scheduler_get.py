"""
Test cases for getting already scheduled job with or without id. Also it should not be retrieved without
using bearer token
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
class TestSchedulerGet:

    def test_single_get_job(self, auth_header, job_config_periodic):
        """
        Get job using id and then delete it. Again try to get that job using id should give 404 status code
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
        # Creating a job
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                 headers=auth_header)
        assert response.status_code == 201
        data = json.loads(response.text)

        # Now get the job
        response_get = requests.get(APP_URL + '/tasks/id/' + data['id'],
                                    headers=auth_header)
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['task']['id'] == data['id']

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=auth_header)
        assert response.status_code == 404

    def test_multiple_get_jobs(self, auth_header, job_config_periodic):
        """
        Create multiple jobs and save the ids in a list. Then get all tasks of the current user.
        Then check if the jobs created are in the tasks of user. If yes, then show status code 200
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

        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                    headers=auth_header)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        for job in jobs_id:
            assert job in get_jobs_id
        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_scheduled_get_job_without_token(self, auth_header, job_config_periodic):
        """
        Get job without using bearer token it should return 401 status code
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
        data = json.loads(response.text)
        assert data['id'] is not None

        headers = auth_header.copy()

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        # Get the job with invalid token
        response_get = requests.get(APP_URL + '/tasks/id/' + data['id'],
                                    headers=headers)

        assert response_get.status_code == 401
        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=auth_header)
        assert response.status_code == 404