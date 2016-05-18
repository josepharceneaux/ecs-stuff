"""
Test cases for Talent Cloud Search functionality
"""
import time
from candidate_service.common.tests.conftest import *
from candidate_service.common.models.candidate import CandidateStatus
from candidate_service.candidate_app import db, logger
from candidate_service.modules.talent_cloud_search import search_candidates, upload_candidate_documents
from candidate_service.common.models.misc import AreaOfInterest
from candidate_service.common.models.talent_pools_pipelines import TalentPool
from candidate_service.common.utils.talent_areas_of_interest import KAISER_PARENT_TO_CHILD_AOIS
from candidate_service.common.tests.fake_testing_data_generator import college_majors
from faker import Faker
from nameparser import HumanName
# Common utilities
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

fake = Faker()

# Various U.S. locations in (city, state, zipcode) format, which can be used to populate candidate locations
VARIOUS_US_LOCATIONS = (('San Jose', 'CA', '95132'), ('Providence', 'Rhode Island', '02905'),
                        ('Lubbock', 'Texas', '79452'), ('Philadelphia', 'Pennsylvania', '19184'),
                        ('Delray Beach', 'Florida', '33448'), ('Houston', 'Texas', '77080'),
                        ('Boston', 'Massachusetts', '02163'), ('Fairbanks', 'Alaska', '99709'),
                        ('Los Angeles', 'California', '90087'), ('Clearwater', 'Florida', '34615'),
                        ('Seattle', 'Washington', '98158'))


def populate_candidates(access_token, talent_pool, count=1, first_name=None, middle_name=None,
                        last_name=None, added_datetime=None, objective=None, company_name=None, job_title=None,
                        city=None, state=None, zip_code=None, areas_of_interest=None, school_name=None,
                        major=None, degree_type=None, degree_title=None, military_branch=None,
                        military_status=None, military_grade=None, military_to_date=None,
                        military_from_date=None, skills=None, experiences=None):
    """
    Function will create candidate(s) by making a POST request to /v1/candidates
     All fields are populated unless if specified via function-params
    :param  access_token:        required | user's access token for authentication
    :type   access_token:        str
    :param  talent_pool:         required | user's talent pool
    :type   talent_pool:         TalentPool
    :param  count:               optional | number of candidates that will be created
    :type   count:               int | long
    :param  first_name:          optional | candidate's first name
    :type   first_name:          str
    :param  middle_name:         optional | candidate's middle name
    :type   middle_name:         str
    :param  last_name:           optional | candidate's last name
    :type   last_name:           str
    :param  added_datetime:      optional | candidate's creation datetime
    :param  objective:           optional | candidate's objective
    :type   objective:           str
    :param  company_name:        optional | candidate's employer's name
    :type   company_name:        str
    :param  job_title:           optional | candidate's job title
    :type   job_title:           str
    :param  city:                optional | candidate's city of resident
    :type   city:                str
    :param  state:               optional | candidate's state of resident
    :type   state:               str
    :param  zip_code:            optional | candidate's zipcode of resident
    :type   zip_code:            str
    :param  areas_of_interest:   optional | candidate's areas of interest
    :type   areas_of_interest:   list[dict]
    :param  school_name:         optional | candidate's school/college/university name
    :type   school_name:         str
    :param  major:               optional | candidate's major, e.g. Mechanical Engineering
    :type   major:               str
    :param  degree_type:         optional | e.g. Bachelors, Masters, Doctorate
    :type   degree_type:         str
    :param  degree_title:        optional | e.g. Bachelor of Fine Arts
    :type   degree_title:        str
    :param  military_branch:     optional | e.g. Marine Corps, Coast Guard
    :type   military_branch:     str
    :param  military_status:     optional | e.g. Active, Inactive
    :type   military_status:     str
    :param  military_grade:      optional | e.g. Private, Sergeant, Major
    :type   military_grade:      str
    :param  military_to_date:    optional | end date of military service, e.g. 2012-07-15
    :type   military_to_date:    str
    :param  military_from_date:  optional | start date of military service, e.g. 2008-07-15
    :type   military_from_date:  str
    :param  skills:              optional | candidate's skills
    :type   skills:              list[dict]
    :param  experiences:         optional | candidate's work experiences
    :type   experiences:         list[dict]
    :return:                     {'candidates': [{'id': int}, {'id': int}, ...]}
    :rtype:                      list[dict]
    """
    candidate_ids = []
    for i in range(count):
        full_name = fake.name()
        parsed_full_name = HumanName(full_name)
        discipline = random.choice(college_majors().keys())
        data = dict(candidates=[dict(
            talent_pool_ids=dict(
                add=[talent_pool.id]
            ),
            added_datetime=added_datetime,
            first_name=first_name or parsed_full_name.first,
            middle_name=middle_name or parsed_full_name.middle,
            last_name=last_name or parsed_full_name.last,
            objective=objective or fake.bs(),
            emails=[dict(
                address=fake.safe_email()
            )],
            addresses=[dict(
                address_line_1=fake.street_address(),
                city=city or fake.city(),
                state=state or fake.state(),
                country_code=fake.country_code(),
                zip_code=zip_code or fake.zipcode()
            )],
            phones=[dict(  # TODO: use international phone number
                value='+14058769932'
            )],
            educations=[dict(
                school_name=school_name or fake.first_name() + ' University',
                city=fake.city(),
                state=fake.state(),
                degrees=[dict(
                    title=degree_title or random.choice(college_majors()[discipline]),
                    type=degree_type or random.choice(["Associate", "Bachelors", "Masters", "Doctoral"]),
                    start_year=random.choice([year for year in range(1980, 2010)]),
                    gpa=round(random.randint(2, 3) + random.random(), 2),
                    bullets=[dict(
                        major=major or discipline,
                    )]
                )]
            )],
            work_experiences=experiences or [dict(
                position=job_title or fake.job(),
                organization=company_name or fake.company()
            )],
            military_services=[dict(
                branch=military_branch or fake.word(),
                status=military_status or 'Active',
                highest_grade=military_grade or None,
                from_date=military_from_date or None,
                to_date=military_to_date or None,
                comments=fake.bs()
            )],
            skills=skills or [dict(
                name=random.choice(['SQL', 'Excel', 'UNIX', 'Testing', 'Payroll', 'Finance', 'Sales', 'Accounting']),
                months_used=random.randint(10, 120)
            )],
            areas_of_interest=areas_of_interest
        )])

        # Send POST request to /v1/candidates
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token, data)
        print response_info(create_resp)
        candidate_ids.append(create_resp.json()['candidates'][0]['id'])

    return candidate_ids


