"""
Test cases for getting already scheduled job with or without id. Also it should not be retrieved without
using bearer token
"""

# Third party imports
import json
import pytest
import requests

# Application imports
from scheduler_service.tests.conftest import APP_URL


__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config')
class TestSchedulerGet:

    def test_single_get_job(self, auth_header, job_config):
        """
        Get job using id and then delete it. Again try to get that job using id should give 404 status code
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        # Creating a job
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()

        # Now get the job
        response_get = requests.get(APP_URL + '/tasks/id/' + data['id'],
                                    headers=auth_header)
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['task']['id'] == data['id']

        job_data = response_get.json()['task']

        assert job_data['start_datetime'] == job_config['start_datetime']
        assert job_data['end_datetime'] == job_config['end_datetime']
        assert int(job_data['frequency']['seconds']) == job_config['frequency']
        assert job_data['post_data'] == job_config['post_data']
        assert job_data['task_type'] == job_config['task_type']
        assert job_data['url'] == job_config['url']

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=auth_header)
        assert response.status_code == 404

    def test_multiple_get_jobs(self, auth_header, job_config):
        """
        Create multiple jobs and save the ids in a list. Then get all tasks of the current user.
        Then check if the jobs created are in the tasks of user. If yes, then show status code 200
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

        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                    headers=auth_header)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        for job in jobs_id:
            assert job in get_jobs_id
        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_scheduled_get_job_without_token(self, auth_header, job_config):
        """
        Get job without using bearer token it should return 401 status code
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

        # Get the job with invalid token
        response_get = requests.get(APP_URL + '/tasks/id/' + data['id'],
                                    headers=invalid_header)

        assert response_get.status_code == 401
        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=auth_header)
        assert response.status_code == 404
