from celery import Celery

accept_content = {
    'CELERY_ACCEPT_CONTENT': ['pickle', 'json', 'msgpack', 'yaml']
}


def make_celery(app, default_queue):
    celery = Celery(app.import_name, broker=app.config['REDIS_URL'], backend=app.config['CELERY_RESULT_BACKEND_URL'])
    celery.conf.update(app.config)
    celery.conf.update(accept_content)
    celery.conf.update(default_queue)
    return celery