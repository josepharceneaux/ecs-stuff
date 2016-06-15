"""
The file contains helper methods for scheduler admin API. Which are used to apply filters on list of tasks
returned by APScheduler
"""
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from scheduler_service import SchedulerUtils
from scheduler_service.common.error_handling import InvalidUsage


def filter_paused_jobs(tasks, is_paused):
    """
    Filter paused jobs only from tasks list
    :param tasks: APScheduler tasks
    :type tasks: list
    :param is_paused: If `true` or `1`, then filter only paused jobs. If its false, filter running jobs.
    :type is_paused: object (bool, str, int)
    :return: Returns the paused or not running tasks in a list depending upon is_paused arg
    """
    if not str(is_paused).lower() in ['true', 'false', '1', '0']:
        raise InvalidUsage("paused should be of type bool or int. If `true` or `1`, paused jobs will be "
                           "returned and if `false` or `0`, then returns only running jobs")
    if str(is_paused).lower() in ["true", "1"]:
        tasks = filter(lambda _task: _task.next_run_time is None,
                       tasks)
    else:
        tasks = filter(lambda _task: _task.next_run_time, tasks)

    return tasks


def filter_jobs_using_task_type(tasks, task_type):
    """
    Filters jobs based on task_type
    :param tasks: APScheduler tasks
    :type tasks: list
    :param task_type: `periodic` or `one_time`
    :type task_type: str
    :return: Returns the periodic or one_time tasks in a list depending upon task_type arg
    """
    if not (isinstance(task_type, basestring) and task_type.lower() in [SchedulerUtils.ONE_TIME.lower(),
                                                                        SchedulerUtils.PERIODIC.lower()]):
        raise InvalidUsage("task_type should be of type string with value of `{0}` or `{1}`"
                           .format(SchedulerUtils.ONE_TIME, SchedulerUtils.PERIODIC))
    if task_type.lower() == SchedulerUtils.PERIODIC.lower():
        tasks = filter(lambda _task: isinstance(_task.trigger, IntervalTrigger), tasks)
    else:
        tasks = filter(lambda _task: isinstance(_task.trigger, DateTrigger), tasks)

    return tasks


def filter_jobs_using_task_category(tasks, task_category):
    """
    Filters jobs based on task_type
    :param tasks: APScheduler tasks
    :type tasks: list
    :param task_category: `user` or `general`
    :type task_category: str
    :return: Returns the user or general tasks in a list depending upon task_category
    """
    if not (isinstance(task_category, basestring) and task_category.lower() in
            [SchedulerUtils.CATEGORY_USER.lower(), SchedulerUtils.CATEGORY_GENERAL.lower()]):
        raise InvalidUsage("task_category should be of type string with value of "
                           "`{0}` or `{1}`".format(SchedulerUtils.CATEGORY_USER, SchedulerUtils.CATEGORY_GENERAL))

    if task_category.lower() == SchedulerUtils.CATEGORY_GENERAL.lower():
        tasks = filter(lambda _task: _task.name, tasks)
    else:
        tasks = filter(lambda _task: _task.name == SchedulerUtils.RUN_JOB_METHOD_NAME, tasks)

    return tasks
