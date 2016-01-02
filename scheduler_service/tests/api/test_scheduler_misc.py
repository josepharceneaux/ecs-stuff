"""
Test cases for monitoring that whether the job is running or not.
Also test bulk tests for jobs
"""
# Third party imports
import json

import datetime
import pytest
import requests

# Application imports
from scheduler_service.tests.conftest import APP_URL

__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config')
class TestSchedulerMisc:

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
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        chunk_size = 200

        # Delete all created jobs in chunks specified above
        for i in range(0, load_number, chunk_size):
            jobs_chunk = jobs[i:i + chunk_size]
            response_remove_jobs = requests.delete(APP_URL + '/tasks/',
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
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        data = response.json()
        assert data['id'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        start_datetime = datetime.datetime.utcnow() - datetime.timedelta(seconds=31)
        job_config['start_datetime'] = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 400




