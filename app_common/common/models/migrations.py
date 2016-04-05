'''
Package for performing database migrations.
'''

import importlib
import os
from datetime import datetime

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

    current_directory = os.getcwd()
    logger.info("Running migrations for {}".format(current_directory))
    migrations_directory = current_directory + "/migrations"

    if not os.path.isdir(migrations_directory):
        # raise NotFoundError(error_message="No migrations directory found")
        logger.info("No migrations to process (non-existant directory {})".format(current_directory))

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

    # Now lets's get a list of migrations already run and cull the list of them
    # try:
    #     results = db.engine.execute('select * from talent_pool_candidate')
    #     logger.info("query results: {}".format(results))
    # except Exception as e:
    #     logger.error("DB Exception: {}".format(e.message))
    # logger.info("Table Names:")

    if MIGRATIONS_TABLE not in db.engine.table_names():
        logger.info("Creating migrations table")
    else:
        logger.info("Migrations table exists")

    # Now we have a list of files not in the DB - run them in order and then record them
    files.sort()
    for f in files:
        # Load and run file
        logger.info("Migrating {}".format(f))
        execfile(f)
        # Record file in DB

    logger.info("{} migrations completed".format(len(files)))

# When run as a script, we have a differrent namespace. Look for all migrations directories
# and run anything found.
if __name__ == "__main__":
    print "Running all migrations from {}".format(os.getcwd())
    # TODO
