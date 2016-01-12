"""
Test cases for monitoring that whether the job is running or not.
Also test bulk tests for jobs
"""
# Third party imports
import json

import datetime
from time import sleep

import requests

# Application imports
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token
from scheduler_service.common.routes import SchedulerApiUrl

__author__ = 'saad'


class TestSchedulerMisc(object):

    def test_scheduled_job_with_expired_token(self, sample_user, user_auth, job_config):
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

        _update_token_expiry_(auth_token_row['user_id'], expiry)

        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Sleep for 25 seconds till the job start and refresh oauth token
        sleep(25)

        # After running the job first time. Token should be refreshed
        db.db.session.commit()
        token = Token.query.filter_by(user_id=auth_token_row['user_id']).first()
        assert token.expires > datetime.datetime.utcnow()

        # Delete the created job
        auth_header['Authorization'] = 'Bearer ' + token.access_token
        response_remove = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

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

    def test_bulk_schedule_jobs(self, auth_header, job_config):
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
        # Schedule some jobs and remove all of them
        for i in range(load_number):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        chunk_size = 200

        # Delete all created jobs in chunks specified above
        for i in range(0, load_number, chunk_size):
            jobs_chunk = jobs[i:i + chunk_size]
            response_remove_jobs = requests.delete(SchedulerApiUrl.TASKS,
                                                   data=json.dumps(dict(ids=jobs_chunk)),
                                                   headers=auth_header)

            assert response_remove_jobs.status_code == 200

    def test_start_datetime_in_past(self, auth_header, job_config):
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

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        start_datetime = datetime.datetime.utcnow() - datetime.timedelta(seconds=31)
        job_config['start_datetime'] = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 400


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


