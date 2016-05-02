"""
Test cases for candidate-search-service-API
"""
from candidate_service.tests.modules.test_talent_cloud_search import (
    populate_candidates, VARIOUS_US_LOCATIONS, create_area_of_interest_facets
)
from candidate_service.cloudsearch_constants import SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH
from ..modules.test_talent_cloud_search import _assert_search_results
from candidate_service.common.tests.conftest import *
from candidate_service.common.models.candidate import Candidate, CandidateSource, CandidateAddress
from candidate_service.modules.talent_cloud_search import upload_candidate_documents
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.geo_services.geo_coordinates import get_geocoordinates_bounding
from candidate_service.common.utils.datetime_utils import DatetimeUtils
from helpers import AddUserRoles
from polling import poll
# Standard libraries
import datetime
import uuid
import time
import requests
from dateutil.parser import parse


class TestCandidateSearchGet(object):
    @staticmethod
    def create_candidates(access_token, user, talent_pool):
        AddUserRoles.add(user=user)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}},
            {'talent_pool_ids': {'add': [talent_pool.id]}},
            {'talent_pool_ids': {'add': [talent_pool.id]}},
        ]}
        resp = requests.post(
            url=CandidateApiUrl.CANDIDATES,
            headers={'Authorization': 'Bearer {}'.format(access_token),
                     'content-type': 'application/json'},
            data=json.dumps(data))
        print response_info(response=resp)
        assert resp.status_code == 201
        return resp

    def test_get_candidates_via_list_of_ids(self, access_token_first, user_first, talent_pool):
        # Create candidates for user
        create_resp = self.create_candidates(access_token_first, user_first, talent_pool).json()
        # Retrieve candidates
        AddUserRoles.get(user_first)
        data = {'candidate_ids': [candidate['id'] for candidate in create_resp['candidates']]}
        resp = send_request('get', CandidateApiUrl.CANDIDATE_SEARCH_URI, access_token_first, data)
        # resp = request_to_candidate_search_resource(access_token_first, 'get', data)
        print response_info(resp)
        assert resp.status_code == 200
        assert len(resp.json()['candidates']) == 3  # Number of candidate IDs sent in
        assert resp.json()['candidates'][0]['talent_pool_ids'][0] == talent_pool.id
        assert resp.json()['candidates'][0]['id'] == data['candidate_ids'][0]


def test_search_all_candidates_in_domain(user_first, access_token_first, talent_pool):
    """
    Test to search all candidates under the same domain
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=5)
    response = get_response(access_token_first, '', len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_location(user_first, access_token_first, talent_pool):
    """
    Test to search candidates using location
    """
    AddUserRoles.add_and_get(user_first)
    city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                        city=city, state=state, zip_code=zip_code)
    response = get_response(access_token_first, '?location=%s,%s' % (city, state), expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_user_ids(user_first, access_token_first, talent_pool):
    """
    Test to search all candidates under the user
    """
    AddUserRoles.add_and_get(user_first)
    user_id = user_first.id
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=5)
    response = get_response(access_token_first, '?user_ids={}'.format(user_id), expected_count=len(candidate_ids))
    print response_info(response)
    _assert_results(candidate_ids, response.json())


def test_search_skills(user_first, access_token_first, talent_pool):
    """
    Test to search all candidates based on skills
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
                                        skills=[{'name': 'hadoop', 'months_used': 36}])

    response = get_response(access_token_first, '?skills=hadoop', expected_count=len(candidate_ids))
    print response_info(response)
    _assert_results(candidate_ids, response.json())


def test_search_aoi(user_first, access_token_first, talent_pool):
    """
    Test to search all candidates based on area_of_interest
    """
    AddUserRoles.add_and_get(user=user_first)
    all_aoi_ids = create_area_of_interest_facets(db, user_first.domain_id)
    number_of_aois = len(all_aoi_ids)
    aoi_ids_list = all_aoi_ids[0:5]
    areas_of_interest = [dict(area_of_interest_id=aoi_id) for aoi_id in aoi_ids_list]
    candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
                                        count=5, areas_of_interest=areas_of_interest)
    response = get_response(access_token_first, '?area_of_interest_ids={}'.format(aoi_ids_list[1]),
                            expected_count=len(candidate_ids))
    print response_info(response)
    _assert_results(candidate_ids, response.json())


def test_search_candidate_experience(user_first, access_token_first, talent_pool):
    """Test to search candidates with experience"""
    AddUserRoles.add_and_get(user_first)
    experience_2_years = [{'organization': 'Intel', 'position': 'Research analyst', 'start_year': 2013,
                           'start_month': 06, 'end_year': 2015, 'end_month': 06}]
    experience_0_years = [{'organization': 'Audi', 'position': 'Mechanic', 'start_year': 2015,
                           'start_month': 01, 'end_year': 2015, 'end_month': 02, 'is_current': True}]
    candidate_ids = []
    candidate_with_0_years_exp = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
                                                     count=3, experiences=experience_0_years)
    for candidate_id in candidate_with_0_years_exp:
        db.session.query(Candidate).filter_by(id=candidate_id).update(dict(total_months_experience=2))
        db.session.flush()
        candidate_ids.append(candidate_id)
    candidate_with_2_years_exp = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
                                                     count=3, experiences=experience_2_years)
    for candidate_id in candidate_with_2_years_exp:
        db.session.query(Candidate).filter_by(id=candidate_id).update(dict(total_months_experience=24))
        db.session.commit()
        candidate_ids.append(candidate_id)
    # Update cloud_search
    upload_candidate_documents.delay(candidate_ids)
    response = get_response(access_token_first, '?minimum_years_experience=0&maximum_years_experience=2', 1).json()
    for candidate in response['candidates']:
        start_date_at_current_job = candidate.get('start_date_at_current_job', '')
        if start_date_at_current_job:
            start_date_at_current_job = parse(start_date_at_current_job)
            assert start_date_at_current_job.month == 1
            assert start_date_at_current_job.year == 2015

    _assert_results(candidate_ids, response)


