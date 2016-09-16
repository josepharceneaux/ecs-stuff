#!python
# query candidates from getTalent database that belongs jobId
# find them via freshUP,
# update those candidates with the latest data from freshUP
import sys
import argparse
import json, base64, requests, time
from nameparser import HumanName

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
STAGE_CANDIDATE_UPDATE = 'https://candidate-service-staging.gettalent.com/v1/candidates'

# Prod mysql URI prefix
MYSQL_PROD = 'mysql://talent_live:{}@rds-prod.gettalent.com/talent_core'
PROD_CANDIDATE_UPDATE = 'https://candidate-service.gettalent.com/v1/candidates'

def convert_freshup_candidate_to_gt_candidate(freshup_candidate):
    """
    ONLY converts the dict object. Won't put in `id` fields or do anything to the DB.

    :param freshup_candidate: Dice/OpenWeb candidate dict
    :return: getTalent-style Candidate dict
    """

    candidate_object = {}
    if freshup_candidate.get('location'):
        candidate_object['addresses'] = [{
            'address_line_1': None,
            'address_line_2': None,
            'city': freshup_candidate.get('location').get('town'),
            'country': freshup_candidate.get('location').get('country'),
            'is_default': True,
        }]

    if freshup_candidate.get('fullName'):
        name = HumanName(freshup_candidate.get('fullName'))
        candidate_object['first_name'] = name.first or None
        candidate_object['middle_name'] = name.middle or None
        candidate_object['last_name'] = name.last or None

    if freshup_candidate.get('description'):
        candidate_object['summary'] = freshup_candidate.get('description')

    if freshup_candidate.get('experience'):
        experience = []
        if freshup_candidate.get('experience').get('current'):
            company = freshup_candidate.get('experience').get('current').get('company') or ""
            job_title = freshup_candidate.get('experience').get('current').get('jobTitle') or ""
            experience.append({
                'organization': company[:99],
                'position': job_title[:99],
                'is_current': True
            })
        if len(freshup_candidate.get('experience').get('history')):
            for job in freshup_candidate.get('experience').get('history'):
                company = job.get('company') or ""
                job_title = job.get('jobTitle') or ""
                experience.append({
                    'organization': company[:99],
                    'position': job_title[:99]
                })
        candidate_object['work_experiences'] = experience

    if freshup_candidate.get('skills'):
        skills = []
        for skill in freshup_candidate.get('skills'):
            skills.append({'name': skill[:254] if len(skill) > 254 else skill, 'last_used_date': None, 'months_used': None})
        candidate_object['skills'] = skills

    if freshup_candidate.get('socialProfiles'):
        social_networks = []
        for k,v in freshup_candidate.get('socialProfiles').items():
            network = k.replace('.com', '').title()
            if 'Ruby' in network:
                network = 'RubyGems'
            elif 'Wordpress' in network:
                network = 'Wordpress.com'
            social_networks.append({
                'name': network,
                'profile_url': v.get('url')
            })
        candidate_object['social_networks'] = social_networks

    return candidate_object


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="query candidates from getTalent database that belongs to NCI & \
    TERRS\nfind them via freshUP,\nupdate those candidates with the latest data from freshUP")
    parser.add_argument('--stage', nargs=1)
    parser.add_argument('--prod', nargs=1)
    parser.add_argument('--jobid', nargs=1)
    parser.add_argument('--domainId', nargs=1)
    parser.add_argument('--token', nargs=1)
    args = parser.parse_args()

    if not args.token:
        print 'valid token argument is required -token'
        sys.exit(0)

    if not args.jobid:
        print 'freshup jobId is required'
        sys.exit(1)

    if not args.domainId:
        print 'Company domain id is required'
        sys.exit(1)

    if args.prod:
        uri = MYSQL_PROD.format(args.prod[0])
        CANDIDATE_UPDATE_URL = PROD_CANDIDATE_UPDATE
    elif args.stage:
        uri = MYSQL_STAGE.format(args.stage[0])
        CANDIDATE_UPDATE_URL = STAGE_CANDIDATE_UPDATE
    else:
        uri = MYSQL_LOCAL_URI
        CANDIDATE_UPDATE_URL = LOCALHOST_CANDIDATE_UPDATE

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

    # read candidates and put them into dict

    print 'fetching candidates from freshup server ...'
    freshup_job = requests.get(
        url='https://freshup.workdigital.co.uk/api/get.job.json?apiKey=%s&jobId=%s' % (freshup_apikey, args.jobid[0]),
        headers={'Content-Type': 'application/json'})

    if 'status' in freshup_job.text:
        print 'freshup lookup failed: %s' % freshup_job.text
        sys.exit(1)

    lines = freshup_job.text.splitlines()
    print 'Found %d lines in job' % len(lines)
    freshup_candidates = {}
    for line in lines:
        json_line = json.loads(line)
        freshup_candidates[json_line['lookup']['input']['email']] = json_line['lookup']['result']
        name = json_line['lookup']['input']['firstName'].encode('utf-8')+json_line['lookup']['input']['lastName'].encode('utf-8') + json_line['lookup']['input']['phone'].encode('utf-8')
        freshup_candidates[base64.b64encode(name)] = json_line['lookup']['result']

    results = connection.execute('select candidate.id, candidate.FirstName, \
    candidate.LastName, candidate_email.Address, candidate_phone.value from candidate \
    left join candidate_email on candidate_email.candidateId = candidate.id \
    left join candidate_phone on candidate_phone.candidateId = candidate.id \
    where candidate.ownerUserId in (select id from user where domainId=%s)' % args.domainId[0])

    print 'matching candidates from freshup to getTalent ...'
    candidates = []
    for row in results:
        if freshup_candidates.get(row[3]) and row[3]:
            candidate_id = row[0]
            candidate = convert_freshup_candidate_to_gt_candidate(freshup_candidates.get(row[3]))
            candidate['id'] = candidate_id
            candidates.append(candidate)

        elif freshup_candidates.get(base64.b64encode(str(row[1])+str(row[2]) + (str(row[4]) if row[4] else ""))):
            candidate_id = row[0]
            candidate = convert_freshup_candidate_to_gt_candidate(freshup_candidates.get(base64.b64encode(str(row[1])+str(row[2]) + (str(row[4]) if row[4] else ""))))
            candidate['id'] = candidate_id
            candidates.append(candidate)
        else:
            candidate_id = None

    print 'matched and patching %d candidates' % len(candidates)

    for candidate in candidates:
        try:
            r = requests.patch(CANDIDATE_UPDATE_URL,
                json={'candidates': [candidate]},
                headers={'Authorization': 'Bearer %s' % args.token[0], 'Content-Type': 'application/json'}
            )

            if r.status_code == 200:
                print '%d candidate updated!' % candidate.get('id')
            else:
                print "Error patching canddiates:" % r.text
        except Exception as e:
            print 'Exception %s' % e.message
        time.sleep(0.5)
