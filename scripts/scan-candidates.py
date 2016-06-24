# Check data consistency of candidates and their talent pools

# TODO: How to connect to staging / prod since there's an ssh tunnel
# Current convention is to run this on the bastion host

import sys
import argparse

from sqlalchemy import *
from sqlalchemy.sql import select

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

    parser = argparse.ArgumentParser(description="Scan database for inconsistencies between candidates and talent pools.\nSupply password if --stage or --prod.")
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
    except Exception as e:
        print
        print "Can't connect: ", e.message
        sys.exit(1)

    print "Connected"

    # Gather all unique talent_pool_candidate ids into a set
    results = connection.execute('select * from talent_pool_candidate')
    talent_pools_with_candidates = set()
    talent_pool_candidates = []
    talent_pool_candidate_ids = set()
    for row in results:
        talent_pool_candidates.append(row.id)
        talent_pools_with_candidates.add(row.talent_pool_id)
        talent_pool_candidate_ids.add(row.candidate_id)

    # Gather all talent pool ids into a set
    results = connection.execute('select * from talent_pool')
    talent_pools = set()
    for row in results:
        talent_pools.add(row.id)

    # Gather all candidate ids into a set
    results = connection.execute('select * from candidate')
    candidate_ids = set()
    for row in results:
        candidate_ids.add(row.Id)

    if len(talent_pool_candidates) != len(candidate_ids):
        print "Missing Candidates:"
        print "    Talent Pool Candidate Count: ", len(talent_pool_candidates)
        print "                Candidate Count: ", len(candidate_ids)
        print

    # Scan candidates for invalid talent pool ids
    print "Checking invalid candidate talent pools..."
    count = 0
    for talent_pool_id in talent_pools_with_candidates:
        if talent_pool_id not in talent_pools:
            print "    Bad talent pool id ", talent_pool_id, " for candidate ", talent_pool_id
            count += 1
    if count == 0:
        print "    None invalid."
    print

    # Scan for candidates with no talent_pools
    print "Checking for candidates with no talent pool..."
    count = 0
    for candidate in candidate_ids:
        if candidate not in talent_pool_candidate_ids:
            count += 1
    print "    ", count, "candidates with empty or invalid talent pool."

    connection.close()
    sys.exit(0)
