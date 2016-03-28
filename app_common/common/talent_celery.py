# Third Party
from flask import Flask
from kombu import Queue
from celery import Celery
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import scoped_session, sessionmaker

# Application Specific
from error_handling import InvalidUsage
from talent_config_manager import TalentConfigKeys

accept_content = {
    'CELERY_ACCEPT_CONTENT': ['pickle', 'json', 'msgpack', 'yaml']
}

CELERY_WORKER_ARGS = ['celery', 'worker', '-Ofair', '--without-gossip', '--without-mingle', '-l', 'info',
                      '--concurrency', '1', '-Q']


def init_celery_app(flask_app, default_queue, modules_to_include=None):
    """
    This initializes Celery app for given Flask app.
    :param flask_app: Flask app
    :param default_queue: Name of queue for particular flask app
    :param modules_to_include: list of modules' names containing Celery tasks
    :type flask_app: Flask
    :type default_queue: str
    :type modules_to_include: list | None
    :return: Celery app
    :rtype: Celery
    """
    if not isinstance(flask_app, Flask):
        raise InvalidUsage('flask_app must be instance of Flask')
    if not isinstance(default_queue, basestring):
        raise InvalidUsage('Queue name must be str')
    if modules_to_include and not isinstance(modules_to_include, list):
        raise InvalidUsage('Include modules containing Celery tasks in a list')
    celery_app = Celery(flask_app.import_name,
                        broker=flask_app.config[TalentConfigKeys.REDIS_URL_KEY],
                        backend=flask_app.config[TalentConfigKeys.CELERY_RESULT_BACKEND_URL],
                        include=modules_to_include)
    flask_app.config['CELERY_QUEUES'] = (
        Queue(default_queue, routing_key=default_queue + '_key'),
    )

    flask_app.config['CELERY_DEFAULT_QUEUE'] = default_queue
    flask_app.config['CELERY_DEFAULT_ROUTING_KEY'] = default_queue + '_key'
    flask_app.config['CELERY_TIMEZONE'] = 'UTC'

    celery_app.conf.update(flask_app.config)
    celery_app.conf.update(accept_content)
    logger = flask_app.config[TalentConfigKeys.LOGGER]
    logger.info("Celery has been configured for %s successfully" % flask_app.import_name)
    return celery_app


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
        self.session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine))()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