# TODO: Use polling instead of time.sleep()
def _assert_search_results(domain_id, search_vars, candidate_ids, wait=True,
                           check_for_equality=False, check_for_sorting=False, facets_dict=None):
    # sometimes when asserting same uploaded candidates in a domain with several different queries,
    # it's not worth waiting
    # so don't sleep as cloud_search is already updated
    if wait:
        time.sleep(30)  # Wait for cloud_search to update

    response = search_candidates(domain_id=domain_id, request_vars=search_vars)
    resultant_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]

    # Test whether every element in the set candidate_ids is in resultant_candidate_ids.
    assert set(candidate_ids).issubset(resultant_candidate_ids)
    if check_for_equality:
        assert set(candidate_ids) == set(resultant_candidate_ids)
    if check_for_sorting:
        # i.e. the candidates in search results should appear in same order as of candidate_ids
        # compare as list so it will check for index as well as element.
        # If using check for sorting no need to check for equality because number of candidates is also checked here.
        assert candidate_ids == resultant_candidate_ids
    if facets_dict:
        # If facets_dict is present, compare provided facets_dict with facets returned from cloudsearch
        assert compare_dictionaries(response['search_data']['facets'], facets_dict)


def create_area_of_interest_facets(db, domain_id):
    """
    Create area of interest (aoi) facets in domain
    :param db:
    :param domain_id:
    :return: list of created area of interest ids
    """
    all_aoi_ids = []
    for parent_aoi_name, child_aoi_names in KAISER_PARENT_TO_CHILD_AOIS.items():
        # Insert parent AOI if doesn't exist
        existing_parent_aoi = AreaOfInterest.query.filter(AreaOfInterest.domain_id == domain_id,
                                                          AreaOfInterest.name == parent_aoi_name).first()
        if existing_parent_aoi:
            parent_aoi_id = existing_parent_aoi.id
        else:
            parent_aoi = AreaOfInterest(domain_id=domain_id, name=parent_aoi_name)
            db.session.add(parent_aoi)
            db.session.commit()
            parent_aoi_id = parent_aoi.id
        all_aoi_ids.append(parent_aoi_id)

        # Insert child AOIs if doesn't exist
        for child_aoi_name in child_aoi_names:
            existing_child_aoi = AreaOfInterest.query.filter(AreaOfInterest.domain_id == domain_id,
                                                             AreaOfInterest.name == child_aoi_name,
                                                             AreaOfInterest.parent_id == parent_aoi_id).first()
            if existing_child_aoi:
                child_aoi_id = existing_child_aoi.id
            else:
                child_aoi = AreaOfInterest(domain_id=domain_id, name=child_aoi_name, parent_id=parent_aoi_id)
                db.session.add(child_aoi)
                db.session.commit()
                child_aoi_id = child_aoi.id
            all_aoi_ids.append(child_aoi_id)
    db.session.commit()
    return all_aoi_ids


def get_or_create_status(db, status_name):
    """
    Creates status with given status_name if not exists, else return id of status
    :param db:
    :param status_name:
    :return: id of given status_name
    """

    status_obj = db.session.query(CandidateStatus).filter_by(description=status_name).first()
    if status_obj:
        return status_obj.id
    else:  # create one with given name
        print "Status: %s, not present in database, creating a new one" % status_name
        add_status = CandidateStatus(description=status_name, otes="Candidate is %s" % status_name.lower())
        db.session.add(add_status)
        db.session.commit()
        return add_status


def compare_dictionaries(dict1, dict2):
    """
    Match two dictionaries.
    :param dict1:
    :param dict2:
    :return: True if matched. False if not matched and print unmatched key/value
    """

    cmp_value = cmp(dict1, dict2)
    if cmp_value != 0:
        if cmp_value < 0:
            # d2 is greater, swap values so as to compare missing keys
            dict1, dict2 = dict2, dict1
        for key, value in dict1.iteritems():
            try:
                dict2_value = dict2[key]
            except KeyError:
                print "%s not in other" % key
                continue
            if value != dict2_value:
                print "One has %s:%s second has %s:%s" % (key, value, key, dict2_value)
        return False
    return True
