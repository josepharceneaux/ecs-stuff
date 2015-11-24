from scheduler_service.common.models.scheduler import SchedulerTask

__author__ = 'basit'

# Standard Library


def get_smart_list_ids():
    # TODO: get smart list ids from cloud service maybe
    return [1]


def get_all_tasks():
    tasks = SchedulerTask.query.all()
    return [task.to_json() for task in tasks]

