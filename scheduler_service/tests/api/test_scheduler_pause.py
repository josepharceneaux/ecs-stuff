"""
Pause jobs which are already scheduled and in running state.
Also try to pause jobs without using token and it should give 401 status code
"""

# Third party imports
import json
import pytest
import requests

# Application imports
from scheduler_service.custom_exceptions import SchedulerServiceApiException
from scheduler_service.tests.conftest import APP_URL

__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config')
class TestSchedulerPause:

    def test_single_job(self, auth_header, job_config):
        """
        Create a job by hitting endpoint. Then stop it using endpoint. We then stop it again and
        it should give error (6053).
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(response.json()['id'])
        job_id = jobs[0]

        # Send job stop request
        response_stop = requests.post(APP_URL + '/tasks/' + job_id + '/pause/',
                                      headers=auth_header)
        assert response_stop.status_code == 200

        # Paused jobs have their 'next_run_datetime' set to 'None'
        response = requests.get(APP_URL + '/tasks/id/' + job_id, headers=auth_header)
        next_run_datetime = response.json()['task']['next_run_datetime']
        assert next_run_datetime is None

        # Try stopping again, it should throw exception
        response_stop_again = requests.post(APP_URL + '/tasks/' + job_id + '/pause/',
                                            headers=auth_header)
        assert response_stop_again.status_code == 500 and \
               response_stop_again.json()['error']['code'] == SchedulerServiceApiException.CODE_ALREADY_PAUSED

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                          headers=auth_header)
        assert response_remove.status_code == 200
        del jobs[:1]
        # Check if rest of the jobs are okay
        for job_id in jobs:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id,
                                        headers=auth_header)
            assert response_get.json()['task']['id'] == job_id and \
                   response_get.json()['task']['next_run_datetime'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_multiple_jobs(self, auth_header, job_config):
        """
        Pause already running scheduled jobs and then see it returns 200 status code and also get jobs
        and check their next_run_datetime is none (Paused job has next_run_datetime equal to None)
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # Send job stop request
        response_stop = requests.post(APP_URL + '/tasks/pause/', data=json.dumps(dict(ids=jobs_id)),
                                      headers=auth_header)
        assert response_stop.status_code == 200

        jobs = []
        # Paused jobs have their next_run_datetime set to 'None'

        # Get jobs
        for job_id in jobs_id:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=auth_header)
            jobs.append(response_get.json()['task'])

        # Now after getting jobs check their next run time
        for res in jobs:
            next_run_datetime = res['next_run_datetime']
            assert next_run_datetime is None

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_single_pause_job_without_token(self, auth_header, job_config):
        """
        Try to pause an already scheduled job using invalid or no token, then check if it shows 401 response
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        invalid_header = auth_header.copy()
        # Set the token to invalid
        invalid_header['Authorization'] = 'Bearer invalid_token'

        # Send job stop request
        response_stop = requests.post(APP_URL + '/tasks/' + data['id'] + '/pause/',
                                      headers=invalid_header)
        assert response_stop.status_code == 401

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=auth_header)
        assert response.status_code == 404

    def test_multiple_pause_jobs_without_token(self, auth_header, job_config):
        """
        Pause multiple jobs which are already scheduled and running without using token and then check
        if the response is 401
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        invalid_header = auth_header.copy()
        invalid_header['Authorization'] = 'Bearer invalid_token'

        # Send job stop request with invalid token
        response_stop = requests.post(APP_URL + '/tasks/pause/', data=json.dumps(dict(ids=jobs_id)),
                                      headers=invalid_header)
        assert response_stop.status_code == 401

        # Paused jobs have their next_run_datetime set to 'None'
        jobs = []

        # Get all jobs
        for job_id in jobs_id:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=auth_header)
            assert response_get.status_code == 200
            jobs.append(response_get.json())

        # Now check if their next run time is None
        for res in jobs:
            next_run_datetime = res['task']['next_run_datetime']
            assert next_run_datetime != 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=auth_header)
        assert response_remove.status_code == 200
