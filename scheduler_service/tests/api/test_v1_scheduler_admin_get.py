"""
Test cases for scheduler admin API. In the tests, get the jobs using the filters and check if the response is same
as expected
"""

# Third party imports
import requests


# Application imports
from scheduler_service import SchedulerUtils
from scheduler_service.common.models.user import DomainRole
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.utils.handy_functions import add_role_to_test_user


class TestSchedulerGet(object):

    def test_retrieve_jobs_as_admin(self, sample_user, auth_header, create_five_users, schedule_ten_jobs_for_each_user):
        """
        First try to get jobs without using token and check if the response is 401
        Try to get jobs using a common user without admin rights.
        Endpoint should return 401 Unauthorized error
        Then assign admin role to sample user.
        Try to get jobs again using a admin user and response should be 200
        """
        auth_header['Authorization'] = 'invalid token'

        # Test without admin access, should get 401 response
        response = requests.get(SchedulerApiUrl.ADMIN_TASKS + '?per_page=50',
                                headers=auth_header)

        assert response.status_code == 401

        # Test without admin access, should get 401 response
        response = requests.get(SchedulerApiUrl.ADMIN_TASKS + '?per_page=50',
                                headers=auth_header)

        assert response.status_code == 401

        # Assign admin role to user
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        response = requests.get(SchedulerApiUrl.ADMIN_TASKS + '?per_page=50',
                                headers=auth_header)

        assert response.status_code == 200

        assert len(response.json()['tasks']) == 50

    def test_retrieve_jobs_as_admin_using_user_id_filters(self, sample_user, auth_header, create_five_users,
                                                         schedule_ten_jobs_for_each_user,
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
        assert len(response.json()['tasks']) >= 10

    def test_retrieve_jobs_as_admin_using_task_category_filters(self, sample_user, auth_header, create_five_users,
                                                                schedule_ten_jobs_for_each_user):
        """
        In this test, use filters to get filtered tasks from admin API
        Test covers user_id, is_paused, task_category, task_type filters to test response from scheduler service endpoint
        """
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        # Get only user jobs by specifying task_category
        response = requests.get('{0}?per_page=50&task_category={1}'
                                .format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.CATEGORY_USER),
                                headers=auth_header)
        assert response.status_code == 200

        # There were 50 scheduled jobs which are user based
        assert len(response.json()['tasks']) >= 50

        # Get only general jobs by specifying task_category
        response = requests.get('{0}?per_page=50&task_category={1}'
                                .format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.CATEGORY_GENERAL),
                                headers=auth_header)
        assert response.status_code == 200

        # There should be 10 scheduled jobs which are general
        assert len(response.json()['tasks']) >= 10

    def test_retrieve_jobs_as_admin_using_task_type_filters(self, sample_user, auth_header, create_five_users,
                                                            schedule_ten_jobs_for_each_user):
        """
        In this test, use filters to get filtered tasks from admin API
        Test covers user_id, is_paused, task_category, task_type filters to test response from scheduler service endpoint
        """
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        # Get only periodic jobs by specifying task_type
        response = requests.get('{0}?per_page=50&task_type={1}'
                                .format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.PERIODIC),
                                headers=auth_header)
        assert response.status_code == 200

        # There are 10 periodic scheduled jobs
        assert len(response.json()['tasks']) >= 10

        # Get only one_time jobs by specifying task_type
        response = requests.get('{0}?per_page=50&task_type={1}'
                                .format(SchedulerApiUrl.ADMIN_TASKS, SchedulerUtils.ONE_TIME),
                                headers=auth_header)
        assert response.status_code == 200

        # There should be 40 scheduled jobs which are one_time
        assert len(response.json()['tasks']) >= 40

    def test_retrieve_jobs_as_admin_using_paused_filters(self, sample_user, auth_header, create_five_users,
                                                            schedule_ten_jobs_for_each_user):
        """
        In this test, use filters to get filtered tasks from admin API
        Test covers user_id, is_paused, task_category, task_type filters to test response from scheduler service endpoint
        """
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        # Get paused jobs only
        response = requests.get('{0}?per_page=50&paused={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'true'),
                                headers=auth_header)
        # There should be 10 paused jobs of user
        assert response.status_code == 200 and len(response.json()['tasks']) >= 10

        response = requests.get('{0}?per_page=50&paused={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'false'),
                                headers=auth_header)
        # There should be 40 jobs which are not paused.
        assert response.status_code == 200 and len(response.json()['tasks']) >= 50

    def test_retrieve_jobs_as_admin_using_invalid_filters(self, sample_user, auth_header, create_five_users,
                                                            schedule_ten_jobs_for_each_user):
        """
        In this test, use filters try to get filtered tasks from admin API using invalid filters
        Test covers user_id, is_paused, task_category, task_type filters to test response from scheduler service endpoint
        """
        users_list = create_five_users
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        # Try to get jobs using wrong is_paused value
        response = requests.get('{0}?per_page=50&is_paused={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'None'),
                                headers=auth_header)
        assert response.status_code == 400

        # Specify invalid task_category and try to get jobs. Should get 400 in response.
        response = requests.get('{0}?per_page=50&task_category={1}'.format(SchedulerApiUrl.ADMIN_TASKS, 'invalid'),
                                headers=auth_header)
        assert response.status_code == 400

        # Get jobs by specifying task_category as general and user_id. This case is invalid as the general jobs
        # are independent of user
        response = requests.get('{0}?per_page=50&user_id={1}&task_category={2}'.format(SchedulerApiUrl.ADMIN_TASKS,
                                                                                      users_list[0][0].id,
                                                                                      SchedulerUtils.CATEGORY_GENERAL),
                                headers=auth_header)
        assert response.status_code == 400

        # Specify invalid task_type and try to get jobs. Should get 400 in response.
        response = requests.get('{0}?per_page=50&task_type={1}'
                                .format(SchedulerApiUrl.ADMIN_TASKS, 'invalid'),
                                headers=auth_header)
        assert response.status_code == 400

    def test_retrieve_jobs_as_admin_using_mutliple_filters(self, sample_user, auth_header, create_five_users,
                                                            schedule_ten_jobs_for_each_user):
        """
        In this test, use filters try to get filtered tasks from admin API using invalid filters
        Test covers user_id, paused, task_category, task_type filters to test response from scheduler service endpoint
        """
        users_list = create_five_users
        add_role_to_test_user(sample_user, [DomainRole.Roles.CAN_GET_ALL_JOBS])

        # Get jobs by specifying task_category as user and user_id. This will return all jobs of first user.
        response = requests.get('{0}?per_page=50&user_id={1}&task_category={2}'.format(SchedulerApiUrl.ADMIN_TASKS,
                                                                                       users_list[0][0].id,
                                                                                       SchedulerUtils.CATEGORY_USER),
                                headers=auth_header)
        assert response.status_code == 200

        assert len(response.json()['tasks']) >= 10

        # Get jobs using all available filters
        response = requests.get('{0}?per_page=50&user_id={1}&task_category={2}&task_type=user&paused=0'
                                .format(SchedulerApiUrl.ADMIN_TASKS,
                                        users_list[0][0].id,
                                        SchedulerUtils.CATEGORY_USER),
                                headers=auth_header)
        assert response.status_code == 200

        assert len(response.json()['tasks']) >= 10
