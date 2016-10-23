"""
Pause jobs which are already scheduled and in running state.
Also try to pause jobs without using token and it should give 401 status code
"""

# Third party imports
import json
import requests
import pytest

# Application imports
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.custom_exceptions import SchedulerServiceApiException
from scheduler_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


__author__ = 'saad'


class TestSchedulerPause(object):

    def test_single_job(self, auth_header, job_config, job_cleanup):
        """
        Create a job by hitting endpoint. Then stop it using endpoint. We then stop it again and
        it should give error (6053).
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs = []

        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs.append(response.json()['id'])
        job_id = jobs[0]

        # Send job stop request
        response_stop = requests.post(SchedulerApiUrl.PAUSE_TASK % job_id,
                                      headers=auth_header)
        assert response_stop.status_code == 200

        # Paused jobs have their 'next_run_datetime' set to 'None'
        response = requests.get(SchedulerApiUrl.TASK % job_id, headers=auth_header)
        next_run_datetime = response.json()['task']['next_run_datetime']
        assert next_run_datetime is None

        # Try stopping again, it should throw exception
        response_stop_again = requests.post(SchedulerApiUrl.PAUSE_TASK % job_id,
                                            headers=auth_header)
        assert response_stop_again.status_code == 400 and \
               response_stop_again.json()['error']['code'] == SchedulerServiceApiException.CODE_ALREADY_PAUSED

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK % job_id,
                                          headers=auth_header)
        assert response_remove.status_code == 200

        del jobs[:1]
        # Check if rest of the jobs are okay
        for job_id in jobs:
            response_get = requests.get(SchedulerApiUrl.TASK % job_id,
                                        headers=auth_header)
            assert response_get.json()['task']['id'] == job_id and \
                   response_get.json()['task']['next_run_datetime']

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs

    def test_multiple_jobs(self, auth_header, job_config, job_cleanup):
        """
        Pause already running scheduled jobs and then see it returns 200 status code and also get jobs
        and check their next_run_datetime is none (Paused job has next_run_datetime equal to None)
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = []

        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # Send job stop request
        response_stop = requests.post(SchedulerApiUrl.PAUSE_TASKS, data=json.dumps(dict(ids=jobs_id)),
                                      headers=auth_header)
        assert response_stop.status_code == 200

        jobs = []
        # Paused jobs have their next_run_datetime set to 'None'

        # Get jobs
        for job_id in jobs_id:
            response_get = requests.get(SchedulerApiUrl.TASK % job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=auth_header)
            jobs.append(response_get.json()['task'])

        # Now after getting jobs check their next run time
        for res in jobs:
            next_run_datetime = res['next_run_datetime']
            assert next_run_datetime is None

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs_id

    def test_single_pause_job_without_token(self, auth_header, job_config):
        """
        Try to pause an already scheduled job using invalid or no token, then check if it shows 401 response
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
        # Set the token to invalid
        invalid_header['Authorization'] = 'Bearer invalid_token'

        # Send job stop request
        response_stop = requests.post(SchedulerApiUrl.PAUSE_TASK % data['id'],
                                      headers=invalid_header)
        assert response_stop.status_code == 401

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(SchedulerApiUrl.TASK % data['id'], headers=auth_header)
        assert response.status_code == 404

    def test_multiple_pause_jobs_without_token(self, auth_header, job_config, job_cleanup):
        """
        Pause multiple jobs which are already scheduled and running without using token and then check
        if the response is 401
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = []

        for i in range(10):
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        invalid_header = auth_header.copy()
        invalid_header['Authorization'] = 'Bearer invalid_token'

        # Send job stop request with invalid token
        response_stop = requests.post(SchedulerApiUrl.PAUSE_TASKS, data=json.dumps(dict(ids=jobs_id)),
                                      headers=invalid_header)
        assert response_stop.status_code == 401

        # Paused jobs have their next_run_datetime set to 'None'
        jobs = []

        # Get all jobs
        for job_id in jobs_id:
            response_get = requests.get(SchedulerApiUrl.TASK % job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=auth_header)
            assert response_get.status_code == 200
            jobs.append(response_get.json())

        # Now check if their next run time is None
        for res in jobs:
            next_run_datetime = res['task']['next_run_datetime']
            assert next_run_datetime != 'None'

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs_id

    @pytest.mark.qa
    def test_pause_job_with_invalid_id(self, auth_header):
        """
        Try to pause job with invalid id's. Should return 404(not found).
        """
        for invalid_job_id in CampaignsTestsHelpers.INVALID_IDS[:3]:
            response = requests.post(SchedulerApiUrl.PAUSE_TASK % invalid_job_id,
                                     headers=auth_header)
            assert response.status_code == requests.codes.NOT_FOUND

    @pytest.mark.qa
    def test_pause_scheduled_task_by_other_domain_user(self, auth_header, job_config, access_token_other):
        """
        Schedule a job from a user and then try to pause same task from a different user in different domain
        """
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header)
        assert response.status_code == requests.codes.CREATED
        data = response.json()
        auth_header['Authorization'] = 'Bearer %s' % access_token_other
        # Now get the job from other user in different domain
        response = requests.post(SchedulerApiUrl.PAUSE_TASK % data['id'],
                                 headers=auth_header)
        assert response.status_code == requests.codes.NOT_FOUND

    @pytest.mark.qa
    def test_pause_multiple_jobs_with_invalid_ids(self, auth_header):
        """
        Try to pause multiple tasks with invalid id's. Should return 400 (bad request).
        """
        invalid_job_ids = CampaignsTestsHelpers.INVALID_IDS
        response = requests.post(SchedulerApiUrl.PAUSE_TASKS, data=json.dumps(dict(ids=invalid_job_ids)),
                                 headers=auth_header)
        assert response.status_code == requests.codes.BAD_REQUEST