def test_search_position(user_first, access_token_first, talent_pool):
    """Test to search candidates by job_title/position"""
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=4,
                                        job_title="Developer")
    response = get_response(access_token_first, '?job_title=Developer', expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_degree(user_first, access_token_first, talent_pool):
    """Test to search candidates by degree type"""
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                        degree_type="Masters")
    response = get_response(access_token_first, '?degree_type=Masters', expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_school_name(user_first, access_token_first, talent_pool):
    """Test to search candidates by university/school_name"""
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                        school_name='Oklahoma State University')
    response = get_response(access_token_first, '?school_name=Oklahoma State University',
                            expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_concentration(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by higher education
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
                                        count=4, major='Post Graduate')
    response = get_response(access_token_first, '?major=Post Graduate', expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_military_service_status(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by military service status
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                        military_status="Retired")
    response = get_response(access_token_first, '?military_service_status=Retired', expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_military_branch(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by military branch
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                        military_branch="Army")
    response = get_response(access_token_first, '?military_branch=Army', expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_military_highest_grade(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by military highest grade
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                        military_grade="W-1")
    response = get_response(access_token_first, '?military_highest_grade=W-1', expected_count=len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_military_date_of_separation(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by military date of separation
    """
    AddUserRoles.add_and_get(user_first)

    candidates_today = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=5,
                                           military_to_date=str(datetime.datetime.utcnow().date()))

    candidates_2014 = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
                                          military_to_date='2014-04-26')

    candidates_2012 = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=2,
                                          military_to_date='2012-07-15')

    test1_candidate_ids = candidates_2014 + candidates_today

    response1 = get_response(access_token_first, '?military_end_date_from=2013', len(test1_candidate_ids))
    _assert_results(test1_candidate_ids, response1.json())

    test2_candidate_ids = candidates_2012 + candidates_2014 + candidates_today
    response2 = get_response(access_token_first, '?military_end_date_from=2010', len(test2_candidate_ids))
    _assert_results(test2_candidate_ids, response2.json())

    test3_candidate_ids = candidates_2012 + candidates_2014
    response3 = get_response(access_token_first,
                             '?military_end_date_from=2010&military_end_date_to=2014', len(test3_candidate_ids))
    _assert_results(test3_candidate_ids, response3.json())

    test4_candidate_ids = candidates_2012
    response4 = get_response(access_token_first, '?military_end_date_to=2012', len(test4_candidate_ids))
    _assert_results(test4_candidate_ids, response4.json())

    test5_candidate_ids = candidates_2012 + candidates_2014
    response5 = get_response(access_token_first, '?military_end_date_to=2014', len(test5_candidate_ids))
    _assert_results(test5_candidate_ids, response5.json())


def test_search_query_with_name(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by passing query argument
    For example, search by querying first_name
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
                                        count=5, first_name=fake.first_name(), last_name=fake.last_name())
    response = get_response(access_token_first, '?q=Naveen', len(candidate_ids))
    _assert_results(candidate_ids, response.json())


def test_search_get_only_requested_fields(user_first, access_token_first, talent_pool):
    """
    Test to search candidates and get only requested fields like email,source_id,etc,..
    """
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=2)
    response = get_response(access_token_first, '?fields=email', len(candidate_ids))
    resultant_keys = response.json()['candidates'][0].keys()
    assert len(resultant_keys) == 1
    assert 'email' in resultant_keys


def test_search_paging(user_first, access_token_first, talent_pool):
    AddUserRoles.add_and_get(user_first)
    candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=50)
    response = get_response(access_token_first, '?sort_by=~recent', 15)
    print response_info(response)
    resultant_candidate_ids = [long(candidate['id']) for candidate in response.json()['candidates']]
    assert set(candidate_ids[:15]).issubset(resultant_candidate_ids)


def test_search_by_first_name(user_first, access_token_first, talent_pool):
    """
    Test search candidates by first name
    """
    AddUserRoles.add_and_get(user_first)
    first_name = 'Marilyn'
    # Create candidate with first name and last name
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, first_name=first_name)
    resp = get_response(access_token_first, '?{}'.format(first_name), len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def test_search_by_last_name(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by last name
    """
    AddUserRoles.add_and_get(user_first)
    last_name = 'Lynn'
    # Create candidate with last name
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, last_name=last_name)
    resp = get_response(access_token_first, '?{}'.format(last_name), len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def test_search_by_current_company(talent_pool, access_token_first, user_first):
    """
    Test to search candidates by current company
    """
    AddUserRoles.add_and_get(user_first)
    company_name = "Google"
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=5,
                                        company_name=company_name)
    resp = get_response(access_token_first, '?{}'.format(company_name), len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def test_search_by_position_facet(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by position
    """
    AddUserRoles.add_and_get(user_first)
    current_title = "Senior Developer"
    candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
                                        count=12, job_title=current_title)
    resp = get_response(access_token_first, '?job_title={}'.format(current_title), len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def test_search_by_position_and_company(user_first, access_token_first, talent_pool):
    """
    Test to search candidates by position and company
    """
    AddUserRoles.add_and_get(user_first)
    company, position = "Apple", "CEO"
    # 10 other candidates at apple
    populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=10, company_name=company)
    ceo_at_apple = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
                                       count=1, company_name=company, job_title=position)
    # Search for company Apple and position CEO, it should only return 1 candidate although Apple has 10 other employees
    resp = get_response(access_token_first, '?organization={}&job_title={}'.format(company, position),
                        len(ceo_at_apple))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(ceo_at_apple).issubset(resultant_candidate_ids)


def test_search_by_university(user_first, access_token_first, talent_pool):
    """
    university > school_name
    """
    AddUserRoles.add_and_get(user_first)
    university1, university2 = 'University Of Washington', 'Oklahoma State University'
    university1_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
                                                 school_name=university1)
    # Create other candidates with other university, check
    university2_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
                                                 school_name=university2)
    total_candidates = university1_candidates + university2_candidates

    resp = get_response(access_token_first, '?school_name={}'.format(university1), len(university1_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(university1_candidates).issubset(resultant_candidate_ids)

    resp = get_response(access_token_first, '?school_name={}'.format(university2), len(university2_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(university2_candidates).issubset(resultant_candidate_ids)


def test_search_by_location(user_first, talent_pool, access_token_first):
    """
    Search by City name, State name
    """
    AddUserRoles.add_and_get(user_first)
    city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
    candidate_ids = populate_candidates(count=2, access_token=access_token_first, talent_pool=talent_pool, city=city,
                                        state=state, zip_code=zip_code)

    # With zipcode only
    resp = get_response(access_token_first, '?zipcode={}'.format(zip_code), len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)

    # With city and state only
    resp = get_response(access_token_first, '?city={}&state={}'.format(city, state), len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)

    # With city, state and zip
    resp = get_response(access_token_first, '?city={}&state={}&zipcode={}'.format(city, state, zip_code),
                        len(candidate_ids))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def test_search_by_major(user_first, access_token_first, talent_pool):
    """
    Test to search based on major facet
    Without university major doesn't gets created in database, So university should also be created for major
    """
    AddUserRoles.add_and_get(user_first)
    major1, major2 = 'Electrical Engineering', 'Computer Science'
    major1_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
                                            major=major1)
    major2_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=7,
                                            major=major2)

    resp = get_response(access_token_first, '?major={}'.format(major1), len(major1_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(major1_candidates).issubset(resultant_candidate_ids)

    resp = get_response(access_token_first, '?major={}'.format(major2), len(major2_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(major2_candidates).issubset(resultant_candidate_ids)


def test_search_by_degree(user_first, access_token_first, talent_pool):
    """
    Search by degree
    """
    AddUserRoles.add_and_get(user_first)
    degree1, degree2 = 'Masters', 'Bachelors'
    master_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
                                            degree_type=degree1)
    bachelor_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
                                              degree_type=degree2)
    all_candidates = master_candidates + bachelor_candidates

    # Search for candidates with Masters
    resp = get_response(access_token_first, '?degree_type={}'.format(degree1), len(master_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(master_candidates).issubset(resultant_candidate_ids)

    # Search for candidates with Bachelors
    resp = get_response(access_token_first, '?degree_type={}'.format(degree2), len(bachelor_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(bachelor_candidates).issubset(resultant_candidate_ids)

    # Search for candidates with any degree types
    resp = get_response(access_token_first, '?degree_type={},{}'.format(degree1, degree2), len(all_candidates))
    print response_info(resp)
    resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
    assert set(all_candidates).issubset(resultant_candidate_ids)


# TODO: fix flaky test - Amir
# def test_location_with_radius(user_first, access_token_first, talent_pool):
#     """
#     Search by city, state + radius
#     Search by zip + radius
#     Distance in miles
#     Ref: http://www.timeanddate.com/worldclock/distances.html?n=283
#     """
#     AddUserRoles.add(user_first)
#     base_location = "San Jose, CA, 95113"  # distance from san jose, in miles
#     location_within_10_miles = {"city": "Santa Clara", "state": "CA", "zip_code": "95050"}  # 4.8
#     location_within_10_miles_2 = {"city": "Milpitas", "state": "CA", "zip_code": "95035"}  # 7.9
#     location_within_25_miles = {"city": "Newark", "state": "CA", "zip_code": "94560"}  # 19.2
#     location_within_25_miles_2 = {"city": "Stanford", "state": "CA", "zip_code": "94305"}  # 22.3
#     location_within_50_miles = {"city": "Oakland", "state": "CA", "zip_code": "94601"}  # 38
#     location_within_75_miles = {"city": "Novato", "state": "CA", "zip_code": "94945"}  # 65
#     location_within_100_miles = {'city': 'Sacramento', "state": "CA", "zip_code": "95405"}  # 89
#     location_more_than_100_miles = {'city': "Oroville", "state": "CA", "zip_code": "95965"}  # 151
#     # 10 mile candidates with city & state
#     _10_mile_candidate = populate_candidates(access_token=access_token_first,
#                                              talent_pool=talent_pool, **location_within_10_miles)
#     _10_mile_candidate_2 = populate_candidates(access_token=access_token_first,
#                                                talent_pool=talent_pool, **location_within_10_miles_2)
#     # 25 mile candidates with city state
#     _25_mile_candidate = populate_candidates(access_token=access_token_first,
#                                              talent_pool=talent_pool, **location_within_25_miles)
#     _25_mile_candidate_2 = populate_candidates(access_token=access_token_first,
#                                                talent_pool=talent_pool, **location_within_25_miles_2)
#     _50_mile_candidate = populate_candidates(access_token=access_token_first,
#                                              talent_pool=talent_pool, **location_within_50_miles)
#     _75_mile_candidate = populate_candidates(access_token=access_token_first,
#                                              talent_pool=talent_pool, **location_within_75_miles)
#     _100_mile_candidate = populate_candidates(access_token=access_token_first,
#                                               talent_pool=talent_pool, **location_within_100_miles)
#     # The following candidate will not appear in search with radius
#     _more_than_100_mile_candidate = populate_candidates(access_token=access_token_first,
#                                                         talent_pool=talent_pool, **location_more_than_100_miles)
#
#     candidates_within_10_miles = _10_mile_candidate + _10_mile_candidate_2
#     candidates_within_25_miles = candidates_within_10_miles + _25_mile_candidate + _25_mile_candidate_2
#     candidates_within_50_miles = candidates_within_25_miles + _50_mile_candidate
#     candidates_within_75_miles = candidates_within_50_miles + _75_mile_candidate
#     candidates_within_100_miles = candidates_within_75_miles + _100_mile_candidate
#     all_candidates = candidates_within_100_miles + _more_than_100_mile_candidate
#
#     # All candidates in domain; it will include more_than_100_mile_candidate also,
#     # which will not appear in other searches with radius.
#     _assert_search_results(user_first.domain_id, {'location': ''}, candidate_ids=all_candidates)
#     # With city, state and radius within 10 miles
#
#     _assert_search_results(user_first.domain_id, {'location': base_location, 'radius': 10},
#                            candidate_ids=candidates_within_10_miles,
#                            check_for_equality=True, wait=False)
#     # Search with zipcode within 10 miles
#     _assert_search_results(user_first.domain_id, {'location': base_location.split()[-1], 'radius': 10},
#                            candidate_ids=candidates_within_10_miles,
#                            check_for_equality=True, wait=False)
#     # With city, state and radius within 25 miles
#     _log_bounding_box_and_coordinates(base_location, 25, candidates_within_25_miles)
#     _assert_search_results(user_first.domain_id, {'location': base_location, 'radius': 25},
#                            candidate_ids=candidates_within_25_miles,
#                            check_for_equality=True, wait=False)
#     # default radius is 50 miles; search for 50 miles radius
#     _log_bounding_box_and_coordinates(base_location, 50, candidates_within_50_miles)
#     _assert_search_results(user_first.domain_id, {'location': base_location, 'radius': 50},
#                            candidate_ids=candidates_within_50_miles,
#                            check_for_equality=True, wait=False)
#     # 75 miles
#     _log_bounding_box_and_coordinates(base_location, 75, candidates_within_75_miles)
#     _assert_search_results(user_first.domain_id, {'location': base_location, 'radius': 75},
#                            candidate_ids=candidates_within_75_miles,
#                            check_for_equality=True, wait=False)
#     # 100 miles
#     _log_bounding_box_and_coordinates(base_location, 100, candidates_within_100_miles)
#     _assert_search_results(user_first.domain_id, {'location': base_location, 'radius': 100},
#                            candidate_ids=candidates_within_100_miles,
#                            check_for_equality=True, wait=False)


# TODO: fix failing test - Amir
# def test_sort_by_proximity(user_first, access_token_first, talent_pool):
#     """
#     Sort by distance
#     """
#     AddUserRoles.add(user_first)
#     user_id, domain_id = user_first.id, user_first.domain_id
#     base_location = "San Jose, CA"  # distance from san jose, in miles
#     location_within_10_miles = {"city": "Santa Clara", "state": "CA", "zip_code": "95050"}  # 4.8
#     location_within_10_miles_2 = {"city": "Milpitas", "state": "CA", "zip_code": "95035"}  # 7.9
#     location_within_25_miles = {"city": "Fremont", "state": "CA", "zip_code": "94560"}  # 16
#     location_within_50_miles = {"city": "Oakland", "state": "CA", "zip_code": "94601"}  # 38
#
#     # 10 mile candidates with city & state
#     _10_mile_candidate = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                              **location_within_10_miles)
#     _10_mile_candidate_2 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                                **location_within_10_miles_2)
#     # 25 mile candiates with city state
#     _25_mile_candidate = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                              **location_within_25_miles)
#     _50_mile_candidate = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                              **location_within_50_miles)
#     candidates_within_10_miles = [_10_mile_candidate[0], _10_mile_candidate_2[0]]
#     closest_to_furthest = [_10_mile_candidate[0], _10_mile_candidate_2[0], _25_mile_candidate[0], _50_mile_candidate[0]]
#
#     furthest_to_closest = closest_to_furthest[::-1]  # Reverse the order
#
#     # Without radius i.e. it will by default take 50 miles
#     # Sort by -> Proximity: Closest
#     proximity_closest = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['proximity']
#     _assert_search_results(domain_id, {'location': base_location, 'sort_by': proximity_closest},
#                            candidate_ids=closest_to_furthest, check_for_sorting=True)
#
#     # Sort by -> Proximity: Furthest
#     proximity_furthest = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~proximity']
#     _assert_search_results(domain_id, {'location': base_location, 'sort_by': proximity_furthest},
#                            candidate_ids=furthest_to_closest, check_for_sorting=True, wait=False)
#
#     # With city, state and radius within 10 miles. Sort by -> Proximity: closest
#     _assert_search_results(domain_id, {'location': base_location, 'radius': 10, 'sort_by': proximity_closest},
#                            candidate_ids=candidates_within_10_miles,
#                            check_for_sorting=True, wait=False)
#
#     # With city, state and radius within 10 miles. Sort by -> Proximity: Furthest
#     _assert_search_results(domain_id, {'location': base_location, 'radius': 10, 'sort_by': proximity_furthest},
#                            candidate_ids=candidates_within_10_miles[::-1],
#                            check_for_sorting=True, wait=False)

# TODO: Test fails very often during Jenkins build -- commenting out for now.
# def test_search_status(user_first, access_token_first):
#     """
#     Test to search all candidates by status
#     """
#     user_id = user_first.id
#     candidate_ids = populate_candidates(count=3, owner_user_id=user_id)
#     status_id = get_or_create_status(db, status_name="Hired")
#     # Change status of last candidate
#     Candidate.query.filter_by(id=candidate_ids[-1]).update(dict(candidate_status_id=status_id))
#     db.session.commit()
#     # Update cloud_search
#     upload_candidate_documents(candidate_ids[-1])
#     # Wait for 10 more seconds for cloudsearch to update data.
#     time.sleep(10)
#     response = get_response_from_authorized_user(access_token_first, '?status_ids=%d' % status_id)
#     # Only last candidate should appear in result.
#     _assert_results(candidate_ids[-1:], response.json())


# TODO: Complete test when CandidateSource API is ready - Amir
# def test_search_source(user_first, access_token_first, talent_pool):
#     """Test to search candidates by source"""
#     # Create a new source
#     AddUserRoles.add_and_get(user_first)
#     new_source = CandidateSource(description="Test source",
#                                  domain_id=user_first.domain_id,
#                                  notes="Sample source for functional tests")
#     db.session.add(new_source)
#     db.session.commit()
#     source_id = new_source.id
#     candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=5,
#                                         source_id=source_id)
#     response = get_response_from_authorized_user(access_token_first, '?source_ids={}'.format(source_id))
#     _assert_results(candidate_ids, response.json())


# def test_search_by_added_date(user_first, talent_pool, access_token_first):
#     """
#     Test to search candidates by added time
#     """
#     AddUserRoles.add(user_first)
#     domain_id = user_first.domain_id
#     # Candidate added on 01 Dec 2014 at 14:30:00
#     candidate1 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=3,
#                                      added_time='2014-12-01T14:30:00+00:00')
#     # Candidate added on 20 Mar 2015 at 10:00:00
#     candidate2 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=3,
#                                      added_time='2015-03-20T10:00:00+00:00')
#     # Candidate added on 25 May 2010 at 00:00:00
#     candidate3 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=3,
#                                      added_time='2010-05-25T00:00:00+00:00')
#     # Candidate added today (now)
#     candidate4 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                      added_time=DatetimeUtils.to_utc_str(datetime.datetime.now()))
#     # Get candidates from within range 1 jan'14 to 30 May'15 (format mm/dd/yyyy) -> Will include candidates 1 & 2
#     _assert_search_results(domain_id, {'date_from': '01/01/2014', 'date_to': '05/30/2015'},
#                            candidate_ids=candidate1 + candidate2)
#     # Get candidates from starting date as 15 Mar 2015 and without end date -> will include candidates- 2, 4
#     _assert_search_results(domain_id, {'date_from': '03/15/2015', 'date_to': ''},
#                            candidate_ids=candidate2 + candidate4, wait=False)
#     # Get candidates from no starting date but ending date as 31 Dec 2014 -> will give candidates 1 & 3
#     _assert_search_results(domain_id, {'date_from': '', 'date_to': '12/31/2014'},
#                            candidate_ids=candidate1 + candidate3, wait=False)
#     # Get candidates from no starting and no ending date i.e. all candidates
#     _assert_search_results(domain_id, {'date_from': '', 'date_to': ''},
#                            candidate_ids=candidate1 + candidate2 + candidate3 + candidate4, wait=False)
#
#
# def test_sort_by_added_date(user_first, access_token_first, talent_pool):
#     """
#     Least recent --> sort_by:added_time-asc
#     Most recent -->  sort_by:added_time-desc
#     """
#     AddUserRoles.add(user_first)
#     domain_id = user_first.domain_id
#     # Candidate added on 25 May 2010 at 00:00:00
#     candidate1 = populate_candidates(user_id=user_first.id,
#                                      added_time=datetime.datetime(2010, 05, 25, 00, 00, 00),
#                                      update_now=False)
#     # Candidate added on 01 Dec 2014 at 14:30:00
#     candidate2 = populate_candidates(user_id=user_first.id,
#                                      added_time=datetime.datetime(2014, 12, 01, 14, 30, 00),
#                                      update_now=False)
#     # Candidate added on 20 Mar 2015 at 10:00:00
#     candidate3 = populate_candidates(user_id=user_first.id,
#                                      added_time=datetime.datetime(2015, 03, 20, 10, 00, 00),
#                                      update_now=False)
#     # Candidate added today (now)
#     candidate4 = populate_candidates(user_id=user_first.id, added_time=datetime.datetime.now(), update_now=False)
#     sorted_in_ascending_order_of_added_time = candidate1 + candidate2 + candidate3 + candidate4
#     _update_now(sorted_in_ascending_order_of_added_time)
#     sorted_in_descending_order_of_added_time = sorted_in_ascending_order_of_added_time[::-1]
#     # check for order in which candiate were added. Sort by Date: Most recent - all candidates
#     most_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['recent']
#     _assert_search_results(domain_id, {'sort_by': most_recent},
#                            candidate_ids=sorted_in_descending_order_of_added_time, check_for_sorting=True)
#     # Sort by Date: Least recent - all candidates
#     least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
#     _assert_search_results(domain_id, {'sort_by': least_recent},
#                            candidate_ids=sorted_in_ascending_order_of_added_time,
#                            check_for_sorting=True, wait=False)
#     # Get candidates from within range 1 jan'14 to 30 May'15 -> Will include candidates 3rd & 2nd in descending order
#     _assert_search_results(domain_id, {'date_from': '01/01/2014', 'date_to': '05/30/2015',
#                                        'sort_by': most_recent}, candidate_ids=candidate3 + candidate2,
#                            wait=False)


# # TODO: fix test - Amir
# def to_fix_test_area_of_interest_facet(sample_user):
#     """
#     Test areaOfInterestIdFacet by passing aoi values as list and as single select
#     areaOfInterestIdFacet:<id>
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     all_aoi_ids = create_area_of_interest_facets(db, domain_id)
#     print "Total area of interest facets present: %s" % len(all_aoi_ids)
#     aoi_ids_list_1 = all_aoi_ids[0:5]
#     aoi_ids_list_2 = all_aoi_ids[-4:-1]
#     candidate1 = populate_candidates(user_id=sample_user.id, areas_of_interest=aoi_ids_list_1,
#                                      update_now=False)
#     candidate2 = populate_candidates(user_id=sample_user.id, areas_of_interest=aoi_ids_list_2,
#                                      update_now=False)
#     _update_now(candidate1 + candidate2)
#     _assert_search_results(domain_id, {"area_of_interest_ids": ','.join(aoi_ids_list_1[0:3])}, candidate1,
#                            check_for_equality=True, wait=False)
#     _assert_search_results(domain_id, {"area_of_interest_ids": ','.join(aoi_ids_list_2[0])}, candidate2,
#                            check_for_equality=True, wait=False)
#     _assert_search_results(domain_id, {"area_of_interest_ids": ','.join([aoi_ids_list_2[-1], aoi_ids_list_1[-2]])},
#                            candidate1 + candidate2,
#                            check_for_equality=True, wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_status_facet(sample_user):
#     """
#     Test with status facet by passing value as list and single value
#     statusFacet: <status_id>
#     :param sample_user:
#     :return:
#     """
#
#     domain_id = sample_user.domain_id
#     # By default every candidate has "New" status
#     candidate1 = populate_candidates(user_id=sample_user.id)
#     candidate2 = populate_candidates(user_id=sample_user.id)
#     candidate3 = populate_candidates(user_id=sample_user.id)
#     new_status_id = get_or_create_status(db, status_name="New")
#     _assert_search_results(domain_id, {'status': new_status_id}, candidate1 + candidate2 + candidate3)
#     status1_id = get_or_create_status(db, status_name="Qualified")
#     status2_id = get_or_create_status(db, status_name="Hired")
#     # Change status of candidate1
#     db.session.query(Candidate).filter_by(id=candidate1[0]).update(dict(candidate_status_id=status1_id))
#     db.session.query(Candidate).filter_by(id=candidate2[0]).update(dict(candidate_status_id=status2_id))
#     # Update cloud_search for status changes
#     _update_now(candidate1 + candidate2)
#     # search for qualified candidates
#     _assert_search_results(domain_id, {'status_ids': str(status1_id)}, candidate1, check_for_equality=True)
#     _assert_search_results(domain_id, {'status_ids': str(status2_id)}, candidate2, check_for_equality=True, wait=False)
#     _assert_search_results(domain_id, {'status_ids': ','.join([status1_id, status2_id])}, candidate2 + candidate1,
#                            check_for_equality=True, wait=False)
#     _assert_search_results(domain_id, {'status_ids': str(new_status_id)}, candidate3, check_for_equality=True,
#                            wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_source_facet(sample_user):
#     """
#     Test search filter for various available source facets.
#     sourceFacet:<source id>
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     # by default all candidates have "Unassigned" source
#     candidate_ids1 = populate_candidates(user_id=sample_user.id, count=5, update_now=False)
#     # Create a new source
#     source_id = CandidateSource(description="Test source-%s" % uuid.uuid4().__str__()[0:8],
#                                 domain_id=domain_id, notes="Source created for functional tests")
#     db.session.add(source_id)
#     db.session.commit()
#     candidate_ids2 = populate_candidates(user_id=sample_user.id, count=5, source_id=source_id, update_now=False)
#     # Update database and cloud_search
#     all_candidates = candidate_ids1 + candidate_ids2
#     _update_now(all_candidates)
#     # Search for candidates with created source, it will not include candidates with unassigned source
#     _assert_search_results(domain_id, {"source_ids": str(source_id)}, candidate_ids2, check_for_equality=True)
#
#
# # TODO: fix test - Amir
# def _test_search_based_on_years_of_experience(sample_user):
#     """
#     minimum_years_experience
#     maximum_years_experience
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     experience_above_10_years = [{'organization': 'Amazon', 'position': 'Software Architect', 'startYear': 2014,
#                                   'startMonth': '09', 'isCurrent': True},
#                                  {'organization': 'Amazon', 'position': 'Sr. Software Developer',
#                                   'startYear': '2008', 'startMonth': '04',
#                                   'endYear': 2014, 'endMonth': '08'},
#                                  {'organization': 'Amazon', 'position': 'Software Developer', 'startYear': 2004,
#                                   'startMonth': '03', 'endYear': 2008, 'endMonth': '03',
#                                   'candidate_experience_bullets': [{'description':
#                                                                         'Developed An Online Complaint And Resolution '
#                                                                         'Database System In Perl Under The Instruction '
#                                                                         'Of Professor Brian Harvey For Students In '
#                                                                         'Computer Science Classes. Various System '
#                                                                         'Administration And Maintenance Tasks.'}]}]
#     experience_5_years = [{'organization': 'Samsung', 'position': 'Area Manager', 'startYear': 2013, 'startMonth': 06,
#                            'endYear': 2015, 'endMonth': '01'},
#                           {'organization': 'Motorola', 'position': 'Area Manager', 'startYear': 2011, 'startMonth': 11,
#                            'endYear': 2013, 'endMonth': '05'},
#                           {'organization': 'Nokia', 'position': 'Marketing executive', 'startYear': 2010,
#                            'startMonth': '01', 'endYear': 2011, 'endMonth': '10'}]  # 60 months exp
#     experience_2_years = [{'organization': 'Intel', 'position': 'Research analyst', 'startYear': 2013, 'startMonth': 06,
#                            'endYear': 2015, 'endMonth': '06'}]  # 24 months exp
#     experience_0_years = [{'organization': 'Audi', 'position': 'Mechanic', 'startYear': 2015, 'startMonth': 01,
#                            'endYear': 2015, 'endMonth': 02}]  # 2 month exp
#     candidate_with_0_years_exp = populate_candidates(user_id=sample_user.id,
#                                                      candidate_experience_dicts=experience_0_years,
#                                                      update_now=False)
#     candidate_with_2_years_exp = populate_candidates(user_id=sample_user.id,
#                                                      candidate_experience_dicts=experience_2_years,
#                                                      update_now=False)
#     candidate_with_5_years_exp = populate_candidates(user_id=sample_user.id,
#                                                      candidate_experience_dicts=experience_5_years,
#                                                      update_now=False)
#     candidate_above_10_years_exp = populate_candidates(user_id=sample_user.id,
#                                                        candidate_experience_dicts=experience_above_10_years,
#                                                        update_now=False)
#     # TODO: Check if there is still need of updating total_months_experience?
#     db.session.commit()
#     db.session.query(Candidate).filter_by(id=candidate_with_0_years_exp[0]).update(dict(total_months_experience=2))
#     db.session.query(Candidate).filter_by(id=candidate_with_2_years_exp[0]).update(dict(total_months_experience=24))
#     db.session.query(Candidate).filter_by(id=candidate_with_5_years_exp[0]).update(dict(total_months_experience=5 * 12))
#     db.session.query(Candidate).filter_by(id=candidate_above_10_years_exp[0]).update(
#         dict(total_months_experience=11 * 12))
#     # Update cloudsearch
#     all_candidates = candidate_with_0_years_exp + candidate_with_2_years_exp + candidate_with_5_years_exp + \
#                      candidate_above_10_years_exp
#     _update_now(all_candidates)
#
#     # Search for candidates with more than 10 years
#     _assert_search_results(domain_id, {"minimum_years_experience": 10}, candidate_above_10_years_exp)
#     _assert_search_results(domain_id, {"minimum_years_experience": 1, "maximum_years_experience": 6},
#                            candidate_with_2_years_exp + candidate_with_5_years_exp, wait=False)
#     _assert_search_results(domain_id, {"maximum_years_experience": 4}, candidate_with_0_years_exp +
#                            candidate_with_2_years_exp, wait=False)
#     _assert_search_results(domain_id, {"minimum_years_experience": "", "maximum_years_experience": ""},
#                            candidate_with_0_years_exp + candidate_with_2_years_exp + candidate_with_5_years_exp +
#                            candidate_above_10_years_exp,
#                            wait=False)
#
#
# # TODO: fix test - Amir
# def _test_skill_description_facet(sample_user):
#     """
#     skillDescriptionFacet
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     network_candidates = populate_candidates(user_id=sample_user.id, count=2,
#                                              skills=[{'last_used': datetime.datetime.now(),
#                                                       'name': 'Network', 'months_used': 12}],
#                                              update_now=True)
#
#     excel_candidates = populate_candidates(user_id=sample_user.id,
#                                            skills=[{'last_used': datetime.datetime.now(),
#                                                     'name': 'Excel', 'months_used': 26}],
#                                            update_now=True)
#     network_and_excel_candidates = populate_candidates(sample_user.id, count=3,
#                                                        skills=[{'last_used': datetime.datetime.now(),
#                                                                 'name': 'Excel',
#                                                                 'months_used': 10},
#                                                                {'last_used': datetime.datetime.now(),
#                                                                 'name': 'Network',
#                                                                 'months_used': 5}], update_now=True)
#     # Update db and cloudsearch
#     _update_now(network_candidates + excel_candidates + network_and_excel_candidates)
#     _assert_search_results(domain_id, {'skills': 'Network'},
#                            candidate_ids=network_candidates + network_and_excel_candidates)
#     _assert_search_results(domain_id, {'skills': 'Excel'},
#                            candidate_ids=excel_candidates + network_and_excel_candidates, wait=False)
#     _assert_search_results(domain_id, {'skills': ['Excel', 'Network']},
#                            candidate_ids=network_and_excel_candidates, wait=False)
#
#
# def to_fix_test_date_of_separation(sample_user):
#     """
#     Date of separation -
#     military_end_date_from
#     military_end_date_to
#     :param sample_user:
#     :return:
#     """
#     """
#
#     """
#     domain_id = sample_user.domain_id
#     candidates_today = populate_candidates(sample_user.id, count=5, military_to_date=datetime.datetime.now(),
#                                            military_grade=True,
#                                            military_status=True, military_branch=True, update_now=False)
#     candidates_2014 = populate_candidates(sample_user.id, count=2,
#                                           military_to_date=datetime.date(year=2014, month=03, day=31),
#                                           update_now=False)
#     candidates_2012 = populate_candidates(sample_user.id, military_to_date=datetime.date(2012, 07, 15),
#                                           update_now=False)
#
#     # Update db and cloudsearch
#     _update_now(candidates_2012 + candidates_2014 + candidates_today)
#     # get candidates where date of separation is
#     _assert_search_results(domain_id, {'military_end_date_from': 2013},
#                            candidate_ids=candidates_2014 + candidates_today)
#     _assert_search_results(domain_id, {'military_end_date_from': 2010},
#                            candidate_ids=candidates_2012 + candidates_2014 + candidates_today, wait=False)
#     _assert_search_results(domain_id, {'military_end_date_from': 2010, 'military_end_date_to': 2014},
#                            candidate_ids=candidates_2012 + candidates_2014, wait=False)
#     _assert_search_results(domain_id, {'military_end_date_to': 2012}, candidate_ids=candidates_2012, wait=False)
#     _assert_search_results(domain_id, {'military_end_date_to': 2014}, candidate_ids=candidates_2012 + candidates_2014,
#                            wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_service_status(sample_user):
#     """
#     military_service_status
#     Facet name: serviceStatus
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     service_status1 = "Veteran"
#     service_status2 = "Guard"
#     service_status3 = "Retired"
#     candidates_status1 = populate_candidates(user_id=sample_user.id, count=4, military_status=service_status1,
#                                              update_now=False)
#     candidates_status2 = populate_candidates(user_id=sample_user.id, count=7, military_status=service_status2,
#                                              update_now=False)
#     candidates_status3 = populate_candidates(user_id=sample_user.id, count=2, military_status=service_status3,
#                                              update_now=False)
#     # Update all candidates at once
#     all_candidates = candidates_status1 + candidates_status2 + candidates_status3
#     _update_now(all_candidates)
#
#     _assert_search_results(domain_id, {'military_service_status': service_status1}, candidates_status1)
#     _assert_search_results(domain_id, {'military_service_status': service_status2}, candidates_status2, wait=False)
#     _assert_search_results(domain_id, {'military_service_status': [service_status1, service_status3]},
#                            candidates_status1 + candidates_status3, wait=False)
#     _assert_search_results(domain_id, {'military_service_status': [service_status1, service_status2, service_status3]},
#                            all_candidates, wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_military_branch(sample_user):
#     """
#     branch: military_branch
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     service_branch1 = "Army"
#     service_branch2 = "Coast Guard"
#     service_branch3 = "Air Force"
#     candidates_branch1 = populate_candidates(user_id=sample_user.id, count=4, military_branch=service_branch1,
#                                              update_now=False)
#     candidates_branch2 = populate_candidates(user_id=sample_user.id, count=7, military_branch=service_branch2,
#                                              update_now=False)
#     candidates_branch3 = populate_candidates(user_id=sample_user.id, count=2, military_branch=service_branch3,
#                                              update_now=False)
#     all_candidates = candidates_branch1 + candidates_branch2 + candidates_branch3
#     # Update all candidates at once
#     _update_now(all_candidates)
#
#     _assert_search_results(domain_id, {'military_branch': service_branch1}, candidates_branch1)
#     _assert_search_results(domain_id, {'military_branch': service_branch2}, candidates_branch2, wait=False)
#     _assert_search_results(domain_id, {'military_branch': [service_branch1, service_branch3]}, candidates_branch1 +
#                            candidates_branch3, wait=False)
#     _assert_search_results(domain_id, {'military_branch': [service_branch1, service_branch2, service_branch3]},
#                            all_candidates,
#                            wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_search_by_military_grade(sample_user):
#     """
#     military highest grade
#     Facet name 'highestGrade'
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     service_grade1 = "E-2"
#     service_grade2 = "O-4"
#     service_grade3 = "W-1"
#     candidates_grade1 = populate_candidates(user_id=sample_user.id, count=3, military_grade=service_grade1,
#                                             update_now=False)
#     candidates_grade2 = populate_candidates(user_id=sample_user.id, count=2, military_grade=service_grade2,
#                                             update_now=False)
#     candidates_grade3 = populate_candidates(user_id=sample_user.id, count=5, military_grade=service_grade3,
#                                             update_now=False)
#     all_candidates = candidates_grade1 + candidates_grade2 + candidates_grade3
#     # Update all candidates at once
#     _update_now(all_candidates)
#
#     _assert_search_results(domain_id, {'military_highest_grade': service_grade1}, candidates_grade1)
#     _assert_search_results(domain_id, {'military_highest_grade': service_grade2}, candidates_grade2, wait=False)
#     _assert_search_results(domain_id, {'military_highest_grade': [service_grade1, service_grade3]}, candidates_grade1 +
#                            candidates_grade3, wait=False)
#     _assert_search_results(domain_id, {'military_highest_grade': [service_grade1, service_grade2, service_grade3]},
#                            all_candidates, wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_custom_fields_kaiser_nuid(sample_user):
#     """
#     Test kaiser specific custom field "Has NUID"
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     custom_field_obj = db.session.query(CustomField).filter(CustomField.name == "NUID").first()
#     if custom_field_obj:
#         custom_field_obj_id = custom_field_obj.id
#     else:
#         print "Creating custom field with name=NUID"
#         new_custom_field_obj = CustomField(domain_id=domain_id, name="NUID", type='string',
#                                            added_time=datetime.datetime.now())
#         db.session.add(new_custom_field_obj)
#         db.session.commit()
#         custom_field_obj_id = new_custom_field_obj.id
#     other_candidates = populate_candidates(user_id=sample_user.id, count=2, update_now=False)
#     candidate_cf1 = populate_candidates(user_id=sample_user.id,
#                                         custom_fields_dict={'custom_field_id': custom_field_obj_id,
#                                                             'value': 'S264964'}, update_now=False)
#     candidate_cf2 = populate_candidates(user_id=sample_user.id,
#                                         custom_fields_dict={'custom_field_id': custom_field_obj_id,
#                                                             'value': 'D704398'}, update_now=False)
#     candidate_cf3 = populate_candidates(user_id=sample_user.id,
#                                         custom_fields_dict={'custom_field_id': custom_field_obj_id,
#                                                             'value': 'X073423'}, update_now=False)
#
#     # Update all candidates in db and cloudsearch
#     nuid_candidates = candidate_cf1 + candidate_cf2 + candidate_cf3
#     all_candidates = other_candidates + nuid_candidates
#     _update_now(all_candidates)
#
#     _assert_search_results(domain_id, {"query": ""}, all_candidates)  # should give all candidates in domain
#     # searched for cf-19; should return only nuid candidates
#     _assert_search_results(domain_id, {"cf-%d" % custom_field_obj_id: "Has NUID"}, nuid_candidates, wait=False)
#
#
# # TODO: fix test - Amir
# def _test_custom_fields(sample_user):
#     """
#     Test various custom_fields
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     # Create custom field category named as 'Certifications'
#     custom_field_cat = CustomFieldCategory(domain_id=domain_id, name="Certifications")
#     db.session.add(custom_field_cat)
#     custom_field_cat_id = custom_field_cat.id
#     # Create custom fields under 'Certifications'
#     custom_field1 = 'hadoop'
#     custom_field2 = 'MangoDB'
#     new_custom_field1 = CustomField(domain_id=domain_id, name=custom_field1, type='string',
#                                     category_id=custom_field_cat_id, added_time=datetime.datetime.now())
#     db.session.add(new_custom_field1)
#
#     new_custom_field2 = CustomField(domain_id=domain_id, name=custom_field2, type='string',
#                                     category_id=custom_field_cat_id, added_time=datetime.datetime.now())
#     db.session.add(new_custom_field2)
#     db.session.commit()
#     custom_field1_id = new_custom_field1.id
#     custom_field2_id = new_custom_field2.id
#     # refresh_custom_fields_cache
#     candidates_cf1 = populate_candidates(user_id=sample_user.id, count=3,
#                                          custom_fields_dict={'custom_field_id': custom_field1_id,
#                                                              'value': custom_field1}, update_now=False)
#     candidates_cf2 = populate_candidates(user_id=sample_user.id, count=4,
#                                          custom_fields_dict={'value': custom_field2,
#                                                              'custom_field_id': custom_field2_id}, update_now=False)
#     all_candidates = candidates_cf1 + candidates_cf2
#     _update_now(all_candidates)
#     _assert_search_results(domain_id, {"cf-%s" % custom_field1_id: custom_field1}, candidates_cf1)
#     _assert_search_results(domain_id, {"cf-%s" % custom_field2_id: custom_field2}, candidates_cf2, wait=False)
#     _assert_search_results(domain_id, {"cf-%s" % custom_field1_id: custom_field1, "cf-%s" %
#                                                                                   custom_field2_id: custom_field2},
#                            all_candidates, wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_paging(sample_user):
#     """
#     Test candidates on all pages
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     candidate_ids = populate_candidates(user_id=sample_user.id, count=50, objective=True, added_time=True,
#                                         phone=True,
#                                         company_name=True, job_title=True, candidate_text_comment=True,
#                                         city=True, state=True,
#                                         zip_code=True, school_name=True, major=True, degree_title=True,
#                                         university_start_year=True,
#                                         university_start_month=True, graduation_year=True, graduation_month=True,
#                                         military_branch=True,
#                                         military_status=True, military_grade=True)
#     # page 1 -> first 15 candidates
#     least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
#     _assert_search_results(domain_id, {'sort_by': least_recent}, candidate_ids[0:15], check_for_sorting=True)
#     _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 1}, candidate_ids[0:15],
#                            check_for_sorting=True, wait=False)  # explicitly passing page 1 as parameter
#     # page2 -> next 15 candidates i.e. 15 to 30
#     _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 2}, candidate_ids[15:30],
#                            check_for_sorting=True, wait=False)
#     # page3 -> next 15 candidates i.e. 30 to 45
#     _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 3}, candidate_ids[30:45],
#                            check_for_sorting=True, wait=False)
#     # page4 -> next 15 candidates i.e. 45 to 50
#     _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 4}, candidate_ids[45:],
#                            check_for_sorting=True, wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_paging_with_facet_search(sample_user):
#     """
#     Test for no. of pages that are having candidates
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     current_title = "Sr. Manager"
#     candidate_ids = populate_candidates(count=30, user_id=sample_user.id, objective=True, phone=True,
#                                         added_time=True, company_name=True, job_title=current_title)
#     # Search by applying sorting so that candidates can be easily asserted
#     least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
#     _assert_search_results(domain_id, {'position': current_title, 'sort_by': least_recent},
#                            candidate_ids[0:15])
#     _assert_search_results(domain_id, {'position': current_title, 'sort_by': least_recent, 'page': 2},
#                            candidate_ids[15:30], wait=False)
#
#
# # TODO: fix test - Amir
# def _test_id_in_request_vars(sample_user):
#     """
#     There is a case where id can be passed as parameter in search_candidates
#     It can be used to check if a certain candidate ID is in a smartlist.
#     :param sample_user:
#     :return:
#     """
#     domain_id = sample_user.domain_id
#     # Insert 10 candidates
#     candidate_ids = populate_candidates(user_id=sample_user.id, count=10, objective=True, phone=True,
#                                         company_name=True,
#                                         job_title=True, candidate_text_comment=True, city=True, state=True,
#                                         zip_code=True, school_name=True, major=True, degree_title=True,
#                                         university_start_year=True, university_start_month=True, graduation_year=True,
#                                         graduation_month=True, military_branch=True, military_status=True,
#                                         military_grade=True)
#     # First candidate id
#     first_candidate_id = candidate_ids[0]
#     middle_candidate_id = candidate_ids[5]
#     last_candidate_id = candidate_ids[-1]
#     # if searched for particular candidate id, search should only return that candidate.
#     _assert_search_results(domain_id, {'id': middle_candidate_id}, [middle_candidate_id], check_for_equality=True)
#     _assert_search_results(domain_id, {'id': last_candidate_id}, [last_candidate_id], check_for_equality=True,
#                            wait=False)
#     _assert_search_results(domain_id, {'id': first_candidate_id}, [first_candidate_id], check_for_equality=True,
#                            wait=False)
#
#
# # TODO: fix test - Amir
# def to_fix_test_facets_are_returned_with_search_results(test_domain, sample_user, sample_user_2):
#     """
#     Test selected facets are returned with search results
#     :param sample_user:
#     :param sample_user_2:
#     :return:
#     """
#     domain_id = test_domain.id
#
#     sample_user_candidate_ids = populate_candidates(user_id=sample_user.id, count=2, update_now=False)
#     sample_user_2_candidate_ids = populate_candidates(user_id=sample_user_2.id, count=1,
#                                                       update_now=False)
#     all_candidates = sample_user_candidate_ids + sample_user_2_candidate_ids
#     # Update
#     _update_now(all_candidates)
#
#     # There is always one 'unassigned' source for every domain.
#     unassigned_candidate_source = db.session.query(CandidateSource).filter(CandidateSource.description == 'Unassigned',
#                                                                            CandidateSource.domain_id == domain_id).first()
#     # By default each candidate is assigned 'New' status
#     new_status_id = get_or_create_status(db, status_name="New")
#     facets = {'username': [{"value": sample_user.first_name + ' ' + sample_user.last_name,
#                             "id": unicode(sample_user.id),
#                             "count": 2},
#                            {"value": sample_user_2.first_name + ' ' + sample_user_2.last_name,
#                             "id": unicode(sample_user_2.id),
#                             "count": 1}],
#               'source': [{"value": unassigned_candidate_source.description,
#                           "count": unicode(unassigned_candidate_source.id),
#                           "id": 3}],
#               'statusFacet': [{"value": 'New',
#                                "id": unicode(new_status_id),
#                                "count": 3}]
#               }
#     _assert_search_results(domain_id, {'query': ''}, all_candidates, check_for_equality=True, facets_dict=facets)
#
#
# # TODO: fix test - Amir
# def OK_test_sort_by_match(sample_user):
#     """
#     TODO: Remove OK_ in name once comments in candidates creation is fixed.
#     """
#     candidate1 = populate_candidates(user_id=sample_user.id, company_name="Newvision", update_now=False)
#     candidate2 = populate_candidates(user_id=sample_user.id, company_name="Newvision",
#                                      objective="Willing to join Newvision",
#                                      update_now=False)
#     candidate3 = populate_candidates(user_id=sample_user.id, company_name="Newvision",
#                                      objective="Willing to join Newvision",
#                                      candidate_text_comment="Eligible for joining Newvision", update_now=False)
#     worst_match_order = candidate1 + candidate2 + candidate3
#     best_match_order = worst_match_order[::-1]
#     _update_now(worst_match_order)
#     # search for Newvision - worst-match
#     worst_match = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~match']
#     _assert_search_results(sample_user.domain_id, {'query': 'Newvision', 'sort_by': worst_match}, worst_match_order,
#                            check_for_sorting=True)
#     # search for Newvision - Best match
#     best_match = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['match']
#     _assert_search_results(sample_user.domain_id, {'query': 'Newvision', 'sort_by': best_match}, best_match_order,
#                            check_for_sorting=True)


def _log_bounding_box_and_coordinates(base_location, radius, candidate_ids):
    """
    Display bounding box coordinates relative to radius (distance) and coordinates of candidate location
    :param base_location:
    :param radius:
    :param candidate_ids:
    :return:
    """
    distance_in_km = float(radius) / 0.62137
    coords_dict = get_geocoordinates_bounding(base_location, distance_in_km)
    top_left_y, top_left_x, bottom_right_y, bottom_right_x = coords_dict['top_left'][0], coords_dict['top_left'][1], \
                                                             coords_dict['bottom_right'][0], \
                                                             coords_dict['bottom_right'][1]
    # Lat = Y Lng = X
    print "%s miles bounding box coordinates: ['%s,%s','%s,%s']" % (radius, top_left_y, top_left_x, bottom_right_y,
                                                                    bottom_right_x)
    if type(candidate_ids) in (int, long):
        candidate_ids = [candidate_ids]
    for index, candidate_id in enumerate(candidate_ids, start=1):
        row = db.session.query(CandidateAddress).filter_by(candidate_id=candidate_id).first()
        if row:
            print "Candidate-%s Address: %s, %s, %s. \n cooridnates: %s" % (index, row.city, row.state,
                                                                            row.zip_code, row.coordinates)

            point = row.coordinates.split(',')
            statement1 = top_left_x <= float(point[1]) <= bottom_right_x
            statement2 = top_left_y >= float(point[0]) >= bottom_right_y
            print "Candidate-%s %s bounding box" % (index, 'lies inside' if statement1 and statement2 else 'not in')
            print "%s <= %s <= %s = %s" % (top_left_x, point[1], bottom_right_x, statement1)
            print "%s >= %s >= %s = %s" % (top_left_y, point[0], bottom_right_y, statement2)


def _assert_results(candidate_ids, response):
    """
    Assert statements for all search results
    :param candidate_ids: list of candidate ids created by the authorized user under same domain
    """
    # List of candidate IDs from the search result
    resultant_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
    print "\nresponse: {}".format(response)
    print '\ncandidate_ids: {}'.format(candidate_ids)
    print '\nresultant_candidate_ids: {}'.format(resultant_candidate_ids)
    # Test whether every element in the set candidate_ids is in resultant_candidate_ids.
    assert set(candidate_ids).issubset(set(resultant_candidate_ids))


def get_response(access_token, arguments_to_url, expected_count, timeout=100):
    # Wait for cloudsearch to update the candidates
    url = CandidateApiUrl.CANDIDATE_SEARCH_URI + arguments_to_url
    headers = {'Authorization': 'Bearer %s' % access_token, 'Content-type': 'application/json'}
    if poll(lambda: len(requests.get(url, headers=headers).json()['candidates']) >= expected_count, step=5,
            timeout=timeout):
        return requests.get(url=url, headers=headers)
