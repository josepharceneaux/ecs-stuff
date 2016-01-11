"""
Test cases for creating schedule job with and without token.
"""

# Third party imports
import json
import pytest
import requests

# Application imports
from scheduler_service.common.routes import SchedulerApiUrl

__author__ = 'saad'


class TestSchedulerCreate:

    def test_single_scheduled_job_without_user(self, auth_header_no_user, job_config):
        """
        Create a job by hitting the endpoint with secret_key (global tasks) and make sure we get job_id in
        response.
        This test case is to create a named task which is in case of server to server communication (global tasks)
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 400

        # Assign task_name in job post data (general task)
        job_config['task_name'] = 'Custom General Named Task'
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Try to create already named job and it should throw 400 invalid usage error
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 400

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.SINGLE_TASK % data['id'],
                                          headers=auth_header_no_user)
        assert response_remove.status_code == 200

    def test_request_send_url(self, auth_header, job_config):
        """
        Test dummy endpoint SendRequest to test send_request method is working fine.
        :param auth_header:
        :param job_config:
        :return:
        """
        response = requests.post(SchedulerApiUrl.TEST_TASK, data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 200

    def test_single_scheduled_job(self, auth_header, job_config):
        """
        Create a job by hitting the endpoint and make sure response
        is correct.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.SINGLE_TASK % data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_multiple_scheduled_jobs(self, auth_header, job_config):
        """
        Create multiple jobs. Then schedule jobs and finally remove all jobs.
         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs = []

        # schedule some jobs and remove all of them
        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs = requests.delete(SchedulerApiUrl.TASKS,
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=auth_header)

        assert response_remove_jobs.status_code == 200

    def test_single_scheduled_job_without_token(self, job_config):
        """
        Create a job without a token, it shouldn't be created and we should get a
        401 when endpoint hit
        Args:
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        invalid_header = {'Authorization': 'Bearer invalid_token',
                          'Content-Type': 'application/json'}

        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=invalid_header)
        assert response.status_code == 401


