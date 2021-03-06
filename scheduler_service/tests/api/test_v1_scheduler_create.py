"""
Test cases for creating schedule job with and without token.
"""

# Std imports
import json

# Third party imports
import requests

# Application imports
import time
from datetime import timedelta, datetime
from scheduler_service import db, redis_store
from scheduler_service.common.models.user import User
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.tests.conftest import sample_user
from scheduler_service.modules.CONSTANTS import REQUEST_COUNTER

__author__ = 'saad'


class TestSchedulerCreate(object):

    def test_single_scheduled_job(self, auth_header, job_config, job_cleanup):
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

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = [data['id']]

    def test_dummy_endpoint_accesstoken_job(self, sample_user, auth_header, job_config_one_time_task):
        """
        Create a job by hitting the endpoint and make sure response
        is correct. Job will be one time and run after 16 seconds.
        Then wait for job to hit our scheduler service dummy endpoint.
        Create a test user and pass its id to post_data
        Dummy endpoint will delete test user. In the test, check if that test user exist
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        test_user = User.query.filter_by(email=sample_user.email).first()
        user_id = test_user.id
        run_datetime = datetime.utcnow() + timedelta(seconds=10)
        job_config_one_time_task['run_datetime'] = run_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        job_config_one_time_task['post_data'].update({'test_user_id': test_user.id})
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config_one_time_task),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Wait till job run
        time.sleep(60)

        # Scheduler endpoint should delete test user
        db.session.commit()
        test_user = User.query.filter_by(id=user_id).first()
        assert not test_user

    def test_dummy_endpoint_jwt_job(self, auth_header, job_config_one_time_task, sample_user):
        """
        Create a job by hitting the endpoint using jwt parameter equal to true and make sure response
        is correct. Job will be one time and run after 16 seconds.
        Then wait for job to hit our scheduler service dummy endpoint.
        Create a test user and pass its id to post_data
        Dummy endpoint will delete test user. In the test, check if that test user exist
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        test_user = User.query.filter_by(email=sample_user.email).first()
        user_id = test_user.id

        access_token = User.generate_jw_token(user_id=user_id)
        auth_header['Authorization'] = access_token

        job_config_one_time_task['is_jwt_request'] = True

        run_datetime = datetime.utcnow() + timedelta(seconds=10)
        job_config_one_time_task['run_datetime'] = run_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        job_config_one_time_task['post_data'].update({'test_user_id': test_user.id})
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config_one_time_task),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Wait till job run
        time.sleep(60)

        # Scheduler endpoint should delete test user
        db.session.commit()
        test_user = User.query.filter_by(id=user_id).first()
        assert not test_user

    def test_single_scheduled_job_without_user(self, auth_header_no_user, job_config, job_cleanup):
        """
        Create a job by hitting the endpoint with secret_key (global tasks) and make sure we get job_id in
        response.
        This test case is to create a named task which is in case of server to server user_auth (global tasks)
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
        job_config['task_name'] = 'General_Named_Task'
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Try to create already named job and it should throw 400 invalid usage error
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 400

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header_no_user
        job_cleanup['job_ids'] = [data['id']]

    def test_multiple_scheduled_jobs(self, auth_header, job_config, job_cleanup):
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

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs

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


