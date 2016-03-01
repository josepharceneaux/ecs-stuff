"""
Test cases for monitoring that whether the job is running or not.
Also test bulk tests for jobs
"""
# Std imports
import time


# Third party imports
import json
import datetime
from time import sleep
import requests

# Application imports
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token, User
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.tests.conftest import sample_user
from scheduler_service.common.utils.models_utils import get_by_id

__author__ = 'saad'


class TestSchedulerMisc(object):

    def test_scheduled_job_with_expired_token(self, sample_user, user_auth, job_config, job_cleanup):
        """
        Schedule a job 12 seconds from now and then set token expiry after 5 seconds.
        So that after 5 seconds token will expire and job will be in running state after 8 seconds.
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

        current_datetime = datetime.datetime.utcnow() + datetime.timedelta(seconds=12)
        job_config['start_datetime'] = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Set the expiry after 5 seconds and update token expiry in db
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        expiry = expiry.strftime('%Y-%m-%d %H:%M:%S')

        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201
        data = response.json()
        assert data['id']

        _update_token_expiry_(auth_token_row['user_id'], expiry)

        # Sleep for 25 seconds till the job start and refresh oauth token
        sleep(25)

        # After running the job first time. Token should be refreshed
        db.db.session.commit()
        token = Token.query.filter_by(user_id=auth_token_row['user_id']).first()
        assert token.expires > datetime.datetime.utcnow()

        # Delete all jobs created in this test case using fixture finalizer
        auth_header['Authorization'] = 'Bearer ' + token.access_token
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = [data['id']]

    def test_run_job_with_expired_token(self, sample_user, user_auth, job_config):
        """
        Create a job by hitting the endpoint and make sure response
        is correct.
        After post request to endpoint /tasks/test. oauth token will be expired and also refreshed.
        So, check if token is refreshed (i.e token expiry should be in future before and after post request)
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """

        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

        auth_token = auth_token_row['access_token']

        auth_header = {'Authorization': 'Bearer ' + auth_token,
                       'Content-Type': 'application/json'}

        job_config.update({'expired': True})

        response = requests.post(SchedulerApiUrl.TEST_TASK, data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 200

        db.db.session.commit()
        token = Token.query.filter_by(user_id=auth_token_row['user_id']).first()

        assert token
        assert token.expires > datetime.datetime.utcnow()

    def test_bulk_schedule_jobs(self, auth_header, job_config, job_cleanup):
        """
        For load testing and scalability, we need to add jobs in bulk and check if they are
        scheduled correctly and then delete them afterwards
         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs = []
        # Check with 800 jobs
        load_number = 800
        start_date = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        # Schedule some jobs and remove all of them
        for i in range(load_number):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        time.sleep(10)
        chunk_size = 200

        # Delete all created jobs in chunks specified above
        for i in range(0, load_number, chunk_size):
            jobs_chunk = jobs[i:i + chunk_size]

            try:
                response_remove_jobs = requests.delete(SchedulerApiUrl.TASKS,
                                                       data=json.dumps(dict(ids=jobs_chunk)),
                                                       headers=auth_header)
                assert response_remove_jobs.status_code == 200
            except Exception as e:
                print 'test_bulk_schedule_jobs: %s' % e.message

    def test_start_datetime_in_past(self, auth_header, job_config, job_cleanup):
        """
        If job's start time is in past and within past 0-30 seconds we should schedule it, otherwise
        an exception should be thrown.
        Check if time is 1 minute in past, then schedule job and it should throw exception
        :param auth_header: Fixture that contains token.
        :param job_config: (dict): Fixture that contains job config to be used as
        :return:
        """
        start_datetime = datetime.datetime.utcnow()
        job_config['start_datetime'] = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Let's delete job now
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = [data['id']]

        start_datetime = datetime.datetime.utcnow() - datetime.timedelta(seconds=31)
        job_config['start_datetime'] = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 400

    def test_get_already_deleted_job(self, auth_header, job_config_one_time_task):
        """
        Schedule a one time job and then wait for its time to pass, then try to get that job.
        Job should not be there.
        :param auth_header: Fixture that contains token.
        :param job_config_one_time_task: (dict): Fixture that contains job config to be used
        :return:
        """
        run_datetime = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        job_config_one_time_task['run_datetime'] = run_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config_one_time_task),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        time.sleep(15)

        # Now get the job
        response_get = requests.get(SchedulerApiUrl.TASK % data['id'],
                                    headers=auth_header)
        assert response_get.status_code == 404

    def test_delete_jobs_of_deleted_user(self, sample_user, auth_header_no_user, auth_header, post_ten_jobs, job_config):
        """
        Schedule 11 jobs. Then delete the user and wait for first job to run and check if all jobs of that user
        deleted
        :param auth_header: Fixture that contains token.
        :param post_ten_jobs: (dict): Fixture that contains 10 job configs to be used
        :param job_config: (dict): Fixture that contains jobs config to be used
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=60)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header.copy())
        assert response.status_code == 201

        user_id = sample_user.id
        sample_user.delete()

        # Wait for the job to run and delete all jobs of the sample user
        time.sleep(80)

        response_get = requests.get(SchedulerApiUrl.TEST_TASK,
                                    data=json.dumps({'user_id': user_id}),
                                    headers=auth_header_no_user)
        assert response_get.status_code == 200

        # There shouldn't be any jobs of sample user now
        len(response_get.json()['tasks']) == 0


def _update_token_expiry_(user_id, expiry):
    """
    Update expiry datetime of token filtered by user_id
    :param user_id: user_id who owned token
    :param expiry: expiry datetime to set
    :return:
    """
    db.db.session.commit()
    token = Token.query.filter_by(user_id=user_id).first()
    assert token
    token.update(expires=expiry)
    return token


