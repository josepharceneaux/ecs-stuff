import os
import logging
import logging.config
import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class GTSQLAlchemy(object):
    """
    This class will be used to initialize SQLAlchemy. Both app_config
    and logging_config paths should be specified, this way apps can configure
    SQLAlchemy to use their own respective app_config and logging_config.

    So in order to define new modules one can create a python file under
    gt_common/gt_models e.g. gt_common/gt_models/entity.py.

    In your starting point of the app, you will instantiate it e.g.

    gt_sqlalchemy = GTSQLAlchemy(app_config_path='/user/gettalent/app.cfg',
        logging_config_path='/user/gettalent/logging.conf',
        logger_name='event_service.app.prod')

    and then one can define use this in models e.g.

        class Entity(GTSQLAlchemy.Base):
            pass
    """
    # Static property
    BASE = declarative_base()
    db_session = None

    def __init__(self, *args, **kwargs):
        self.app_config_path = kwargs.get('app_config_path')
        self.logging_config_path = kwargs.get('logging_config_path')
        self.db_conn = None
        self.logger_name = kwargs.get('logger_name')
        self.logger = None
        self.engine = None
        self.convert_unicode = kwargs.get('convert_unicode', True)
        self.auto_commit = kwargs.get('auto_commit', False)
        self.auto_flush = kwargs.get('auto_flush', False)

        self.setup(self.app_config_path, self.logging_config_path)

    def setup(self, app_config_path, logging_config_path):
        app_config_path = os.path.normpath(app_config_path)
        logging_config_path = os.path.normpath(logging_config_path)
        logging.config.fileConfig(logging_config_path)
        config = ConfigParser.ConfigParser()
        config.read(app_config_path)
        environment = config.get('local', 'env')
        if environment == 'prod':
            db_conn_str = 'mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core'
            # logger = logging.getLogger("event_service.app.prod")
            logger = logging.getLogger(self.logger_name)
        elif environment == 'qa':
            db_conn_str = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
            logger = logging.getLogger(self.logger_name)
        else:
            db_conn_str = 'mysql://talent_web:s!loc976892@localhost/talent_local'
            logger = logging.getLogger(self.logger_name)
        self.engine = create_engine(db_conn_str, convert_unicode=self.convert_unicode)

        GTSQLAlchemy.db_session = scoped_session(sessionmaker(autocommit=self.auto_commit,
                                             autoflush=self.auto_flush,
                                             bind=self.engine))
        self.create_all()

    def create_all(self):
        import candidate
        import event
        import user
        import domain
        import organization
        import culture
        import rsvp
        import activity
        import candidate
        import event
        import client
        import social_network
        import token
        GTSQLAlchemy.BASE.metadata.create_all(bind=self.engine)

# def set_up(app_config_path, logging_conf_path):
#     global DB_CONN
#     global logger
#     #ile_path = os.path.realpath(__file__)
#     #ir_path, _ = os.path.split(file_path)
#     #ATH = os.path.abspath(os.path.join(dir_path, '../'))
#     cfg_path = os.path.normpath(app_config_path)
#     logfile = os.path.normpath(logging_conf_path)
#     logging.config.fileConfig(logfile)
#     config = ConfigParser.ConfigParser()
#     config.read(cfg_path)
#     environment = config.get('local', 'env')
#     if environment == 'prod':
#         DB_CONN = 'mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core'
#         logger = logging.getLogger("event_service.app.prod")
#     elif environment == 'qa':
#         DB_CONN = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
#         logger = logging.getLogger("event_service.app.qa")
#     else:
#         DB_CONN = 'mysql://talent_web:s!loc976892@localhost/talent_local'
#         logger = logging.getLogger("event_service.app.dev")
#
# print 'DB_Conn', DB_CONN
# engine = create_engine(DB_CONN, convert_unicode=True)
# db_session = scoped_session(sessionmaker(autocommit=False,
#                                              autoflush=False,
#                                              bind=engine))
# Base = declarative_base()
# db_session, engine = set_up()
# Base.query = db_session.query_property()
#
# def init_db():
#     # import all modules here that might define models so that
#     # they will be registered properly on the metadata.  Otherwise
#     # you will have to import them first before calling init_db()
#     import organization
#     import culture
#     import candidate
#     import domain
#     import user
#     import social_network
#     import rsvp
#     import event
#     import activity
#     import client
#     import token
#     Base.metadata.create_all(bind=engine)
