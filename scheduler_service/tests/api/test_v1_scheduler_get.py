"""
Test cases for getting already scheduled job with or without id. Also it should not be retrieved without
using bearer token
"""

# Std imports
import json
import uuid

# Third party imports
import requests

# Application imports
# TODO: Correct this import
from auth_service.common.models.user import DomainRole
from scheduler_service import SchedulerUtils
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.utils.handy_functions import random_word, add_role_to_test_user

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

    def test_single_job_without_user(self, auth_header_no_user, job_config, job_cleanup):
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
        job_config['task_name'] = 'General_Named_Task' + '-' + uuid.uuid4().__str__()[0:8]

        # Get the job using correct task name
        response_get = requests.get(SchedulerApiUrl.TASK_NAME % job_config['task_name'],
                                    headers=auth_header_no_user)

        # If task with the same name already exist
        if response_get.status_code == 200:
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

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header_no_user
        job_cleanup['job_ids'] = [data['id']]

    def test_job_without_user(self, auth_header_no_user, job_config, job_cleanup):
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
        job_config['task_name'] = 'General_Named_Task' + '-' + uuid.uuid4().__str__()[0:8]
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

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header_no_user
        job_cleanup['job_ids'] = [data['id']]

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
        word = random_word(5)
        # Create tasks
        for i in range(10):
            job_config['task_name'] = word + str(i)
            response = requests.post(SchedulerApiUrl.TASKS, data=json.dumps(job_config),
                                     headers=auth_header_no_user)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # Get tasks
        response_get = requests.get(SchedulerApiUrl.TASKS,
                                    headers=auth_header_no_user)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        # Assert the job ids in the retrieved jobs
        for job in jobs_id:
            assert job in get_jobs_id

        # Delete all jobs
        for job_id in jobs_id:
            response_remove_job = requests.delete(SchedulerApiUrl.TASK % job_id,
                                                  headers=auth_header_no_user)

            assert response_remove_job.status_code == 200

    def test_multiple_jobs(self, auth_header, job_config, job_cleanup):
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

        response_get = requests.get(SchedulerApiUrl.TASKS,
                                    headers=auth_header)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        for job in jobs_id:
            assert job in get_jobs_id

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs_id

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

    def test_multiple_jobs_with_page_only(self, auth_header, post_hundred_jobs, job_cleanup):
        """
        Create multiple jobs and save the ids in a list. Then get 15 tasks of the current user using 'per_page' arg.
        Then check if there are 15 jobs returned. If yes, then show status code 200
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as POST data while hitting the endpoint.
        :return:
        """
        jobs_id = post_hundred_jobs

        # Get only 15 jobs
        per_page = 15
        # Should get 10 jobs in response
        response_get = requests.get('{0}?per_page={1}'.format(SchedulerApiUrl.TASKS, per_page),
                                    headers=auth_header)

        get_jobs_id = set(map(lambda job_: job_['id'], response_get.json()['tasks']))
        set_jobs_ids = set(jobs_id)

        assert len(set_jobs_ids.difference(get_jobs_id)) == 85

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs_id

    def test_multiple_jobs_with_page(self, auth_header, post_hundred_jobs, job_cleanup):
        """
        Get 10 tasks of the current user using 'page' and 'per_page' of 1-10 page
        arg. Then check if there are 10 jobs returned. If yes, then show status code 200
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = post_hundred_jobs
        # Get jobs of page 5
        page = 5

        # Get 10 job on page 5
        per_page = 10
        # Should get jobs from 40-49
        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, page, per_page),
                                    headers=auth_header)

        get_jobs_id = set(map(lambda job_: job_['id'], response_get.json()['tasks']))
        set_jobs_ids = set(jobs_id)

        assert len(set_jobs_ids.difference(get_jobs_id)) == 90

        # There are 100 jobs scheduled, try to get the jobs higher than per_page limit.
        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, 1, 105),
                                    headers=auth_header)

        get_jobs_id = set(map(lambda job_: job_['id'], response_get.json()['tasks']))

        # Max per_page limit is 50, so we get 50 tasks instead of 105
        assert len(set_jobs_ids.difference(get_jobs_id)) == 50

        # If we request job 90-99, it will return 10 jobs instead
        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, 10, 10),
                                    headers=auth_header)

        get_jobs_id = set(map(lambda job_: job_['id'], response_get.json()['tasks']))

        assert len(set_jobs_ids.difference(get_jobs_id)) == 90

        # If we request job of page 10 with per_page, it will return 0 jobs instead
        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, 10, 15),
                                    headers=auth_header)

        get_jobs_id = set(map(lambda job_: job_['id'], response_get.json()['tasks']))

        assert len(set_jobs_ids.difference(get_jobs_id)) == 100

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs_id

    def test_multiple_jobs_with_invalid_page_per_page(self, auth_header, post_ten_jobs, job_cleanup):
        """
        Create multiple jobs and save the ids in a list. Then get 10 tasks of the current user using invalid start
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        jobs_id = post_ten_jobs

        response_get = requests.get('{0}?page={1}'.format(SchedulerApiUrl.TASKS, -1),
                                    headers=auth_header)

        # Response should be 400 as start arg is invalid
        assert response_get.status_code == 400

        # Try with invalid per_page 0
        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, 1, 0),
                                    headers=auth_header)

        # Response should be 400 as start arg is invalid
        assert response_get.status_code == 400

        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, 3, -1),
                                    headers=auth_header)

        # Response should be 400 as start arg is invalid
        assert response_get.status_code == 400

        response_get = requests.get('{0}?page={1}&per_page={2}'.format(SchedulerApiUrl.TASKS, -1, -1),
                                    headers=auth_header)

        # Response should be 400 as page and per_page arg is invalid
        assert response_get.status_code == 400

        # Setting up job_cleanup to be used in finalizer to delete all jobs created in this test
        job_cleanup['header'] = auth_header
        job_cleanup['job_ids'] = jobs_id

    # TODO: We can add a test with no auth-token to get 403 error
    def test_retrieve_jobs_as_admin(self, sample_user, auth_header, create_five_users, schedule_ten_jobs_of_each_user):
        """
        Create 5 users, assign admin role to one of them. Then
        schedule 50 jobs of 5 different users, 10 each. Then get the jobs using admin user.
        """
        # TODO--kindly improve above comment
        # TODO--fixture 'schedule_ten_jobs_of_each_user' can be 'schedule_ten_jobs_for_each_user'
        # Test without admin access, should get 401 response
        response = requests.get(SchedulerApiUrl.ADMIN_TASKS + '?per_page=50',
                                headers=auth_header)

        assert response.status_code == 401

        # Assign admin role to user
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        response = requests.get(SchedulerApiUrl.ADMIN_TASKS + '?per_page=50',
                                headers=auth_header)

        # TODO--I don't see where jobs are being scheduled? Or it's not apparent due to lack of useful comments
        # TODO--We should assert on jobs of users as well. Do as many asserts as possible
        assert response.status_code == 200
        # TODO: IMO we can assert number of retrieved Jobs as you mentioned in docString.

    def test_retrieve_jobs_as_admin_using_filters(self, sample_user, auth_header, create_five_users, schedule_ten_jobs_of_each_user,
                                                  schedule_ten_general_jobs):
        """
        In this test, use filters to get filtered tasks from admin API
        Test covers user_id, is_paused, task_category, task_type filters to test response from scheduler service endpoint
        """
        users_list = create_five_users
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        # Get jobs of only first user
        response = requests.get('{0}?per_page=50&user_id={1}'.format(SchedulerApiUrl.ADMIN_TASKS, users_list[0][0].id),
                                headers=auth_header)

        assert response.status_code == 200

        # There should be 10 jobs of first user
        assert len(response.json()['tasks']) >= 10  # TODO: why > ? Here and every where else

        # Try to get jobs using wrong is_paused value
        response = requests.get('{0}?per_page=50&is_paused={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'None'),
                                headers=auth_header)
        assert response.status_code == 400

        # Get paused jobs only
        response = requests.get('{0}?per_page=50&is_paused={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'true'),
                                headers=auth_header)
        # There should be 10 jobs which we paused in the fixture
        # TODO--which fixture?
        assert response.status_code == 200 and len(response.json()['tasks']) >= 10

        response = requests.get('{0}?per_page=50&is_paused={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'false'),
                                headers=auth_header)
        # There should be 10 jobs which we paused in the fixture and 40 were not in paused state
        assert response.status_code == 200 and len(response.json()['tasks']) >= 50

        # Specify invalid task_category and try to get jobs. Should get 400 in response.
        response = requests.get('{0}?per_page=50&task_category={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'invalid'),
                                headers=auth_header)
        assert response.status_code == 400

        # Get only user jobs by specifying task_category
        response = requests.get('{0}?per_page=50&task_category={1}'.format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.CATEGORY_USER),
                                headers=auth_header)
        assert response.status_code == 200

        # There were 50 scheduled jobs which are user based
        assert len(response.json()['tasks']) >= 50

        # Get only general jobs by specifying task_category
        response = requests.get('{0}?per_page=50&task_category={1}'.format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.CATEGORY_GENERAL),
                                headers=auth_header)
        assert response.status_code == 200

        # There should be 10 scheduled jobs which are general
        assert len(response.json()['tasks']) >= 10

        # Specify invalid task_type and try to get jobs. Should get 400 in response.
        response = requests.get('{0}?per_page=50&task_type={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'invalid'),
                                headers=auth_header)
        assert response.status_code == 400

        # Get only periodic jobs by specifying task_type
        response = requests.get('{0}?per_page=50&task_type={1}'.format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.PERIODIC),
                                headers=auth_header)
        assert response.status_code == 200

        # There are 10 periodic scheduled jobs
        assert len(response.json()['tasks']) >= 10

        # Get only one_time jobs by specifying task_type
        response = requests.get('{0}?per_page=50&task_type={1}'.format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.ONE_TIME),
                                headers=auth_header)
        assert response.status_code == 200

        # There should be 40 scheduled jobs which are one_time
        assert len(response.json()['tasks']) >= 40

        # Get jobs by specifying task_category as general and user_id. This case is invalid as the general jobs
        # are independent of user
        response = requests.get('{0}?per_page=50&user_id={1}&task_category={2}'.format(SchedulerApiUrl.ADMIN_TASKS,
                                                                                      users_list[0][0].id,
                                                                                      SchedulerUtils.CATEGORY_GENERAL),
                                headers=auth_header)
        assert response.status_code == 400

        # Get jobs by specifying task_category as user and user_id. This will return all jobs of first user.
        response = requests.get('{0}?per_page=50&user_id={1}&task_category={2}'.format(SchedulerApiUrl.ADMIN_TASKS,
                                                                                      users_list[0][0].id,
                                                                                      SchedulerUtils.CATEGORY_USER),
                                headers=auth_header)
        assert response.status_code == 200

        # TODO--nice try. But this test needs refactoring. We need to break it down into more tests. I think one test
        # TODO--should test one functionality. It will be more clear and meaningful.
        assert len(response.json()['tasks']) >= 10

