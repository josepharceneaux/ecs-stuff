"""
Test cases for delete job with and with out token
First create few jobs using service endpoint. After that delete these jobs using job_id of each job and
also check for the case when invalid bearer token is passed
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


@pytest.mark.usefixtures('auth_header', 'job_config')
class TestSchedulerDelete:

    def test_single_delete_job(self, auth_header, job_config):
        """
        Delete a single job and it should give 200 status code, then delete that created job.
        after that check if the job is still there, it should give 404 status code
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        job_id = response.json()['id']
        response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + job_id, headers=auth_header)
        assert response.status_code == 404

    def test_multiple_delete_job(self, auth_header, job_config):
        """
        First, delete jobs using correct ids, should return 200 status code
        After that, delete jobs using correct and incorrect ids, should return 207 status code with removed and not removed
         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
        jobs = []

        # schedule 10 jobs and remove all of them
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs = requests.delete(APP_URL + '/tasks/',
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=auth_header)

        assert response_remove_jobs.status_code == 200

        # free resources
        del jobs[:]

        # add a non-existing or invalid job and check if it shows 207 status code
        jobs.append('Non-existing job')
        # schedule 10 jobs and remove all of them
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs = requests.delete(APP_URL + '/tasks/',
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=auth_header)

        assert response_remove_jobs.status_code == 207

    def test_single_delete_job_without_token(self, auth_header, job_config):
        """
        Create a job and then try to delete the job with invalid token and
        we assert for a 401. Then we delete it with correct token and it's deleted.
        Finally, we make sure we cannot delete the job because it doesn't exist
        anymore.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        headers = auth_header.copy()

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        # send job delete request
        response_delete = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_delete.status_code == 401

        response_delete = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                           headers=auth_header)

        assert response_delete.status_code == 200

        # send job delete request...#job should n't exist now
        response_delete = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                           headers=auth_header)

        assert response_delete.status_code == 404

    def test_multiple_delete_jobs_without_token(self, auth_header, job_config):
        """
        Create 10 jobs and then try to delete them without token and we get 401s.
        Create and schedule jobs then remove all jobs
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
        jobs = []

        # schedule some jobs
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        headers = auth_header.copy()
        headers['Authorization'] = 'Bearer invalid_token'

        for job_id in jobs:
            response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                              headers=headers)
            assert response_remove.status_code == 401

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=auth_header)
        assert response_remove.status_code == 200
