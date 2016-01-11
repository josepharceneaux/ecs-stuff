"""
Scheduler Restful-API which has endpoints to schedule, remove, delete, pause, resume single
or multiple jobs.
This API also checks for authentication token
"""

# Standard imports
import json
import types

# Third party imports
from datetime import timedelta, datetime
from flask import Blueprint, request
from flask.ext.restful import Resource
from flask.ext.cors import CORS

# Application imports
from werkzeug.exceptions import BadRequest

from scheduler_service import TalentConfigKeys, flask_app
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.utils.api_utils import api_route, ApiResponse
from scheduler_service.common.talent_api import TalentApi
from scheduler_service.common.error_handling import InvalidUsage, ResourceNotFound, ForbiddenError
from scheduler_service.common.utils.auth_utils import require_oauth
from scheduler_service.custom_exceptions import JobAlreadyPausedError, PendingJobError, JobAlreadyRunningError, \
    SchedulerNotRunningError, SchedulerServiceApiException
from scheduler_service.scheduler import scheduler, schedule_job, serialize_task, remove_tasks, run_job

api = TalentApi()
scheduler_blueprint = Blueprint('scheduler_api', __name__)
api.init_app(scheduler_blueprint)
api.route = types.MethodType(api_route, api)

# Enable CORS
CORS(scheduler_blueprint, resources={
    SchedulerApiUrl.SCHEDULER_MULTIPLE_TASKS + '*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route(SchedulerApiUrl.SCHEDULER_MULTIPLE_TASKS)
class Tasks(Resource):
    """
        This resource returns a list of tasks or it can be used to create or schedule a task using POST.
    """
    @require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
    def get(self, **kwargs):
        """
        This action returns a list of user tasks and their count
        :keyword user_id: user_id of tasks' owner
        :type user_id: int
        :return tasks_data: a dictionary containing list of tasks and their count
        :rtype json

        :Example:
        In case of authenticated user

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/v1//tasks/', headers=headers)

        In case of SECRET_KEY

            headers = {'Authorization': 'Basic <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.get(API_URL + '/v1//tasks/', headers=headers)

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
                    500 (Internal Server Error)

        """
        user_id = request.user.id if request.user else None
        check_if_scheduler_is_running()
        tasks = scheduler.get_jobs()
        tasks = filter(lambda task: task.args[0] == user_id, tasks)
        tasks = [serialize_task(task) for task in tasks]
        tasks = [task for task in tasks if task]
        return dict(tasks=tasks, count=len(tasks))

    @require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
    def post(self, **kwargs):
        """
        This method takes data to create or schedule a task for scheduler.

        :Example:
            for interval or periodic schedule
            task = {
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

            headers = {'Authorization': 'Basic <access_token>',
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
        check_if_scheduler_is_running()
        try:
            task = request.get_json()
        except Exception:
            raise InvalidUsage("Bad Request, data should be in json")

        task_id = schedule_job(task, request.user.id if request.user else None, request.oauth_token)

        headers = {'Location': '/v1/tasks/%s' % task_id}
        response = json.dumps(dict(id=task_id))
        return ApiResponse(response, status=201, headers=headers)

    @require_oauth()
    def delete(self, **kwargs):
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
        check_if_scheduler_is_running()
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
            return dict(
                message='%s Tasks removed successfully' % len(removed))

        # removed_jobs have valid jobs - filters in remove_tasks
        # job[1] contains job id
        removed_jobs = map(lambda job: job[1], removed)
        not_removed = list(set(task_ids) - set(removed_jobs))
        if not_removed:
            return dict(message='Unable to remove %s tasks' % len(not_removed),
                        removed=removed,
                        not_removed=not_removed), 207


@api.route(SchedulerApiUrl.SCHEDULER_MULTIPLE_TASK_RESUME)
class ResumeTasks(Resource):
    """
        This resource resumes a previously paused jobs/tasks
    """
    decorators = [require_oauth()]

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
        check_if_scheduler_is_running()
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


@api.route(SchedulerApiUrl.SCHEDULER_MULTIPLE_TASK_PAUSE)
class PauseTasks(Resource):
    """
        This resource pauses jobs/tasks which can be resumed again
    """
    decorators = [require_oauth()]

    def post(self, **kwargs):
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
        check_if_scheduler_is_running()
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


@api.route(SchedulerApiUrl.SCHEDULER_ONE_TASK)
class TaskById(Resource):
    """
        This resource returns a specific task based on id or update a task
    """

    @require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
    def get(self, _id, **kwargs):
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
            response = requests.get(API_URL + '/v1//tasks/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

        In case of SECRET_KEY

            headers = {'Authorization': 'Basic <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.get(API_URL + '/v1//tasks/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

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
        check_if_scheduler_is_running()
        task = scheduler.get_job(_id)
        # Make sure task is valid and belongs to logged-in user
        if task and task.args[0] == user_id:
            task = serialize_task(task)
            if task:
                return dict(task=task)
        raise ResourceNotFound(error_message="Task not found")

    @require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
    def delete(self, _id, **kwargs):
        """
        Deletes/removes a tasks from scheduler store
        :param kwargs:
        :return:

        :Example:
         In case of authenticated user

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.delete(API_URL + '/v1//tasks/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)

        In case of SECRET_KEY

            headers = {'Authorization': 'Basic <access_token>',
                        'X-Talent-Server-Key-ID': '<secret_key>'}
            response = requests.delete(API_URL + '/v1//tasks/5das76nbv950nghg8j8-33ddd3kfdw2', headers=headers)


        .. Response::

            {
                'message': 'Task has been removed successfully'
            }
        .. Status:: 200 (Resource deleted)
                    404 (Task Not found)
                    500 (Internal Server Error)

        """
        user_id = request.user.id if request.user else None
        check_if_scheduler_is_running()
        task = scheduler.get_job(_id)
        # Check if task is valid and belongs to the logged-in user
        if task and task.args[0] == user_id:
            scheduler.remove_job(task.id)
            return dict(message="Task has been removed successfully")
        raise ResourceNotFound(error_message="Task not found")


@api.route(SchedulerApiUrl.SCHEDULER_SINGLE_TASK_RESUME)
class ResumeTaskById(Resource):
    """
        This resource resumes a previously paused job/task
    """
    decorators = [require_oauth()]

    def post(self, _id, **kwargs):
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
        check_if_scheduler_is_running()
        # check and raise exception if job is already paused or not present
        task = check_job_state(job_id=_id, job_state_to_check='running')
        if task and task.args[0] == user_id:
            scheduler.resume_job(job_id=_id)
            return dict(message="Task has been successfully resumed")
        raise ResourceNotFound(error_message="Task not found")


@api.route(SchedulerApiUrl.SCHEDULER_SINGLE_TASK_PAUSE)
class PauseTaskById(Resource):
    """
        This resource pauses job/task which can be resumed again
    """
    decorators = [require_oauth()]

    def post(self, _id, **kwargs):
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
        check_if_scheduler_is_running()
        task = check_job_state(job_id=_id, job_state_to_check='paused')
        if task and task.args[0] == user_id:
            scheduler.pause_job(job_id=_id)
            return dict(message="Task has been successfully paused")
        raise ResourceNotFound(error_message="Task not found")


@api.route(SchedulerApiUrl.SCHEDULER_TASKS_TEST)
class SendRequestTest(Resource):
    """
        This resource is dummy endpoint which is used to call send_request method for testing
        This dummy endpoint serve two purposes.
        1. To check if endpoint is working then send response 201 (run callback function directly)
        2. To check if authentication token is refreshed after expiry.
    """
    decorators = [require_oauth()]

    def post(self):

        key = flask_app.config.get(TalentConfigKeys.ENV_KEY)
        if not (key == 'dev' or key == 'circle'):
            raise ForbiddenError("You are not authorized to access this endpoint.")

        user_id = request.user.id
        try:
            task = request.get_json()
        except BadRequest:
            raise InvalidUsage('Given data is not JSON serializable')

        # Post data param expired. If yes, then expire the token
        expired = task.get('expired', False)

        url = task.get('url', '')

        if expired:
            # Set the date in past to expire request oauth token.
            # This is to test that run_job method refresh token or not
            expiry = datetime.utcnow() - timedelta(days=5)
            expiry = expiry.strftime('%Y-%m-%d %H:%M:%S')

            # Expire oauth token and then pass it to run_job. And run_job should refresh token and send request to URL
            db.db.session.commit()
            token = Token.query.filter_by(user_id=request.user.id).first()
            token.update(expires=expiry)

        run_job(user_id, request.oauth_token, url, task.get('content_type', 'application/json'),
                kwargs=task.get('post_data', dict()))

        return dict(message="Request sent to url %s" % url)


def check_if_scheduler_is_running():
    # if scheduler is not running
    if not scheduler.running:
        raise SchedulerNotRunningError("Scheduler is not running")


def check_job_state(job_id, job_state_to_check):
    """
    We retrieve a job and if it's pending we raise an error. If job_state_to_check
    is 'paused' and job's next_run_time is None then we raise an error indicating job
    is already in paused state. Likewise, if job_state_to_check is 'running' and
    next_run_time is not None then we raise an error indicating job is already running.
    :param job_id: job_id of task which is in APScheduler
    :param job_state_to_check: the state to check, if doesn't meet requirement then raise exception.
            'func' can be 'running' or 'paused'.
    :return:
    """
    # get job from scheduler by job_id
    job = scheduler.get_job(job_id=job_id)

    # if job is pending then throw pending state exception
    if job.pending:
        raise PendingJobError("Task with id '%s' is in pending state. Scheduler not running" % job_id)

    # if job has next_run_datetime none, then job is in paused state
    if not job.next_run_time and job_state_to_check == 'paused':
        raise JobAlreadyPausedError("Task with id '%s' is already in paused state" % job_id)

    # if job has_next_run_datetime is not None, then job is in running state
    if job.next_run_time and job_state_to_check == 'running':
        raise JobAlreadyRunningError("Task with id '%s' is already in running state" % job_id)

    return job
