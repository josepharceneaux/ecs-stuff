'''
Package for performing database migrations.

Files located in the 'migrations' directory under each micro service may contain database migration code. The files must be named in
the format: YYYY-MM-DD-HH-MM-SS  So, for example, 2016-04-19-14-13-00

Files are run in order, according to the timestamp represented by the file name, and then recorded in the database so that the same
file is not run again. The name format recorded is: <service-name>/<filename> so migrations are scoped by service name.
'''

import importlib
import os
from datetime import datetime

from migration import Migration
from ..error_handling import *

# Format of a migration filename
DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'

# Name of the migrations directory
MIGRATIONS_DIRECTORY = 'migrations'

def invalid_migration_filename(filename):
    '''
    We expect migration filenames to be in the form of: 2016-03-15-12-30-10
    Validate whether they are or not.

    :param filename: The filename to be validated.
    :return: True or False
    '''

    try:
        date_object = datetime.strptime(filename, DATETIME_FORMAT)
    except Exception as e:
        return True

    return False

def run_migrations(logger, db):
    '''
    Run the database migration files in the MIGRATIONS directory of a service.

    :param logger: The logger object for the system.
    :param db: The SQLAlchemy database object.
    :return: None or raises an exception
    '''

    service_name = os.path.basename(os.getcwd())
    logger.info("Running migrations for {}".format(service_name))
    migrations_directory = "./" + MIGRATIONS_DIRECTORY
    if not os.path.isdir(migrations_directory):
        # raise NotFoundError(error_message="No migrations directory found")
        logger.info("No migrations to process (non-existant directory {})".format(migrations_directory))
        return

    # Ensure that all migration files appear valid before using them
    files = []
    for f in os.listdir(migrations_directory):
        pathname = "{}/{}".format(migrations_directory, f)
        if not os.path.isfile(pathname):
            raise UnprocessableEntity(error_message="Unexpected non-file found: {}".format(pathname))
        if invalid_migration_filename(f):
            raise UnprocessableEntity(error_message="Incorrect migration filename: {}".format(f))

        files.append(pathname)

    if len(files) == 0:
        logger.info("No migrations to process.")
        return

    # Now sort the files, and if not recorded in the DB, run the file and record it
    files.sort()
    migrated_count = 0
    for f in files:
        name = service_name + "/" + MIGRATIONS_DIRECTORY + "/" + os.path.basename(f)

        migrations_found = []
        # Check manually for the table - some exceptions are not caught
        if Migration.__tablename__ in db.engine.table_names():
            try:
                migrations_found = db.session.query(Migration).filter(Migration.name == name).all()
            except Exception as e:
                logger.error("DB Query Exception: {}".format(e.message))
        else:
            Migration.__table__.create(db.engine)

        if len(migrations_found) == 0:
            # Load and run file
            logger.info("Migrating {}".format(f))
            try:
                execfile(f)
            except Exception as e:
                raise UnprocessableEntity(error_message="Can't execute migration: {}".format(f))

            # Record migration processed
            logger.info("Recording {}".format(name))
            m = Migration(name=name)
            db.session.add(m)
            db.session.commit()
            migrated_count += 1
        else:
            # Since we expect our timestamp-inspired naming convention to be unique, we should never find more than one
            if len(migrations_found) > 1:
                logger.error("Multiple records for migration: ".format(migrations_found[0].name))
            logger.info("Skipping recorded migration".format(migrations_found[0].name))

    logger.info("{} migrations performed".format(migrated_count))

# When run as a script, we have a differrent namespace. Look for all migrations directories
# and run anything found.
if __name__ == "__main__":
    print "Running all migrations from {}".format(os.getcwd())
    # TODO
