"""
Test cases for deleting job with and with out token.
First create few jobs using service endpoint. After that delete these jobs using job_id of each job and
also check for the case when invalid bearer token is passed.
"""

# Third party imports
import json
import requests

# Application imports
from scheduler_service.common.routes import SchedulerApiUrl


__author__ = 'saad'


class TestSchedulerDelete(object):

    def test_single_job(self, auth_header, job_config):
        """
        Create a single job and it should give 200 status code, then delete that created job.
        after that check if the job is still there, it should give 404 status code while accessing
        a deleted job.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        # Creating a job
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == 201
        job_id = response.json()['id']

        # Removing a job
        response_remove = requests.delete(SchedulerApiUrl.TASK % job_id,
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(SchedulerApiUrl.TASK % job_id, headers=auth_header)
        assert response.status_code == 404

    def test_multiple_jobs(self, auth_header, job_config):
        """
        First, create jobs using correct ids, should return 200 status code.
        Then we delete all jobs. Then we create 10 scheduled jobs and 1 invalid job (which
        doesn't exist on the server). Then we try to delete all the jobs. Server does delete
        all scheduled jobs but couldn't find the invalid one and hence returns 207.

         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs = []

        # schedule 10 jobs and remove all of them
        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        # Delete all of them
        response_remove_jobs = requests.delete(SchedulerApiUrl.TASKS,
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=auth_header)

        assert response_remove_jobs.status_code == 200

        # Emptying the job list
        del jobs[:]

        # add a non-existing or invalid job and check if it shows 207 status code
        jobs.append('Non-existing job')
        # schedule 10 jobs and remove all of them
        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])
        # Then removed all scheduled jobs
        response_remove_jobs = requests.delete(SchedulerApiUrl.TASKS,
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=auth_header)
        # Returning 207 because 'Non-existing job' doesn't exist and server couldn't find it
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
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id']

        invalid_header = auth_header.copy()

        # set the token to invalid
        invalid_header['Authorization'] = 'Bearer invalid_token'

        # send job delete request
        response_delete = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=invalid_header)
        assert response_delete.status_code == 401

        # Now try deleting job with correct token
        response_delete = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)

        assert response_delete.status_code == 200

        # send job delete request, job shouldn't exist now, hence we will get a 404
        response_delete = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)

        assert response_delete.status_code == 404

    def test_multiple_delete_jobs_without_token(self, auth_header, job_config):
        """
        Create 10 jobs and then try to delete them without token and we get 401 for all.
        Then try deleting them with correct token and they should be deleted.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs = []

        # schedule some jobs
        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        invalid_header = auth_header.copy()
        invalid_header['Authorization'] = 'Bearer invalid_token'

        for job_id in jobs:
            response_remove = requests.delete(SchedulerApiUrl.TASK + job_id,
                                              headers=invalid_header)
            assert response_remove.status_code == 401

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASKS, data=json.dumps(dict(ids=jobs)),
                                          headers=auth_header)
        assert response_remove.status_code == 200
