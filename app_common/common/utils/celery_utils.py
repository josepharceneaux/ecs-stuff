# Third Party
from flask import Flask
from celery import Celery

# Application Specific
from ..error_handling import InvalidUsage
from ..talent_config_manager import TalentConfigKeys

__author__ = 'basit'


def init_celery_app(flask_app, queue_name, modules_to_include):
    """
    This initializes Celery app for given flask app.
    :param flask_app: Flask app
    :param queue_name: Name of queue for particular flask app
    :param modules_to_include: list of modules' names containing Celery tasks
    :type flask_app: Flask
    :type queue_name: str
    :type modules_to_include: list
    :return:
    """
    if not isinstance(flask_app, Flask):
        raise InvalidUsage('flask_app must be instance of Flask')
    if not isinstance(queue_name, basestring):
        raise InvalidUsage('Queue name must be str')
    if not isinstance(modules_to_include, list):
        raise InvalidUsage('Include modules containing Celery tasks in a list')
    # Celery settings
    default_queue = {'CELERY_DEFAULT_QUEUE': queue_name}
    default_serializer = {'CELERY_RESULT_SERIALIZER': 'json'}
    resultant_db_tables = {
        'CELERY_RESULT_DB_TABLENAMES': {
            'task': queue_name + '_taskmeta',
            'group': queue_name + '_groupmeta'
        }
    }
    accept_content = {
        'CELERY_ACCEPT_CONTENT': ['pickle', 'json', 'msgpack', 'yaml']
    }
    # Initialize Celery app
    celery_app = Celery(flask_app,
                        broker=flask_app.config[TalentConfigKeys.REDIS_URL_KEY],
                        backend=flask_app.config[TalentConfigKeys.CELERY_RESULT_BACKEND_URL],
                        include=modules_to_include)

    celery_app.conf.update(default_queue)
    celery_app.conf.update(resultant_db_tables)
    celery_app.conf.update(default_serializer)
    celery_app.conf.update(accept_content)
    TaskBase = celery_app.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery_app.Task = ContextTask
    return celery_app
