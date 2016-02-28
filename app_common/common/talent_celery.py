from flask import has_app_context
from sqlalchemy.orm import scoped_session, sessionmaker
from celery import Celery, Task
from talent_config_manager import TalentConfigKeys
from ..common.models.db import db

accept_content = {
    'CELERY_ACCEPT_CONTENT': ['pickle', 'json', 'msgpack', 'yaml']
}


def make_celery(app, default_queue):
    celery = Celery(app.import_name, broker=app.config['REDIS_URL'], backend=app.config['CELERY_RESULT_BACKEND_URL'])
    celery.conf.update(app.config)
    celery.conf.update(accept_content)
    celery.conf.update(default_queue)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            if has_app_context():
                return TaskBase.__call__(self, *args, **kwargs)
            else:
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


class SqlAlchemyTask(Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        environment = db.app.config[TalentConfigKeys.ENV_KEY]
        db.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=db.engine))