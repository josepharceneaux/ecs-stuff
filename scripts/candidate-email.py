"""
"""

import sys
import argparse

from sqlalchemy import *
from sqlalchemy.sql import select
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Modify import path to include current directory
sys.path[0] = '.'
# When run on production, remove app_common.
from app_common.common.models.candidate import Candidate
from app_common.common.models.user import User


# Localhost mysql URI
MYSQL_LOCAL_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'

# Staging mysql URI prefix
# MYSQL_STAGE = 'mysql://talent_web:{}@rds-staging.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_staging'
MYSQL_STAGE = 'mysql://talent_web:{}@stage-db.gettalent.com/talent_staging'

# Prod mysql URI prefix
MYSQL_PROD = 'mysql://talent_live:{}@rds-prod.gettalent.com/talent_core'

# Talent Pool Candidates table
CANDIDATES_NAME = 'talent_pool_candidate'

# Talent Pool table
TALENT_POOL_NAME = 'talent_pool'

# Pool ID Column
POOL_ID_NAME = 'talent_pool_id'

if __name__ == "__main__":
    uri = MYSQL_LOCAL_URI

    print "Connecting to", uri, "...",
    sys.stdout.flush()
    try:
        engine = create_engine(uri)
        connection = engine.connect()
        db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    except Exception as e:
        print
        print "Can't connect: ", e.message
        sys.exit(1)

    print "Connected."

    candidate = Candidate.get_by_id(18)
    print "C: {}".format(candidate)

    sys.exit(0)
