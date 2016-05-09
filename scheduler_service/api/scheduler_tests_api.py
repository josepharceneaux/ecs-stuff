from datetime import datetime, timedelta
from werkzeug.exceptions import BadRequest

from scheduler_service import flask_app, TalentConfigKeys, redis_store, logger
from scheduler_service.common.error_handling import ForbiddenError, InvalidUsage
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token, User
from scheduler_service.common.talent_config_manager import TalentEnvs
from scheduler_service.custom_exceptions import SchedulerNotRunningError, PendingJobError, JobAlreadyPausedError, \
    JobAlreadyRunningError
from scheduler_service.modules.CONSTANTS import REQUEST_COUNTER
from scheduler_service.modules.scheduler import run_job, scheduler


def test_dummy_endpoint_hits(_request):
    # Increment the count in redis whenever this endpoint hits
    request_counter_key = REQUEST_COUNTER % (_request.method.lower())

    # Add a counter key in redis to check how many times this dummy endpoint is called
    if redis_store.exists(request_counter_key):
        redis_store.set(request_counter_key, int(redis_store.get(request_counter_key))+1)
    else:
        redis_store.set(request_counter_key, 1)


def dummy_request_method(_request):
    """
    Dummy endpoint to test GET, POST, DELETE request using celery
    :param _request:
    :return:
    """
    env_key = flask_app.config.get(TalentConfigKeys.ENV_KEY)
    if not (env_key == TalentEnvs.DEV or env_key == TalentEnvs.JENKINS):
        raise ForbiddenError("You are not authorized to access this endpoint.")

    user_id = _request.user.id
    try:
        task = _request.get_json()
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
        token = Token.query.filter_by(user_id=_request.user.id).first()
        token.update(expires=expiry)
        run_job(user_id, _request.oauth_token, url, task.get('content-type', 'application/json'),
                task.get('post_data', dict()))
    else:
        try:
            # Try deleting the user if exist
            db.db.session.commit()
            test_user_id = task['test_user_id']
            test_user = User.query.filter_by(id=test_user_id).first()
            test_user.delete()
        except Exception as e:
            logger.exception(e.message)


def raise_if_scheduler_not_running():
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