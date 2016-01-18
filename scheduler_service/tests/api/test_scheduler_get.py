"""
Test cases for getting already scheduled job with or without id. Also it should not be retrieved without
using bearer token
"""

# Third party imports
import json
import requests

# Application imports
from scheduler_service.common.routes import SchedulerApiUrl


__author__ = 'saad'


class TestSchedulerGet(object):

    def test_single_job(self, auth_header, job_config):
        """
        Get job using id and then delete it. Again try to get that job using id should give 404 status code
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
        data = response.json()

        # Now get the job
        response_get = requests.get(SchedulerApiUrl.TASK % data['id'],
                                    headers=auth_header)
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['task']['id'] == data['id']

        job_data = response_get.json()['task']

        assert job_data['start_datetime'] == job_config['start_datetime']
        assert job_data['end_datetime'] == job_config['end_datetime']
        assert int(job_data['frequency']['seconds']) == job_config['frequency']
        assert job_data['post_data'] == job_config['post_data']
        assert job_data['task_type'] == job_config['task_type']
        assert job_data['url'] == job_config['url']

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(SchedulerApiUrl.TASK % data['id'], headers=auth_header)
        assert response.status_code == 404

    def test_single_job_without_user(self, auth_header_no_user, job_config):
        """
        Create a job by hitting the endpoint with secret_key (no authenticated user) and make sure we get job_id in
        response.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        # Assign task_name in job post data (general task)
        job_config['task_name'] = 'General_Named_Task'

        # Get the job using correct task name
        response_get = requests.get(SchedulerApiUrl.TASK_NAME % job_config['task_name'],
                                    headers=auth_header_no_user)

        # If task with the same name already exist
        if response_get.status_code == 400:
            response_delete = requests.delete(SchedulerApiUrl.TASK_NAME % job_config['task_name'],
                                              headers=auth_header_no_user)
            assert response_delete.status_code == 200

        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Now get the job
        response_get = requests.get(SchedulerApiUrl.TASK % data['id'],
                                    headers=auth_header_no_user)
        assert response_get.status_code == 200

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header_no_user)
        assert response_remove.status_code == 200

    def test_job_without_user(self, auth_header_no_user, job_config):
        """
        Create a job by hitting the endpoint with secret_key (no authenticated user) and make sure we get job_id in
        response. Also try to get task using 'invalid_name' string which shouldn't be in apscheduler. So, it should
        return task not found exception (404)
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        # Assign task_name in job post data (general task)
        job_config['task_name'] = 'General_Named_Task'
        response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                 headers=auth_header_no_user)
        assert response.status_code == 201
        data = response.json()
        assert data['id']

        # Now get the job using invalid task name
        response_get = requests.get(SchedulerApiUrl.TASK_NAME % 'invalid_name',
                                    headers=auth_header_no_user)
        assert response_get.status_code == 404

        # Now get the job using correct task name
        response_get = requests.get(SchedulerApiUrl.TASK_NAME % job_config['task_name'],
                                    headers=auth_header_no_user)
        assert response_get.status_code == 200

        job_data = response_get.json()['task']

        assert job_data['task_name'] == job_config['task_name']

        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK_NAME % job_config['task_name'],
                                          headers=auth_header_no_user)
        assert response_remove.status_code == 200

    def test_multiple_jobs_without_user(self, auth_header_no_user, job_config):
        """
        Create multiple jobs and save the ids in a list. Then get all tasks of the current user which is None in this case.
        Then check if the jobs created are in the tasks of user. If yes, then show status code 200.
        Finally, delete the jobs.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = []
        # Create tasks
        for i in range(10):
            job_config['task_name'] = 'Custom_General_Named_Task_%s' % i
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header_no_user)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # Get tasks
        response_get = requests.get(SchedulerApiUrl.TASKS, data=json.dumps(dict(ids=jobs_id)),
                                    headers=auth_header_no_user)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        # Assert the job ids in the retrieved jobs
        for job in jobs_id:
            assert job in get_jobs_id

        # Delete all jobs
        for job_id in jobs_id:
            response_remove = requests.delete(SchedulerApiUrl.TASK % job_id,
                                              headers=auth_header_no_user)
            assert response_remove.status_code == 200

    def test_multiple_jobs(self, auth_header, job_config):
        """
        Create multiple jobs and save the ids in a list. Then get all tasks of the current user.
        Then check if the jobs created are in the tasks of user. If yes, then show status code 200
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

        response_get = requests.get(SchedulerApiUrl.TASKS, data=json.dumps(dict(ids=jobs_id)),
                                    headers=auth_header)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        for job in jobs_id:
            assert job in get_jobs_id
        # Delete all jobs
        response_remove = requests.delete(SchedulerApiUrl.TASKS, data=json.dumps(dict(ids=jobs_id)),
                                          headers=auth_header)
        assert response_remove.status_code == 200

    def test_scheduled_get_job_without_token(self, auth_header, job_config):
        """
        Get job without using bearer token it should return 401 status code
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

        # Get the job with invalid token
        response_get = requests.get(SchedulerApiUrl.TASK % data['id'],
                                    headers=invalid_header)

        assert response_get.status_code == 401
        # Let's delete jobs now
        response_remove = requests.delete(SchedulerApiUrl.TASK % data['id'],
                                          headers=auth_header)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(SchedulerApiUrl.TASK % data['id'], headers=auth_header)
        assert response.status_code == 404
