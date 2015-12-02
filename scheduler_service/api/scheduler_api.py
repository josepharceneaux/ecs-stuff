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
from scheduler_service.app_utils import api_route, authenticate, JsonResponse
from scheduler_service.common.talent_api import TalentApi
from scheduler_service.common.error_handling import *
from scheduler_service.scheduler import scheduler, schedule_job, serialize_task, remove_tasks
from scheduler_service.custom_exceptions import NoJobFound, PendingStatus, JobAlreadyPaused, \
    JobAlreadyRunning

scheduler_blueprint = Blueprint('scheduling_api', __name__)
api = TalentApi()
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

    @authenticate
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
                            "some_other_kwarg": "abc"
                        },
                        "frequency": "0:00:10",
                        "start_time": "2015-11-05T08:00:00-05:00",
                        "end_time": "2015-12-05T08:00:00-05:00"
                        "next_run_time": "2015-11-05T08:20:30-05:00",
                        "campaign_name": "SMS Campaign"

                    }
               ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        """
        tasks = scheduler.get_jobs()
        tasks = [serialize_task(task) for task in tasks]
        response = json.dumps(dict(tasks=tasks, count=len(tasks)))
        return JsonResponse(response)

    @authenticate
    def post(self, **kwargs):
        """
        This method takes data to create or schedule a task for scheduler.

        :Example:
            task = {
                "frequency": {
                    "day": 5,
                    "hour": 6
                },
                "start_time": "2015-12-05T08:00:00-05:00",
                "end_time": "2016-01-05T08:00:00-05:00",
                "url": "http://getTalent.com/sms/send/",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms"
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
        task = request.get_json(force=True)
        bearer = request.headers.get('Authorization')
        access_token = bearer.lower().replace('bearer ', '')
        task_id = schedule_job(task, 1, access_token)  # kwargs['user_id'])
        headers = {'Location': '/tasks/%s' % task_id}
        response = json.dumps(dict(id=task_id))
        return JsonResponse(response, status=201, headers=headers)

    @authenticate
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
        # get task_ids for tasks to be removed
        req_data = request.get_json(force=True)
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        # check if tasks_ids list is not empty
        if task_ids:
            removed = remove_tasks(task_ids, 1)
            if len(removed) == len(task_ids):
                return JsonResponse(json.dumps(dict(
                    message='%s Tasks removed successfully' % len(removed))),
                    status=200)

            removed_jobs = map(lambda job: job[1], removed)
            not_removed = list(set(task_ids) - set(removed_jobs))
            if not_removed:
                return JsonResponse(json.dumps(dict(message='Unable to remove %s tasks' % len(not_removed),
                                                    removed=removed,
                                                    not_removed=not_removed)), status=207)
        raise InvalidUsage('Bad request, include ids as list data', error_code=400)


@api.route('/tasks/resume/')
class ResumeTasks(Resource):
    """
        This resource resumes a previously paused jobs/tasks
    """

    @authenticate
    def get(self, **kwargs):
        """
        Resume a previously paused tasks/jobs
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            task_ids = {
                'ids': [1,2,3]
            }
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/resume/', headers=headers, data=json.dumps(task_ids))

        .. Response::
            {
               "message":"Tasks has been resumed successfully"
            }

        .. Status:: 200 (OK)
                    6054(Job Already running)
                    500 (Internal Server Error)

        """
        req_data = request.get_json(force=True)
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        for id in task_ids:
            scheduler.resume_job(job_id=id)
        response = json.dumps(dict(message="Tasks has been successfully resumed"))
        return JsonResponse(response)


@api.route('/tasks/pause/')
class PauseTasks(Resource):
    """
        This resource pauses jobs/tasks which can be resumed again
    """

    @authenticate
    def get(self, **kwargs):
        """
        Pause tasks which is currently running.
        :param id: id of task
        :type id: str
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :rtype json

        :Example:
            task_ids = {
                'ids': [1,2,3]
            }
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/tasks/resume/', headers=headers, data=json.dumps(task_ids))

        .. Response::
            {
               "message":"Tasks have been paused successfully"
            }

        .. Status:: 200 (OK)
                    6053(Job already running
                    500 (Internal Server Error)

        """
        req_data = request.get_json(force=True)
        task_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        for id in task_ids:
            # pause the job whether it is paused before or not
            scheduler.pause_job(job_id=id)

        response = json.dumps(dict(message="Tasks have been successfully paused"))
        return JsonResponse(response)


@api.route('/tasks/id/<string:id>')
class TaskById(Resource):
    """
        This resource returns a specific task based on id or update a task
    """

    @authenticate
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
                            "start_time": "2015-11-05T08:00:00-05:00",
                            "end_time": "2015-12-05T08:00:00-05:00"
                            "next_run_time": "2015-11-05T08:20:30-05:00",
                            "timezone": "Asia/Karachi"

                         }
                    }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        """
        job_state_exceptions(job_id=id)
        task = scheduler.get_job(id)
        if task:
            task = serialize_task(task)
            response = json.dumps(dict(task=task))
            return JsonResponse(response)
        return JsonResponse(dict(error=dict(message="Task not found")), 404)

    @authenticate
    def post(self, **kwargs):
        """
        This method takes data to update/reschedules an existing task

        :Example:
            task = {
                "url": "http://getTalent.com/sms/send/",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms"
                },
                "frequency": {
                    "day": 5,
                    "hour": 6
                },
                "start_time": "2015-12-05T08:00:00-05:00",
                "end_time": "2016-01-05T08:00:00-05:00",
                "timezone": "Asia/Karachi"

            }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(task)
            response = requests.post(
                                        API_URL + '/tasks/5das76nbv950nghg8j8-33ddd3kfdw2',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "message" : "Task updated successfully"
            }
        .. Status:: 201 (Resource Created)
                    500 (Internal Server Error)
                    401 (Unauthorized to access getTalent)

        :return: id of created task
        """
        # get json post request data
        task = request.get_json(force=True)
        scheduler.modify_job(id, **task)
        response = json.dumps(dict(message="Task updated successfully"))
        return JsonResponse(response, status=200)

    @authenticate
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
        # user_id = kwargs['user_id']
        task = scheduler.get_job(id)
        if task:
            scheduler.remove_job(task.id)
            response = json.dumps(dict(message="Task has been removed successfully"))
            return JsonResponse(response, 200)

        return JsonResponse(dict(error=dict(message="Task not found")), 404)


@api.route('/tasks/<string:id>/resume/')
class ResumeTaskById(Resource):
    """
        This resource resumes a previously paused job/task
    """

    @authenticate
    def get(self, id, **kwargs):
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
                    6054 (Job Already Running)
                    500 (Internal Server Error)

        """
        # check and raise exception if job is already paused or not present
        job_state_exceptions(job_id=id, func='RUNNING')
        scheduler.resume_job(job_id=id)
        response = json.dumps(dict(message="Task has been successfully resumed"))
        return JsonResponse(response)


