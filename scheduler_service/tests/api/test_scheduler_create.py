"""
Test cases for creating schedule job with and without token.
"""

# Third party imports
import json

import datetime
from time import sleep

import pytest
import requests

# Application imports
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token
from scheduler_service.tests.conftest import APP_URL

__author__ = 'saad'


def _update_token_expiry_(user_id, expiry):
    token = Token.query.filter_by(user_id=user_id).first()
    token.update(expires=expiry)
    return token


@pytest.mark.usefixtures('auth_header', 'auth_header_no_user', 'job_config', 'sample_user')
class TestSchedulerCreate:

    def test_scheduled_job_with_expired_token(self, sample_user, user_auth, job_config):
        """
        Schedule a job 8 seconds from now and then set token expiry after 5 seconds.
        So that after 5 seconds token will expire and job will run after 8 seconds.
        When job time comes, endpoint will call run_job method and which will refresh the expired token.
        Then check the new expiry time of expired token in test which should be in future
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """

        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

        auth_header = {'Authorization': 'Bearer ' + auth_token_row['access_token'],
                       'Content-Type': 'application/json'}

        current_datetime = datetime.datetime.utcnow() + datetime.timedelta(seconds=8)
        job_config['start_datetime'] = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Set the expiry after 5 seconds and update token expiry in db
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        expiry = expiry.strftime('%Y-%m-%d %H:%M:%S')

        db.db.session.commit()
        _update_token_expiry_(auth_token_row['user_id'], expiry)

        response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201
        data = response.json()
        assert data['id'] is not None

        # Sleep for 12 seconds till the job start and refreshes oauth token
        sleep(12)

        # After running the job first time. Token should be refreshed
        token = Token.query.filter_by(user_id=auth_token_row['user_id']).first()
        assert token.expires > datetime.datetime.utcnow()

        # Delete the created job
        auth_header['Authorization'] = 'Bearer ' + token.access_token
        response_remove = requests.delete(APP_URL % 'tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

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
        response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 400

        # Assign task_name in job post data (general task)
        job_config['task_name'] = 'Custom General Named Task'
        response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 201
        data = response.json()
        assert data['id'] is not None

        # Try to create already named job and it should throw 400 invalid usage error
        response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 400

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL % 'tasks/id/' + data['id'],
                                          headers=auth_header_no_user)
        assert response_remove.status_code == 200

    def test_request_send_url(self, auth_header, job_config):
        """
        Test dummy endpoint SendRequest to test send_request method is working fine.
        :param auth_header:
        :param job_config:
        :return:
        """
        response = requests.post(APP_URL % 'tasks/test/', data=json.dumps(job_config),
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
        response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL % 'tasks/id/' + data['id'],
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
            response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs = requests.delete(APP_URL % 'tasks/',
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

        response = requests.post(APP_URL % 'tasks/', data=json.dumps(job_config),
                                 headers=invalid_header)
        assert response.status_code == 401


