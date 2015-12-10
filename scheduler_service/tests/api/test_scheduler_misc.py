"""
Test cases for monitoring that whether the job is running or not.
Also test bulk tests for jobs
"""
# Standard imports
import datetime

# Third party imports
import json
from pytz import timezone
from time import sleep
import pytest
import requests
from dateutil.parser import parse

# Application imports
from scheduler_service.tests.conftest import APP_URL

__author__ = 'saad'


@pytest.mark.usefixtures('auth_header', 'job_config_periodic')
class TestSchedulerMisc:

    def test_monitor_job_running(self, auth_header, job_config_periodic):
        """
        Its important to check whether job is running or not. And more importantly, if job is running on correct
        time according to its frequency
            Args:
                auth_data: Fixture that contains token.
                job_config_periodic (dict): Fixture that contains job config to be used as
                POST data while hitting the endpoint.
            :return:
            """
        frequency = 10
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=3)
        end_date = start_date + datetime.timedelta(seconds=30)
        job_config_periodic['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config_periodic['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config_periodic['frequency'] = {"seconds": frequency}

        # Created a job
        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                 headers=auth_header)

        assert response.status_code == 201

        # Wait for 3 seconds for the job to start
        sleep(3)
        old_run_time = job_config_periodic['start_datetime']

        # Wait for the next runtime and then check if runtime changed and is greater
        for x in range(2):
            sleep(frequency)
            response_running = requests.get(APP_URL + '/tasks/id/' + response.json()['id'],
                                            headers=auth_header)
            task = response_running.json()

            # Parse date into UTC format
            str_current_run = parse(old_run_time)
            current_run = str_current_run.replace(tzinfo=timezone('UTC'))
            str_next_run = parse(task['task']['next_run_datetime'])
            next_run = str_next_run.replace(tzinfo=timezone('UTC'))

            # current run time should be lower than next run time to ensure job has at least run once
            assert current_run < next_run

            # set the old_run_time to the next_run_datetime
            old_run_time = task['task']['next_run_datetime']

        # delete job
        response_delete = requests.delete(APP_URL + '/tasks/id/' + response.json()['id'],
                                          headers=auth_header)

        assert response_delete.status_code == 200

    def test_bulk_schedule_jobs(self, auth_header, job_config_periodic):
        """
        For load testing and scalability, we need to add jobs in bulk and check if they are
        scheduled correctly and then delete them afterwards
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
        # Check with 800 jobs
        load_number = 800
        # Schedule some jobs and remove all of them
        for i in range(load_number):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config_periodic),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        chunk_size = 200

        # Delete all created jobs
        for i in range(0, load_number, chunk_size):
            jobs_chunk = jobs[i:i + chunk_size]
            response_remove_jobs = requests.delete(APP_URL + '/tasks/',
                                                   data=json.dumps(dict(ids=jobs_chunk)),
                                                   headers=auth_header)

            assert response_remove_jobs.status_code == 200
