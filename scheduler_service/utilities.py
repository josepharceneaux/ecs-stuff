from scheduler_service.common.models.scheduler import SchedulerTask

__author__ = 'basit'

# Standard Library


def get_smart_list_ids():
    # TODO: get smart list ids from cloud service maybe
    return [1]


def get_all_tasks():
    tasks = SchedulerTask.query.all()
    return [task.to_json() for task in tasks]


def get_random_word(length):
    """
    This function takes a number as an input and creates a random string of length
    specified by given number.
    :param length: int or long
    :return:
    """
    return ''.join(random.choice(string.lowercase) for i in xrange(length))

