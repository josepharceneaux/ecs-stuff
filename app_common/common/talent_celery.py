from celery import Celery
from kombu import Queue
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import scoped_session, sessionmaker

accept_content = {
    'CELERY_ACCEPT_CONTENT': ['pickle', 'json', 'msgpack', 'yaml']
}


def make_celery(app, default_queue):
    celery = Celery(app.import_name, broker=app.config['REDIS_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND_URL'])
    app.config['CELERY_QUEUES'] = (
        Queue(default_queue, routing_key=default_queue + '_key'),
    )
    app.config['CELERY_DEFAULT_QUEUE'] = default_queue
    app.config['CELERY_DEFAULT_ROUTING_KEY'] = default_queue + '_key'
    celery.conf.update(app.config)
    celery.conf.update(accept_content)
    return celery


class OneTimeSQLConnection(object):
    """
    In Flask-SQLAlchemy we can not use NullPool Class (https://github.com/mitsuhiko/flask-sqlalchemy/issues/266)
    The default QueuePool pool doesn't allow you to fully close a connection. Calling db.session.close() returns
    the session to the pool with the TCP connection still open and a new transaction started. To avoid this we want
    to use NullPool class which is not supported yet in Flask-SqlAlchemy
    """

    def __init__(self, app):
        self.engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], poolclass=pool.NullPool)

    def __enter__(self):
        self.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


