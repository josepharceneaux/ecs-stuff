"""
Scheduler Restful-API which has endpoints to schedule, remove, delete single or multiple jobs
This API also checks for authentication token
"""

import json
import types
from flask import Blueprint, request
from flask.ext.restful import Resource
from flask.ext.cors import CORS
from scheduler_service import logger
from scheduler_service.common.utils.api_utils import api_route, ApiResponse
from scheduler_service.common.talent_api import TalentApi
from scheduler_service.common.error_handling import *
from scheduler_service.common.utils.auth_utils import require_oauth
from scheduler_service.custom_exceptions import JobAlreadyPausedError, PendingJobError, JobAlreadyRunningError, \
    NoJobFoundError
from scheduler_service.scheduler import scheduler, schedule_job, serialize_task, remove_tasks

api = TalentApi()
scheduler_blueprint = Blueprint('scheduling_api', __name__)
api.init_app(scheduler_blueprint)
api.route = types.MethodType(api_route, api)

# Enable CORS
CORS(scheduler_blueprint, resources={
    r'/tasks/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route('/tasks/')
class Tasks(Resource):
    """
        This resource returns a list of tasks or it can be used to create or schedule a task using POST.
    """
    decorators = [require_oauth]

    def get(self, **kwargs):
        """
        This action returns a list of user tasks and their count
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :return tasks_data: a dictionary containing list of tasks and their count
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/', headers=headers)

        .. Response::

            {
                "count": 1,
                "tasks": [
                    {
                        "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                        args: [1,2],
                        "kwargs": {
                            "url": "http://getTalent.com/sms/send/",
                            "phone_number": "09230862348",
                            "smart_list_id": 123456,
                            "content": "text to be sent as sms"
                            "some_other_kwarg": "abc",
                            "campaign_name": "SMS Campaign"
                        },
                        "frequency": "0:00:10",
                        "start_datetime": "2015-11-05T08:00:00-05:00",
                        "end_datetime": "2015-12-05T08:00:00-05:00"
                        "next_run_datetime": "2015-11-05T08:20:30-05:00",
                    }
               ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        """
        auth_user = request.user
        user_id = auth_user.id
        tasks = scheduler.get_jobs()
        tasks = filter(lambda task: task.args[0] == user_id, tasks)
        tasks = [serialize_task(task) for task in tasks]
        response = json.dumps(dict(tasks=tasks, count=len(tasks)))
        return ApiResponse(response)

    def post(self, **kwargs):
        """
        This method takes data to create or schedule a task for scheduler.

        :Example:
            for interval or periodic schedule
            task = {
                "frequency": {
                    "day": 5,
                    "hour": 6
                },
                "trigger": "interval",
                "start_datetime": "2015-12-05T08:00:00-05:00",
                "end_datetime": "2016-01-05T08:00:00-05:00",
                "url": "http://getTalent.com/sms/send/",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms"
                }
            }
            for one-time schedule
            task = {
                "trigger": "date",
                "run_datetime": "2015-12-05T08:00:00-05:00",
                "url": "http://getTalent.com/email/send/",
                "post_data": {
                    "campaign_name": "Email Campaign",
                    "email": "user1@hotmail.com",
                    "smart_list_id": 123456,
                    "content": "content to be sent as email"
                }
            }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(task)
            response = requests.post(
                                        API_URL + '/tasks/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "id" : "5das76nbv950nghg8j8-33ddd3kfdw2"
            }
        .. Status:: 201 (Resource Created)
                    500 (Internal Server Error)
                    401 (Unauthorized to access getTalent)

        :return: id of created task
        """
        # get json post request data
        auth_user = request.user
        user_id = auth_user.id
        task = request.get_json()
        bearer = request.headers.get('Authorization')
        access_token = bearer.lower().replace('bearer ', '')
        task_id = schedule_job(task, user_id, access_token)
        headers = {'Location': '/tasks/%s' % task_id}
        response = json.dumps(dict(id=task_id))
        return ApiResponse(response, status=201, headers=headers)

    def delete(self, **kwargs):
        """
        Deletes multiple tasks whose ids are given in list in request data.
        :param kwargs:
        :return:

        :Example:
            task_ids = {
                'ids': [1,2,3]
            }
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(task_ids)
            response = requests.post(
                                        API_URL + '/tasks/',
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
        auth_user = request.user
        user_id = auth_user.id
        # get task_ids for tasks to be removed
        req_data = request.get_json()
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        # check if tasks_ids list is not empty
        if task_ids:
            removed = remove_tasks(task_ids, user_id=user_id)
            if len(removed) == len(task_ids):
                return ApiResponse(json.dumps(dict(
                    message='%s Tasks removed successfully' % len(removed))),
                    status=200)

            removed_jobs = map(lambda job: job[1], removed)
            not_removed = list(set(task_ids) - set(removed_jobs))
            if not_removed:
                return ApiResponse(json.dumps(dict(message='Unable to remove %s tasks' % len(not_removed),
                                              removed=removed,
                                              not_removed=not_removed)), status=207)
        raise InvalidUsage('Bad request, include ids as list data', error_code=400)


@api.route('/tasks/resume/')
class ResumeTasks(Resource):
    """
        This resource resumes a previously paused jobs/tasks
    """
    decorators = [require_oauth]

    def post(self, **kwargs):
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
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/resume/', headers=headers, data=json.dumps(task_ids))

        .. Response::
            {
               "message":"Tasks has been resumed successfully"
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        .. Error code:: 6053(Job Already running)

        """
        auth_user = request.user
        user_id = auth_user.id
        req_data = request.get_json()
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        none_tasks = filter(lambda task_id: scheduler.get_job(job_id=task_id) == None, task_ids)
        if len(none_tasks):
            raise NoJobFoundError("Job with id %s doesn't exist" % none_tasks)
        task_ids = filter(lambda task_id: scheduler.get_job(job_id=task_id).args[0] == user_id, task_ids)
        for id in task_ids:
            scheduler.resume_job(job_id=id)
        response = json.dumps(dict(message="Tasks has been successfully resumed"))
        return ApiResponse(response)


@api.route('/tasks/pause/')
class PauseTasks(Resource):
    """
        This resource pauses jobs/tasks which can be resumed again
    """
    decorators = [require_oauth]

    def post(self, **kwargs):
        """
        Pause tasks which is currently running.
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            task_ids = {
                'ids': [fasdff12n22m2jnr5n6skf,ascv3h5k1j43k6k8k32k345jmn,123n23n4n43m2kkcj53vdsxc]
            }
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/resume/', headers=headers, data=json.dumps(task_ids))

        .. Response::
            {
               "message":"Tasks have been paused successfully"
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        .. Error code:: 6054(Job Already running)

        """
        auth_user = request.user
        user_id = auth_user.id
        req_data = request.get_json()
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        none_tasks = filter(lambda task_id: scheduler.get_job(job_id=task_id) == None, task_ids)
        if len(none_tasks):
            raise NoJobFoundError("Job with id %s doesn't exist" % none_tasks)
        task_ids = filter(lambda task_id: scheduler.get_job(job_id=task_id).args[0] == user_id, task_ids)
        for id in task_ids:
            # pause the job whether it is paused before or not
            scheduler.pause_job(job_id=id)

        response = json.dumps(dict(message="Tasks have been successfully paused"))
        return ApiResponse(response)


@api.route('/tasks/id/<string:id>')
class TaskById(Resource):
    """
        This resource returns a specific task based on id or update a task
    """
    decorators = [require_oauth]

    def get(self, id, **kwargs):
        """
        This action returns a task owned by a this user
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :return task: a dictionary containing a task data
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

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
                            "frequency": {
                                "days": 0,
                                "seconds": 10
                            }
                            "start_datetime": "2015-11-05T08:00:00-05:00",
                            "end_datetime": "2015-12-05T08:00:00-05:00"
                            "next_run_datetime": "2015-11-05T08:20:30-05:00",
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
                            "run_datetime": "2015-11-05T08:00:00-05:00",
                         }
                    }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        """
        auth_user = request.user
        user_id = auth_user.id
        task = scheduler.get_job(id)
        if task and task.args[0] == user_id:
            task = serialize_task(task)
            response = json.dumps(dict(task=task))
            return ApiResponse(response)
        return ApiResponse(dict(error=dict(message="Task not found")), 404)

    def delete(self, id, **kwargs):
        """
        Deletes/removes a tasks from scheduler store
        :param kwargs:
        :return:

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            response = requests.delete(
                                        API_URL + '/tasks/5das76nbv950nghg8j8-33ddd3kfdw2',
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Task has been removed successfully'
            }
        .. Status:: 200 (Resource deleted)
                    404 (Not found)
                    500 (Internal Server Error)

        """
        auth_user = request.user
        user_id = auth_user.id
        task = scheduler.get_job(id)
        if task and task.args[0] == user_id:
            scheduler.remove_job(task.id)
            response = json.dumps(dict(message="Task has been removed successfully"))
            return ApiResponse(response, 200)

        return ApiResponse(dict(error=dict(message="Task not found")), 404)


@api.route('/tasks/<string:id>/resume/')
class ResumeTaskById(Resource):
    """
        This resource resumes a previously paused job/task
    """
    decorators = [require_oauth]

    def post(self, id, **kwargs):
        """
        Resume a previously paused task/job
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/5das76nbv950nghg8j8-33ddd3kfdw2/resume/', headers=headers)

        .. Response::
            {
               "message":"Task has been resumed successfully"
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        .. Error code:: 6054(Job Already running)

        """
        auth_user = request.user
        user_id = auth_user.id
        # check and raise exception if job is already paused or not present
        job_state_exceptions(job_id=id, func='RUNNING')
        task = scheduler.get_job(id)
        if task and task.args[0] == user_id:
            scheduler.resume_job(job_id=id)
            response = json.dumps(dict(message="Task has been successfully resumed"))
            return ApiResponse(response)
        return ApiResponse(dict(error=dict(message="Task not found")), 404)


@api.route('/tasks/<string:id>/pause/')
class PauseTaskById(Resource):
    """
        This resource pauses job/task which can be resumed again
    """
    decorators = [require_oauth]

    def post(self, id, **kwargs):
        """
        Pause a task which is currently running.
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/5das76nbv950nghg8j8-33ddd3kfdw2/resume/', headers=headers)

        .. Response::
            {
               "message":"Task has been paused successfully"
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        .. Error code:: 6053(Job Already Paused)

        """
        # check and raise exception if job is already paused or not present
        auth_user = request.user
        user_id = auth_user.id
        job_state_exceptions(job_id=id, func='PAUSED')
        task = scheduler.get_job(id)
        if task and task.args[0] == user_id:
            scheduler.pause_job(job_id=id)
            response = json.dumps(dict(message="Task has been successfully paused"))
            return ApiResponse(response)
        return ApiResponse(dict(error=dict(message="Task not found")), 404)


def job_state_exceptions(job_id=None, func='GET'):
    """
    raise exception if condition matched
    :param job_id: job_id of task which is in apscheduler
    :param func: the state to check, if doesn't meet with requirement then raise exception
    :return:
    """
    # get job from scheduler by job_id
    job = scheduler.get_job(job_id=job_id)

    # if job is None => throw job not found exception
    if job is None:
        logger.exception("Job with id '%s' not found" % job_id)
        raise NoJobFoundError("Job with id '%s' not found" % job_id)

    # if job is pending => throw pending state exception
    if job.pending:
        logger.exception("Job with id '%s' is in pending state. Scheduler not running" % job_id)
        raise PendingJobError("Job with id '%s' is in pending state. Scheduler not running" % job_id)

    # if job has next_run_datetime none, then job is in paused state
    if job.next_run_time is None and func == 'PAUSED':
        logger.exception("Job with id '%s' is already in paused state" % job_id)
        raise JobAlreadyPausedError("Job with id '%s' is already in paused state" % job_id)

    # if job has_next_run_datetime is not None, then job is in running state
    if job.next_run_time is not None and func == 'RUNNING':
        logger.exception("Job with id '%s' is already in running state" % job_id)
        raise JobAlreadyRunningError("Job with id '%s' is already in running state" % job_id)