@api.route('/tasks/<string:id>/pause/')
class PauseTaskById(Resource):
    """
        This resource pauses job/task which can be resumed again
    """

    @authenticate
    def get(self, id, **kwargs):
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
                    6053 (Job Already Paused)
                    500 (Internal Server Error)

        """
        # check and raise exception if job is already paused or not present
        job_state_exceptions(job_id=id, func='PAUSED')
        scheduler.pause_job(job_id=id)

        response = json.dumps(dict(message="Task has been successfully paused"))
        return JsonResponse(response)


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
        raise NoJobFound("Job with id '%s' not found" % job_id)

    # if job is pending => throw pending state exception
    if job.pending:
        logger.exception("Job with id '%s' is in pending state. Scheduler not running" % job_id)
        raise PendingStatus("Job with id '%s' is in pending state. Scheduler not running" % job_id)

    # if job has next_run_time none, then job is in paused state
    if job.next_run_time is None and func == 'PAUSED':
        logger.exception("Job with id '%s' is already in paused state" % job_id)
        raise JobAlreadyPaused("Job with id '%s' is already in paused state" % job_id)

    # if job has_next_run_time is not None, then job is in running state
    if job.next_run_time is not None and func == 'RUNNING':
        logger.exception("Job with id '%s' is already in running state" % job_id)
        raise JobAlreadyRunning("Job with id '%s' is already in running state" % job_id)

