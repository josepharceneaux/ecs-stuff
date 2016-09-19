import sys
import argparse
import csv

from sqlalchemy import *
from sqlalchemy.sql import select
from logo import logo

logo()
freshup_apikey = 'c41ed83dbec4c061827ecdc1c8565bce9f8feb63'

# Localhost
MYSQL_LOCAL_URI = 'mysql://root:@localhost/talent_local'
LOCALHOST_CANDIDATE_UPDATE = 'http://127.0.0.1:8005/v1/candidates'

# MYSQL_STAGE = 'mysql://talent_web:{}@rds-staging.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_staging'
MYSQL_STAGE = 'mysql://talent_web:{}@stage-db.gettalent.com/talent_staging'

# Prod mysql URI prefix
MYSQL_PROD = 'mysql://talent_live:{}@rds-prod.gettalent.com/talent_core'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="query candidates from getTalent database that belongs to NCI & \
    TERRS\nfind them via freshUP,\nupdate those candidates with the latest data from freshUP")
    parser.add_argument('--stage', nargs=1)
    parser.add_argument('--prod', nargs=1)
    parser.add_argument('--domainId', nargs=1)
    args = parser.parse_args()

    if args.prod:
        uri = MYSQL_PROD.format(args.prod[0])
    elif args.stage:
        uri = MYSQL_STAGE.format(args.stage[0])
    else:
        uri = MYSQL_LOCAL_URI

    print "Connecting to", uri, "...\n",
    sys.stdout.flush()
    try:
        engine = create_engine(uri)
        connection = engine.connect()
    except Exception as e:
        print "\n"
        print "Can't connect: ", e.message
        sys.exit(1)

    print "Connected"
    connection.execute("SET sql_mode = ''")
    result = connection.execute("select candidate.id, candidate.FirstName, \
    candidate.LastName, candidate_email.Address, candidate_phone.value, candidate_address.City, \
    candidate_address.State, candidate_address.ZipCode, candidate_address.AddressLine1\
    from candidate \
    left join candidate_email on candidate_email.candidateId = candidate.id \
    left join candidate_phone on candidate_phone.candidateId = candidate.id \
    left join candidate_address on candidate_address.candidateId = candidate.id \
    where candidate.ownerUserId in (select id from user where user.domainId=%s) group by candidate_email.Address" % args.domainId[0])

    with open('domain-%s.csv' % args.domainId[0], 'w') as csvfile:
        w = csv.writer(csvfile)
        w.writerow(['refId', 'firstname', 'lastname', 'email', 'address', 'city', 'country', 'phone', 'zip'])
        for row in result:
            w.writerow([row[0], row[1], row[2], row[3], row[8], row[5], '', row[4], row[7]])

    #just_comment
