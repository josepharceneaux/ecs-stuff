"""
Scheduler Restful-API which has endpoints to schedule, remove, delete, pause, resume single
or multiple jobs.
This API also checks for authentication token
"""

# Standard imports
import json
import types

# Third party imports
from flask import Blueprint, request
from flask.ext.restful import Resource

# Application imports
from scheduler_service import logger, SchedulerUtils
from scheduler_service.api.scheduler_tests_api import raise_if_scheduler_not_running, check_job_state, \
    dummy_request_method
from scheduler_service.common.models.user import DomainRole
from scheduler_service.common.routes import SchedulerApi
from scheduler_service.common.utils.api_utils import api_route, ApiResponse, get_pagination_params
from scheduler_service.common.talent_api import TalentApi
from scheduler_service.common.error_handling import InvalidUsage, ResourceNotFound
from scheduler_service.common.utils.auth_utils import require_oauth, require_all_roles
from scheduler_service.custom_exceptions import SchedulerServiceApiException
from scheduler_service.modules.scheduler import scheduler, schedule_job, serialize_task, remove_tasks
from scheduler_service.modules.scheduler_admin import filter_jobs_using_task_type, \
    filter_jobs_using_task_category, filter_paused_jobs

api = TalentApi()
scheduler_blueprint = Blueprint('scheduler_api', __name__)
api.init_app(scheduler_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(SchedulerApi.SCHEDULER_MULTIPLE_TASKS)
class Tasks(Resource):
    """
        This resource returns a list of tasks particular to a user by using pagination concept
         or it can be used to create or schedule a task using POST.
    """
    @require_oauth(allow_null_user=True)
    def get(self):
        """
        This action returns a list of user tasks and their count
        :return tasks_data: a dictionary containing list of tasks and their count
        :rtype json


        :Example (in case of pagination):
            By default, it will return 10 jobs (max)

            Case 1:

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/v1/tasks?page=3', headers=headers)

            # Returns 10 jobs ranging from 30-39

            Case 2:

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/v1/tasks?page=5&per_page=12', headers=headers)

            # Returns 12 jobs ranging from 48-59

        :Example:
        In case of authenticated user

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/v1/tasks/', headers=headers)

        In case of SECRET_KEY

            headers = {'Authorization': 'Bearer <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.get(API_URL + '/v1/tasks/', headers=headers)

        .. Response::

            {
                "count": 1,
                "tasks": [
                    {
                        "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                        "post_data": {
                            "url": "http://getTalent.com/sms/send/",
                            "phone_number": "09230862348",
                            "smart_list_id": 123456,
                            "content": "text to be sent as sms"
                            "some_other_kwarg": "abc",
                            "campaign_name": "SMS Campaign"
                        },
                        "frequency": 3601,      # in seconds
                        "start_datetime": "2015-11-05T08:00:00",
                        "end_datetime": "2015-12-05T08:00:00"
                        "next_run_datetime": "2015-11-05T08:20:30",
                        "task_type": "periodic"
                    }
               ]
            }

        .. Status:: 200 (OK)
                    400 (Invalid Usage)
                    500 (Internal Server Error)

        """
        # In case of higher number of scheduled task running for a particular user and user want to get only
        # a limited number of jobs by specifying page and per_page parameter, then return only specified jobs

        # Limit the jobs to 50 if user requests for more than 50
        max_per_page = 50

        # Default per_page size
        default_per_page = 10

        # If user didn't specify page or per_page, then it should be set to default 1 and 10 respectively.
        page, per_page = request.args.get('page', 1), request.args.get('per_page', default_per_page)

        if not (str(page).isdigit() and int(page) > 0):
            raise InvalidUsage(error_message="'page' arg should be a digit (greater than or equal to 1)")

        if not (str(per_page).isdigit() and int(per_page) >= default_per_page):
            raise InvalidUsage(
                error_message="'per_page' arg should be a digit and its value should be greater or equal to 10")

        page, per_page = int(page), int(per_page)

        # Limit the jobs if user requests jobs greater than 50
        if per_page > max_per_page:
            per_page = max_per_page

        user_id = request.user.id if request.user else None

        raise_if_scheduler_not_running()
        tasks = scheduler.get_jobs()
        tasks = filter(lambda _task: _task.args[0] == user_id, tasks)
        tasks_count = len(tasks)
        # If page is 1, and per_page is 10 then task_indices will look like list of integers e.g [0-9]
        task_indices = range((page-1) * per_page, page * per_page)

        tasks = [serialize_task(tasks[index])
                 for index in task_indices if index < tasks_count and tasks[index]]

        tasks = [task for task in tasks if task]
        header = {
            'X-Total': tasks_count,
            'X-Per-Page': per_page,
            'X-Page': page
        }
        return ApiResponse(response=dict(tasks=tasks), headers=header)

    @require_oauth(allow_null_user=True)
    def post(self):
        """
        This method takes data to create or schedule a task for scheduler.

        :Example:
            for interval or periodic schedule
            task = {
                "task_name": "custom-task",     # Field required only in case of general task
                "frequency": 3601,
                "task_type": "periodic",
                "start_datetime": "2015-12-05T08:00:00",
                "end_datetime": "2016-01-05T08:00:00",
                "url": "http://getTalent.com/sms/send/",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms"
                }
            }
            for one_time schedule
            task = {
                "task_name": "custom-task",     # Field required only in case of general task
                "task_type": "one_time",
                "run_datetime": "2015-12-05T08:00:00",
                "url": "http://getTalent.com/email/send/",
                "post_data": {
                    "campaign_name": "Email Campaign",
                    "email": "user1@hotmail.com",
                    "smart_list_id": 123456,
                    "content": "content to be sent as email"
                }
            }

            In case of authenticated user

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }

            In case of SECRET_KEY

            headers = {'Authorization': 'Bearer <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>',
                        'Content-Type': 'application/json'
                        }

            data = json.dumps(task)
            response = requests.post(
                                        API_URL + '/v1/tasks/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "id" : "5das76nbv950nghg8j8-33ddd3kfdw2"
            }
        .. Status:: 201 (Resource Created)
                    400 (Bad Request)
                    401 (Unauthorized to access getTalent)
                    500 (Internal Server Error)

        :return: id of created task
        """
        # get JSON post request data
        raise_if_scheduler_not_running()
        try:
            task = request.get_json()
        except Exception:
            raise InvalidUsage("Bad Request, data should be in json")

        task_id = schedule_job(task, request.user.id if request.user else None, request.oauth_token)

        headers = {'Location': '/v1/tasks/%s' % task_id}
        response = json.dumps(dict(id=task_id))
        return ApiResponse(response, status=201, headers=headers)

    @require_oauth()
    def delete(self):
        """
        Deletes multiple tasks whose ids are given in list in request data.
        :param kwargs:
        :return:

        :Example:
            task_ids = {
                'ids': [fasdff12n22m2jnr5n6skf,ascv3h5k1j43k6k8k32k345jmn,123n23n4n43m2kkcj53vdsxc]
            }
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(task_ids)
            response = requests.delete(
                                        API_URL + '/v1/tasks/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': '3 task have been removed successfully'
            }
        .. Status:: 200 (Resource deleted)
                    207 (Not all removed)
                    400 (Bad request)
                    500 (Internal Server Error)

        """

        user_id = request.user.id
        raise_if_scheduler_not_running()
        # get task_ids for tasks to be removed
        try:
            req_data = request.get_json()
        except Exception:
            raise InvalidUsage("Bad Request, data should be in JSON",
                               error_code=SchedulerServiceApiException.CODE_INVALID_USAGE)
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else None
        if not task_ids:
            raise InvalidUsage("Bad request, No data in ids", error_code=400)
        # check if tasks_ids list is not empty
        removed = remove_tasks(task_ids, user_id=user_id)
        if len(removed) == len(task_ids):
            logger.info('Job with ids %s removed successfully.' % task_ids)
            return dict(
                message='%s Tasks removed successfully' % len(removed))

        # removed_jobs have valid jobs - filters in remove_tasks
        # job[1] contains job id
        removed_jobs = map(lambda job: job[1], removed)
        not_removed = list(set(task_ids) - set(removed_jobs))
        if not_removed:
            logger.info('Job with ids %s removed successfully and unable to remove jobs %s' % (task_ids, not_removed))
            return dict(message='Unable to remove %s tasks' % len(not_removed),
                        removed=removed,
                        not_removed=not_removed), 207


@api.route(SchedulerApi.SCHEDULER_MULTIPLE_TASK_RESUME)
class ResumeTasks(Resource):
    """
        This resource resumes a previously paused jobs/tasks
    """
    decorators = [require_oauth()]

    def post(self):
        """
        Resume a previously paused tasks/jobs
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            task_ids = {
                'ids': [fasdff12n22m2jnr5n6skf,ascv3h5k1j43k6k8k32k345jmn,123n23n4n43m2kkcj53vdsxc]
            }
            headers = {'Authorization': 'Bearer <access_token>', 'Content-Type' : 'application/json'}
            response = requests.post(API_URL + '/v1/tasks/resume/', headers=headers, data=json.dumps(task_ids))

        .. Response::
            {
               "message":"Tasks have been resumed successfully"
            }

        .. Status:: 200 (OK)
                    207 (Not all paused)
                    404 (Bad Request)
                    500 (Internal Server Error)

        """
        user_id = request.user.id
        raise_if_scheduler_not_running()
        try:
            req_data = request.get_json()
        except Exception:
            raise InvalidUsage("Bad Request, data should be in JSON")
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else None
        if not task_ids:
            raise InvalidUsage("Bad Request, No data in ids", error_code=400)
        # Filter jobs that are not None
        valid_tasks = [task for task in task_ids if scheduler.get_job(job_id=task)]
        if valid_tasks:
            # Only keep jobs that belonged to the auth user
            valid_tasks = filter(lambda task_id: scheduler.get_job(job_id=task_id).args[0] == user_id, valid_tasks)
            # Resume each job
            for _id in valid_tasks:
                scheduler.resume_job(job_id=_id)
            if len(valid_tasks) != len(task_ids):
                none_tasks = filter(lambda task_id: scheduler.get_job(job_id=task_id) is None, task_ids)
                return dict(message='Unable to resume %s tasks' % len(none_tasks),
                            paused=valid_tasks,
                            not_found=none_tasks), 207
            return dict(message="Tasks have been successfully resumed")
        raise InvalidUsage('Bad request, invalid data in request', error_code=400)


@api.route(SchedulerApi.SCHEDULER_MULTIPLE_TASK_PAUSE)
class PauseTasks(Resource):
    """
        This resource pauses jobs/tasks which can be resumed again
    """
    decorators = [require_oauth()]

    def post(self):
        """
        Pause tasks which are currently running.

        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            task_ids = {
                'ids': [fasdff12n22m2jnr5n6skf,ascv3h5k1j43k6k8k32k345jmn,123n23n4n43m2kkcj53vdsxc]
            }
            headers = {'Authorization': 'Bearer <access_token>', 'Content-Type' : 'application/json'}
            response = requests.post(API_URL + '/v1/tasks/resume/', headers=headers, data=json.dumps(task_ids))

        .. Response::
            {
               "message":"Tasks have been paused successfully"
            }

        .. Status:: 200 (OK)
                    400 (Bad Request)
                    207 (Not all Paused)
                    500 (Internal Server Error)

        """
        user_id = request.user.id
        raise_if_scheduler_not_running()
        try:
            req_data = request.get_json()
        except Exception:
            raise InvalidUsage("Bad Request, data should be in json")
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else None
        if not task_ids:
            raise InvalidUsage("Bad request, No data in ids", error_code=400)
        # Filter tasks which are None and of the current user
        valid_tasks = filter(lambda task_id: scheduler.get_job(job_id=task_id) and
                                             scheduler.get_job(job_id=task_id).args[0] == user_id, task_ids)
        if valid_tasks:
            for _id in valid_tasks:
                scheduler.pause_job(job_id=_id)
            if len(valid_tasks) != len(task_ids):
                none_tasks = filter(lambda task_id: scheduler.get_job(job_id=task_id) is None, task_ids)
                return dict(message='Unable to pause %s tasks' % len(none_tasks),
                            paused=valid_tasks,
                            not_found=none_tasks), 207

            return dict(message="Tasks have been successfully paused")
        raise InvalidUsage('Bad request, invalid data in request', error_code=400)


@api.route(SchedulerApi.SCHEDULER_NAMED_TASK)
class TaskByName(Resource):
    """
        This resource returns a specific task based on name
    """

    @require_oauth(allow_null_user=True)
    def get(self, _name):
        """
        This action returns a task owned by other service
        :param _name: name of task
        :type _name: str
        :return task: a dictionary containing a task data
        :rtype json

        :Example:

        In case of SECRET_KEY

            headers = {'Authorization': 'Bearer <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.get(API_URL + '/v1/tasks/name/custom_task', headers=headers)

        .. Response::
            {
               for one time scheduled task
               "task": {
                         {
                            "task_name": "custom_task",
                            "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                            "url": "http://getTalent.com/sms/send/",
                            "post_data": {
                                "campaign_name": "SMS Campaign",
                                "phone_number": "09230862348",
                                "smart_list_id": 123456,
                                "content": "text to be sent as sms"
                                "some_other_kwarg": "abc"
                            },
                            "frequency": 3601,
                            "start_datetime": "2015-11-05T08:00:00",
                            "end_datetime": "2015-12-05T08:00:00"
                            "next_run_datetime": "2015-11-05T08:20:30",
                            "task_type": "periodic"
                         }
                    }
               for interval scheduled task
               "task": {
                         {
                            "task_name": "custom_task",
                            "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                            "url": "http://getTalent.com/email/send/",
                            "post_data": {
                                "campaign_name": "Email Campaign",
                                "phone_number": "09230862348",
                                "smart_list_id": 123456,
                                "content": "text to be sent as Email"
                                "some_other_kwarg": "abc"
                            },
                            "run_datetime": "2015-11-05T08:00:00",
                            "task_type": "one_time"
                         }
                    }
        .. Status:: 200 (OK)
                    404 (Task not found)
                    500 (Internal Server Error)

        """
        user_id = request.user.id if request.user else None
        raise_if_scheduler_not_running()
        tasks = scheduler.get_jobs()
        task = [task for task in tasks if task.name == _name and task.args[0] is None]
        # Make sure task is valid and belongs to non-logged-in user
        if task and user_id is None:
            task = serialize_task(task[0])
            if task:
                return dict(task=task)
        raise ResourceNotFound(error_message="Task with name %s not found" % _name)

    @require_oauth(allow_null_user=True)
    def delete(self, _name):
        """
        Deletes/removes a tasks from scheduler jobstore
        :param kwargs:
        :param _name: name of general task
        :return:

        :Example:
        In case of SECRET_KEY

            headers = {'Authorization': 'Bearer <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.delete(API_URL + '/v1/tasks/name/custom_task', headers=headers)


        .. Response::

            {
                'message': 'Task has been removed successfully'
            }
        .. Status:: 200 (Resource deleted)
                    404 (Task Not found)
                    500 (Internal Server Error)

        """
        user_id = request.user.id if request.user else None
        raise_if_scheduler_not_running()
        tasks = scheduler.get_jobs()
        task = [task for task in tasks if task.name == _name and task.args[0] is None]
        # Check if task is valid and belongs to the logged-in user
        if task and user_id is None:
            scheduler.remove_job(task[0].id)
            return dict(message="Task has been removed successfully")
        raise ResourceNotFound(error_message="Task with name %s not found" % _name)


@api.route(SchedulerApi.SCHEDULER_ONE_TASK)
class TaskById(Resource):
    """
        This resource returns a specific task based on id or delete a task
    """

    @require_oauth(allow_null_user=True)
    def get(self, _id):
        """
        This action returns a task owned by a this user
        :param _id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :return task: a dictionary containing a task data
        :rtype json

        :Example:

        In case of authenticated user

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/v1/tasks/id/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

        In case of SECRET_KEY

            headers = {'Authorization': 'Bearer <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.get(API_URL + '/v1/tasks/id/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

        .. Response::
            {
               for one time schedule
               "task": {
                         {
                            "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                            "url": "http://getTalent.com/sms/send/",
                            "post_data": {
                                "campaign_name": "SMS Campaign",
                                "phone_number": "09230862348",
                                "smart_list_id": 123456,
                                "content": "text to be sent as sms"
                                "some_other_kwarg": "abc"
                            },
                            "frequency": 3601,
                            "start_datetime": "2015-11-05T08:00:00",
                            "end_datetime": "2015-12-05T08:00:00"
                            "next_run_datetime": "2015-11-05T08:20:30",
                            "task_type": "periodic"
                         }
                    }
               for interval schedule
               "task": {
                         {
                            "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                            "url": "http://getTalent.com/email/send/",
                            "post_data": {
                                "campaign_name": "Email Campaign",
                                "phone_number": "09230862348",
                                "smart_list_id": 123456,
                                "content": "text to be sent as Email"
                                "some_other_kwarg": "abc"
                            },
                            "run_datetime": "2015-11-05T08:00:00",
                            "task_type": "one_time"
                         }
                    }
        .. Status:: 200 (OK)
                    404 (Task not found)
                    500 (Internal Server Error)

        """
        user_id = request.user.id if request.user else None
        raise_if_scheduler_not_running()
        task = scheduler.get_job(_id)
        # Make sure task is valid and belongs to logged-in user
        if task and task.args[0] == user_id:
            task = serialize_task(task)
            if task:
                return dict(task=task)
        raise ResourceNotFound(error_message="Task not found")

    @require_oauth(allow_null_user=True)
    def delete(self, _id):
        """
        Deletes/removes a tasks from scheduler store
        :param kwargs:
        :param _id: job_id
        :return:

        :Example:
         In case of authenticated user

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.delete(API_URL + '/v1/tasks/id/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

        In case of SECRET_KEY

            headers = {'Authorization': 'Bearer <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.delete(API_URL + '/v1/tasks/id/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)


        .. Response::

            {
                'message': 'Task has been removed successfully'
            }
        .. Status:: 200 (Resource deleted)
                    404 (Task Not found)
                    500 (Internal Server Error)

        """
        user_id = request.user.id if request.user else None
        raise_if_scheduler_not_running()
        task = scheduler.get_job(_id)
        # Check if task is valid and belongs to the logged-in user
        if task and task.args[0] == user_id:
            scheduler.remove_job(task.id)
            logger.info('Job with id %s removed successfully.' % _id)
            return dict(message="Task has been removed successfully")
        raise ResourceNotFound(error_message="Task not found")


@api.route(SchedulerApi.SCHEDULER_SINGLE_TASK_RESUME)
class ResumeTaskById(Resource):
    """
        This resource resumes a previously paused job/task
    """
    decorators = [require_oauth()]

    def post(self, _id):
        """
        Resume a previously paused task/job
        :param _id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.post(API_URL + '/v1/tasks/5das76nbv950nghg8j8-33ddd3kfdw2/resume/', headers=headers)

        .. Response::
            {
               "message":"Task has been resumed successfully"
            }

        .. Status:: 200 (OK)
                    404 (Task not found)
                    500 (Internal Server Error)

        .. Error code:: 6054(Task Already running)

        """
        user_id = request.user.id
        raise_if_scheduler_not_running()
        # check and raise exception if job is already paused or not present
        task = check_job_state(job_id=_id, job_state_to_check='running')
        if task and task.args[0] == user_id:
            scheduler.resume_job(job_id=_id)
            return dict(message="Task has been successfully resumed")
        raise ResourceNotFound(error_message="Task not found")


@api.route(SchedulerApi.SCHEDULER_SINGLE_TASK_PAUSE)
class PauseTaskById(Resource):
    """
        This resource pauses job/task which can be resumed again
    """
    decorators = [require_oauth()]

    def post(self, _id):
        """
        Pause a task which is currently running.
        :param id: id of task
        :type _id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.post(API_URL + '/v1/tasks/5das76nbv950nghg8j8-33ddd3kfdw2/resume/', headers=headers)

        .. Response::
            {
               "message":"Task has been paused successfully"
            }

        .. Status:: 200 (OK)
                    404 (Task Not Found)
                    500 (Internal Server Error)

        .. Error code:: 6053(Task Already Paused)

        """
        # check and raise exception if job is already paused or not present
        user_id = request.user.id
        raise_if_scheduler_not_running()
        task = check_job_state(job_id=_id, job_state_to_check='paused')
        if task and task.args[0] == user_id:
            scheduler.pause_job(job_id=_id)
            return dict(message="Task has been successfully paused")
        raise ResourceNotFound(error_message="Task not found")


@api.route(SchedulerApi.SCHEDULER_ADMIN_TASKS)
class AdminTasks(Resource):
    """
        This resource returns a list of tasks owned by a user or service by using pagination and it's accessible to
        admin users only.
    """
    decorators = [require_oauth()]
    # a parent class and put all the core pagination functionality in its get() and then we can later override that

    @require_all_roles(DomainRole.Roles.CAN_GET_ALL_JOBS)
    def get(self):
        """
        This action returns a list of apscheduler scheduled tasks.
        :return tasks_data: a dictionary containing list of tasks
        :rtype: json


        :Example (in case of pagination):
            By default, it will return 30 jobs (max)

            Case 1:

             >>> headers = {'Authorization': 'Bearer <access_token>'}
             >>> response = requests.get(API_URL + '/admin/v1/tasks?page=2', headers=headers)

            # Returns 30 jobs ranging from 30-59 ( zero-based index )

            Case 2:

             >>> headers = {'Authorization': 'Bearer <access_token>'}
             >>> response = requests.get(API_URL + '/admin/v1/tasks?page=2&per_page=35', headers=headers)

            # Returns 35 jobs ranging from 35-69 ( zero-based index )

        :Example:
        # TODO--please explaining the following a bit more. Give eaxample each filter one by one. That would add more clarity

        In case of task_category filter

             >>> headers = {'Authorization': 'Bearer <access_token>'}
             >>> response = requests.get(API_URL + '/admin/v1/tasks?task_category=general', headers=headers)

        In case of task_type filter

             >>> headers = {'Authorization': 'Bearer <access_token>'}
             >>> response = requests.get(API_URL + '/admin/v1/tasks?task_type=periodic', headers=headers)

        In case of jobs of a specific user

             >>> headers = {'Authorization': 'Bearer <access_token>'}
             >>> response = requests.get(API_URL + '/admin/v1/tasks?user_id=2', headers=headers)


        In case of paused or running jobs only

             >>> headers = {'Authorization': 'Bearer <access_token>'}
             # returns paused jobs only
             >>> response = requests.get(API_URL + '/admin/v1/tasks?paused=true', headers=headers)
             # returns running jobs only
             >>> response = requests.get(API_URL + '/admin/v1/tasks?paused=false', headers=headers)


        Response will be similar to get all tasks endpoint with few additional fields

        .. Response::

            {
                "tasks": [
                    {
                        "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                        "user_email": "saad_lhr@hotmail.com",
                        "task_type": "user",
                        "post_data": {
                            "url": "http://getTalent.com/sms/send/",
                            "phone_number": "09230862348",
                            "smart_list_id": 123456,
                            "content": "text to be sent as sms"
                            "some_other_kwarg": "abc",
                            "campaign_name": "SMS Campaign"
                        },
                        "frequency": 3601,      # in seconds
                        "start_datetime": "2015-11-05T08:00:00",
                        "end_datetime": "2015-12-05T08:00:00"
                        "next_run_datetime": "2015-11-05T08:20:30",
                        "task_type": "periodic"
                    }
               ]
            }


        .. Status:: 200 (OK)
                    400 (Invalid Usage)
                    401 (Unauthorized Error)
                    500 (Internal Server Error)

        """
        # In case of higher number of scheduled task running for a particular user and user wants to get only
        # a limited number of jobs by specifying page and per_page parameter, then return only specified jobs

        # Default per_page size
        default_per_page = 30

        # If user didn't specify page or per_page, then it should default to 1 and 30 respectively.
        page, per_page = get_pagination_params(request, default_per_page=default_per_page)

        raise_if_scheduler_not_running()
        tasks = scheduler.get_jobs()

        # Get all param filters
        user_id, paused, task_type, task_category = request.args.get('user_id'), request.args.get('paused'), \
                                                       request.args.get('task_type'), \
                                                       request.args.get('task_category')

        # If user_id is given then only return jobs of that particular user
        if user_id:
            if not (str(user_id).isdigit() and int(user_id) > 0):
                raise InvalidUsage("user_id should be of type int")
            tasks = filter(lambda _task: _task.args[0] == int(user_id), tasks)

        # If paused is given then only return paused jobs.
        if paused:
            tasks = filter_paused_jobs(tasks, is_paused=paused)

        # If task_type is specified then return only specified `one_time` or `periodic` jobs
        if task_type:
            tasks = filter_jobs_using_task_type(tasks, task_type=task_type)

        # If task_category is given then return only specified `user` or `general` job
        if task_category:
            filter_jobs_using_task_category(tasks, task_category=task_category)

        # The following case should never occur. As the general jobs are independent of user. So, if user use such
        # a filter then raise Invalid usage api exception.
        if user_id and task_category == SchedulerUtils.CATEGORY_GENERAL:
            raise InvalidUsage(error_message=
                               "user and task_category cannot be used together. General jobs are independent of users.")

        tasks_count = len(tasks)

        # If page is 1, and per_page is 30 then task_indices will look like list of integers e.g [0-29]
        task_indices = range((page-1) * per_page, page * per_page)

        tasks = [serialize_task(tasks[index], is_admin_api=True)
                 for index in task_indices if index < tasks_count and tasks[index]]

        tasks = [task for task in tasks if task]

        header = {
            'X-Total': tasks_count,
            'X-Per-Page': per_page,
            'X-Page': page
        }
        return ApiResponse(response=dict(tasks=tasks), headers=header)


@api.route(SchedulerApi.SCHEDULER_TASKS_TEST)
class SendRequestTest(Resource):
    """
    POST Method:
        This resource is dummy endpoint which is used to call send_request method for testing
        This dummy endpoint serve two purposes.
        1. To check if endpoint is working then send response 201 (run callback function directly)
        2. To check if authentication token is refreshed after expiry.
        3. Test that scheduler sends GET, POST, DELETE, PUT, PATCH request
    """
    @require_oauth()
    def post(self):
        dummy_request_method(_request=request)

        return dict(message='Dummy POST Endpoint called')

    @require_oauth()
    def put(self):
        dummy_request_method(_request=request)

        return dict(message='Dummy PUT Endpoint called')

    @require_oauth()
    def patch(self):
        dummy_request_method(_request=request)

        return dict(message='Dummy PATCH Endpoint called')

    @require_oauth()
    def delete(self):
        dummy_request_method(_request=request)

        return dict(message='Dummy DELETE Endpoint called')

    @require_oauth()
    def get(self):
        dummy_request_method(_request=request)

        return dict(message='Dummy GET Endpoint called')