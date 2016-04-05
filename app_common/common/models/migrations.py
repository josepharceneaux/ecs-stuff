'''
Package for performing database migrations.
'''

import importlib
import os
from datetime import datetime

from migration import Migration
from ..error_handling import *

DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'

MIGRATIONS_TABLE = 'migration'

def invalid_migration_filename(filename):
    '''
    Expect filenames to be in the form of: 2016-03-15-12-30-10
    '''

    try:
        date_object = datetime.strptime(filename, DATETIME_FORMAT)
    except Exception as e:
        return True

    return False

def run_migrations(logger, db):
    '''
    '''

    service_name = os.path.basename(os.getcwd())
    logger.info("Running migrations for {}".format(service_name))
    migrations_directory = "./migrations"
    if not os.path.isdir(migrations_directory):
        # raise NotFoundError(error_message="No migrations directory found")
        logger.info("No migrations to process (non-existant directory {})".format(migrations_directory))

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
        name = service_name + "/migrations/" + os.path.basename(f)
        result = db.session.query(Migration).filter_by(name=name)
        migrations_found = result.all()
        logger.info("DB Query len: {}".format(len(migrations_found)))
        logger.info("DB Query: {}".format(migrations_found))
        if len(migrations_found) > 1:
            raise UnprocessableEntity(error_message="Multiple records of migration: {}".format(name))

        if len(migrations_found) == 0:
            # Load and run file
            logger.info("Migrating {}".format(f))
            execfile(f)
            logger.info("Recording {}".format(name))
            m = Migration(name=name, run_at_timestamp=datetime.now())
            db.session.add(m)
            db.session.commit()
            migrated_count += 1
        else:
            logger.info("Skipping recorded migration".format(migrations_found[0]))

    logger.info("{} migrations performed".format(migrated_count))

# When run as a script, we have a differrent namespace. Look for all migrations directories
# and run anything found.
if __name__ == "__main__":
    print "Running all migrations from {}".format(os.getcwd())
    # TODO
