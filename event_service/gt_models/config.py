import os
import logging
import logging.config
import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def set_up():
    file_path = os.path.realpath(__file__)
    dir_path, _ = os.path.split(file_path)
    PATH = os.path.abspath(os.path.join(dir_path, '../'))
    cfg_path = os.path.normpath(PATH + "/app.cfg")
    logfile = os.path.normpath(PATH + "/logging.conf")
    logging.config.fileConfig(logfile)
    config = ConfigParser.ConfigParser()
    config.read(cfg_path)
    environment = config.get('local', 'env')
    if environment == 'prod':
        DB_CONN = 'mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core'
        logger = logging.getLogger("event_service.app.prod")
    elif environment == 'qa':
        DB_CONN = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
        logger = logging.getLogger("event_service.app.qa")
    else:
        DB_CONN = 'mysql://talent_web:s!loc976892@localhost/talent_local'
        logger = logging.getLogger("event_service.app.dev")

    engine = create_engine(DB_CONN, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    return db_session, engine

Base = declarative_base()
db_session, engine = set_up()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import organization
    import culture
    import candidate
    import domain
    import user
    import social_network
    import rsvp
    import event
    import activity
    Base.metadata.create_all(bind=engine)
