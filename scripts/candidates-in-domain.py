"""
Scan database for number of candidates each domain.
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
from common.models.candidate import Candidate
from common.models.user import User


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

    parser = argparse.ArgumentParser(description="Scan database for number of candidates each domain.\nSupply password if --stage or --prod.")
    parser.add_argument('--stage', nargs=1)
    parser.add_argument('--prod', nargs=1)
    args = parser.parse_args()

    if args.prod:
        uri = MYSQL_PROD.format(args.prod[0])
    elif args.stage:
        uri = MYSQL_STAGE.format(args.stage[0])
    else:
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

    zero_count = 0
    total_count = 0
    domain_list = connection.execute('select id, Name from domain')
    for row in domain_list:
        # print "Domain: {}".format(row.Name)
        total_count += 1
        domain_id = row.id
        candidate_list = db_session.query(Candidate).join(User).filter(User.domain_id == domain_id).all()
        count = len(candidate_list)
        if count == 0:
            zero_count += 1
        # print "    {} candidates".format(count)

    print "{} Domains".format(total_count)
    print "{} Empty".format(zero_count)

    # print "Searching domain {}".format(domain_id)
    # candidate_list = db_session.query(Candidate).join(User).filter(User.domain_id == domain_id).all()
    # for candidate in candidate_list:
    #     exist = db_session.query(Candidate).join(User).filter(Candidate.id == candidate.id).filter(User.domain_id == domain_id).first()
    #     if exist:
    #         print "id: {} domain: {}".format(candidate.id, domain_id)
    #     else:
    #         print "id: {} not in {}".format(candidate.id, domain_id)

    sys.exit(0)
