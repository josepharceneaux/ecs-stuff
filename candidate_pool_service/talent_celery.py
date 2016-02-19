from celery import Celery

accept_content = {
    'CELERY_ACCEPT_CONTENT': ['pickle', 'json', 'msgpack', 'yaml']
}

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['REDIS_URL'], backend=app.config['CELERY_RESULT_BACKEND_URL'])
    celery.conf.update(app.config)
    celery.conf.update(accept_content)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery