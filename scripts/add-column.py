# Add a column to DB tables

# The DB name is specified in the URI. The tables and the column name and type are specified in constants below

import sys

from sqlalchemy import *
from sqlalchemy.sql import select

# Localhost mysql URI
MYSQL_LOCAL_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'

# Stage URI - alter when used
MYSQL_STAGE_URI = 'mysql://talent_web:'

# Prod URI - alter when used
MYSQL_PROD_URI = 'mysql://talent_web:'

TABLES = [ 'candidate_address', 'candidate_education', 'candidate_experience', 'candidate_preferred_location', 'candidate_military_service' ]

COLUMN = 'iso3166_country'

TYPE = 'varchar(2)'

if __name__ == "__main__":

    uri = MYSQL_LOCAL_URI
    print "Connecting to", uri, "...",
    sys.stdout.flush()
    try:
        engine = create_engine(uri)
        connection = engine.connect()
    except Exception as e:
        print
        print "Can't connect: ", e.message
        sys.exit(1)

    print "Connected"

    for table in TABLES:
        query = 'alter table {} add {} {}'.format(table, COLUMN, TYPE)
        try:
            print "   ", query
            results = connection.execute(query)
        except Exception as e:
            print
            print "Execution exception: ", e.message
            sys.exit(1)

    print "Completed"
    connection.close()
    sys.exit(0)
