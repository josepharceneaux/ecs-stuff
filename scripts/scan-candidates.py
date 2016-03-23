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
MYSQL_STAGE = 'mysql://talent_web:{}@devdb.gettalent.com/talent_staging'

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
    candidate_talent_pools = set()
    talent_pool_candidates = []
    talent_pool_candidate_ids = set()
    for row in results:
        talent_pool_candidates.append(row.id)
        candidate_talent_pools.add(row.talent_pool_id)
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
    for candidate in candidate_talent_pools:
        if candidate not in talent_pools:
            print "    Bad talent pool id ", id, " for candidate ", candidate
            count += 1
    if count == 0:
        print "    None invalid."
    print

    # Scan talent pools to see if it's not present in the candidate set
    print "Checking empty talent pools:"
    empty_pools = []
    for pool in talent_pools:
        if pool not in candidate_talent_pools:
            # print "    No candidates in pool ", pool
            empty_pools.append(pool)
    print "    ", len(empty_pools), " empty talent pools."
    print

    # Scan for candidates with no talent_pools
    print "Checking for candidates with no talent pool..."
    count = 0
    for talent_pool_candidate in candidate_ids:
        if talent_pool_candidate not in talent_pool_candidate_ids:
            count += 1
    print "    ", count, " candidates without talent pool."

    connection.close()
    sys.exit(0)
