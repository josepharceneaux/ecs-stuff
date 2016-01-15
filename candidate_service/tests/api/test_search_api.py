"""
Test cases for candidate-search-service-API
"""
from candidate_service.tests.modules.test_talent_cloud_search import populate_candidates, VARIOUS_US_LOCATIONS, \
    create_area_of_interest_facets, get_or_create_status
from candidate_service.common.tests.conftest import *
from candidate_service.common.models.candidate import Candidate, CandidateSource
from candidate_service.common.models.misc import CustomFieldCategory
from candidate_service.modules.talent_cloud_search import upload_candidate_documents
from candidate_service.common.routes import CandidateApiUrl
import random
import datetime
import uuid
import time
import requests

SEARCH_URI = CandidateApiUrl.CANDIDATE_SEARCH_URI


def test_search_all_candidates_in_domain(sample_user, user_auth):
    """
    Test to search all candidates under the same domain
    :param sample_user: user to create candidates under the same domain
    :param user_auth: User Authentication
    :return:
    """
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id)
    response = get_response_from_authorized_user(user_auth, sample_user, '')
    _assert_results(candidate_ids, response.json())


# def test_search_location(sample_user, user_auth):
#     """
#     Test to search candidates using location
#     :param sample_user: user-row
#     :param user_auth: User Authentication
#     :return:
#     """
#     city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
#     time.sleep(10)
#     candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, city=city, state=state,
#                                         zip_code=zip_code)
#     response = get_response_from_authorized_user(user_auth, sample_user, '?location=%s,%s' % (city, state))
#     _assert_results(candidate_ids, response.json())


def test_search_user_ids(sample_user, user_auth):
    """
    Test to search all candidates under the user
    :param sample_user: user-row
    :param user_auth: User Authentication
    :return:
    """
    user_id = sample_user.id
    candidate_ids = populate_candidates(count=5, owner_user_id=user_id)
    response = get_response_from_authorized_user(user_auth, sample_user, '?user_ids=%d' % user_id)
    _assert_results(candidate_ids, response.json())


def test_search_skills(sample_user, user_auth):
    """
    Test to search all candidates based on skills
    :param sample_user: user-row
    :param user_auth: User Authentication
    :return:
    """
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id,
                                        candidate_skill_dicts=[{'last_used':datetime.datetime.now(),
                                                                'name': 'hadoop', 'months_used': 36}],
                                        update_now=True)
    response = get_response_from_authorized_user(user_auth, sample_user, '?skills=hadoop')
    _assert_results(candidate_ids, response.json())


def test_search_aoi(sample_user, user_auth):
    """
    Test to search all candidates based on area_of_interest
    :param sample_user: user-row
    :param user_auth: User Authentication
    :return:
    """
    all_aoi_ids = create_area_of_interest_facets(db, sample_user.domain_id)
    print "Total area of interest facets present: %s" % len(all_aoi_ids)
    aoi_ids_list = all_aoi_ids[0:5]
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id, area_of_interest_ids=aoi_ids_list)
    response = get_response_from_authorized_user(user_auth, sample_user, '?area_of_interest_ids=%d' % aoi_ids_list[1])
    _assert_results(candidate_ids, response.json())

# TODO: This test fails very often during circlCI build. I'm commenting it for time being.
# def test_search_status(sample_user, user_auth):
#     """
#     Test to search all candidates by status
#     :param sample_user: user-row
#     :param user_auth: User Authentication
#     :return:
#     """
#     user_id = sample_user.id
#     candidate_ids = populate_candidates(count=3, owner_user_id=user_id)
#     status_id = get_or_create_status(db, status_name="Hired")
#     # Change status of last candidate
#     Candidate.query.filter_by(id=candidate_ids[-1]).update(dict(candidate_status_id=status_id))
#     db.session.commit()
#     # Update cloud_search
#     upload_candidate_documents(candidate_ids[-1])
#     # Wait for 10 more seconds for cloudsearch to update data.
#     time.sleep(10)
#     response = get_response_from_authorized_user(user_auth, sample_user, '?status_ids=%d' % status_id)
#     # Only last candidate should appear in result.
#     _assert_results(candidate_ids[-1:], response.json())


def to_fix_test_search_source(sample_user, user_auth):
    """
    Test to search candidates by source

    """
    # Create a new source
    new_source = CandidateSource(description="Test source",
                                 domain_id=sample_user.domain_id, notes="Sample source for functional tests")
    db.session.add(new_source)
    db.session.commit()
    source_id = new_source.id
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id, source_id=source_id)
    response = get_response_from_authorized_user(user_auth, sample_user, '?source_ids=%d' % source_id)
    _assert_results(candidate_ids, response.json())


def test_search_candidate_experience(sample_user, user_auth):
    """
    Test to search candidates with experience

    """
    user_id = sample_user.id
    experience_2_years = [{'organization': 'Intel', 'position': 'Research analyst', 'startYear': 2013, 'startMonth': 06,
                           'endYear': 2015, 'endMonth': '06'}]
    experience_0_years = [{'organization': 'Audi', 'position': 'Mechanic', 'startYear': 2015, 'startMonth': 01,
                           'endYear': 2015, 'endMonth': 02}]
    candidate_ids = []
    candidate_with_0_years_exp = populate_candidates(count=3, owner_user_id=user_id,
                                                     candidate_experience_dicts=experience_0_years)
    for candidate_id in candidate_with_0_years_exp:
        db.session.query(Candidate).filter_by(id=candidate_id).update(dict(total_months_experience=2))
        db.session.flush()
        candidate_ids.append(candidate_id)
    candidate_with_2_years_exp = populate_candidates(count=3, owner_user_id=user_id,
                                                     candidate_experience_dicts=experience_2_years)
    for candidate_id in candidate_with_2_years_exp:
        db.session.query(Candidate).filter_by(id=candidate_id).update(dict(total_months_experience=24))
        db.session.commit()
        candidate_ids.append(candidate_id)
    # Update cloud_search
    upload_candidate_documents(candidate_ids)
    response = get_response_from_authorized_user(user_auth, sample_user, '?minimum_years_experience=0&maximum_years_experience=2')
    _assert_results(candidate_ids, response.json())


def test_search_position(sample_user, user_auth):
    """
    Test to search candidates by job_title/position

    """
    candidate_ids = populate_candidates(count=4, owner_user_id=sample_user.id, current_title="Developer")
    response = get_response_from_authorized_user(user_auth, sample_user, '?job_title=Developer')
    _assert_results(candidate_ids, response.json())


def test_search_degree(sample_user, user_auth):
    """
    Test to search candidates by degree type

    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, degree="Masters", university=True)
    response = get_response_from_authorized_user(user_auth, sample_user, '?degree_type=Masters')
    _assert_results(candidate_ids, response.json())


def test_search_school_name(sample_user, user_auth):
    """
    Test to search candidates by university/school_name

    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, university='Oklahoma State University')
    response = get_response_from_authorized_user(user_auth, sample_user, '?school_name=Oklahoma State University')
    _assert_results(candidate_ids, response.json())


def test_search_concentration(sample_user, user_auth):
    """
    Test to search candidates by higher education
    """
    candidate_ids = populate_candidates(count=4, owner_user_id=sample_user.id, major='Post Graduate', university=True)

    response = get_response_from_authorized_user(user_auth, sample_user, '?major=Post Graduate')
    _assert_results(candidate_ids, response.json())


def test_search_military_service_status(sample_user, user_auth):
    """
    Test to search candidates by military service status
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, military_status="Retired")

    response = get_response_from_authorized_user(user_auth, sample_user, '?military_service_status=Retired')
    _assert_results(candidate_ids, response.json())


def test_search_military_branch(sample_user, user_auth):
    """
    Test to search candidates by military branch
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, military_branch="Army")

    response = get_response_from_authorized_user(user_auth, sample_user, '?military_branch=Army')
    _assert_results(candidate_ids, response.json())


def test_search_military_highest_grade(sample_user, user_auth):
    """
    Test to search candidates by military highest grade
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, military_grade="W-1")

    response = get_response_from_authorized_user(user_auth, sample_user, '?military_highest_grade=W-1')
    _assert_results(candidate_ids, response.json())


def to_fix_test_search_military_date_of_separation(sample_user, user_auth):
    """
    Test to search candidates by military date of separation
    :param sample_user:
    :param user_auth:
    :return:
    """
    user_id = sample_user.id
    candidates_today = populate_candidates(user_id, count=5, military_to_date=datetime.datetime.now(),
                                           military_grade=True, military_status=True, military_branch=True)
    candidates_2014 = populate_candidates(user_id, count=3, military_to_date=datetime.date(year=2014, month=03,
                                                                                                    day=31))
    candidates_2012 = populate_candidates(user_id, count=2, military_to_date=datetime.date(2012, 07, 15))

    test1_candidate_ids = candidates_2014+candidates_today

    response1 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_from=2013')
    _assert_results(test1_candidate_ids, response1.json())

    test2_candidate_ids=candidates_2012+candidates_2014 + candidates_today
    response2 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_from=2010')
    _assert_results(test2_candidate_ids, response2.json())

    test3_candidate_ids = candidates_2012+candidates_2014
    response3 = get_response_from_authorized_user(user_auth, sample_user,
                                                  '?military_end_date_from=2010&military_end_date_to=2014')
    _assert_results(test3_candidate_ids, response3.json())

    test4_candidate_ids=candidates_2012
    response4 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_to=2012')
    _assert_results(test4_candidate_ids, response4.json())

    test5_candidate_ids=candidates_2012+candidates_2014
    response5 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_to=2014')
    _assert_results(test5_candidate_ids, response5.json())


def to_fix_test_search_query_with_name(sample_user, user_auth):
    """
    Test to search candidates by passing query argument
    For example, search by querying first_name
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id,
                                        first_name="Naveen", last_name=uuid.uuid4().__str__()[0:8])

    response = get_response_from_authorized_user(user_auth, sample_user, '?q=Naveen')
    _assert_results(candidate_ids, response.json())


def test_search_get_only_requested_fields(sample_user, user_auth):
    """
    Test to search candidates and get only requested fields like email,source_id,etc,..
    :param sample_user:
    :param user_auth:
    :return:
    """
    populate_candidates(count=2, owner_user_id=sample_user.id)

    response = get_response_from_authorized_user(user_auth, sample_user, '?fields=email')
    resultant_keys = response.json()['candidates'][0].keys()
    assert len(resultant_keys) == 1
    assert 'email' in resultant_keys


def to_fix_test_search_paging(sample_user, user_auth):
    """

    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=50, owner_user_id=sample_user.id, objective=True, added_time=True,
                                        current_company=True, current_title=True, candidate_text_comment=True,
                                        city=True, state=True, phone=True,
                                        zip_code=True, university=True, major=True, degree=True,
                                        university_start_year=True,
                                        university_start_month=True, graduation_year=True, graduation_month=True,
                                        military_branch=True,
                                        military_status=True, military_grade=True,
                                        military_to_date=datetime.datetime.now())

    response1 = get_response_from_authorized_user(user_auth, sample_user, '?sort_by=added_time-asc')
    _assert_results(candidate_ids[0:15], response1.json())


def to_fix_test_search_custom_fields(sample_user, user_auth):
    """

    :param sample_user:
    :param user_auth:
    :return:
    """
    # Create custom field category named as 'Certifications'
    domain_id = sample_user.domain_id
    custom_field_cat = CustomFieldCategory(domain_id=domain_id, name="Certifications")
    db.session.add(custom_field_cat)
    custom_field_cat_id = custom_field_cat.id
    # Create custom fields under 'Certifications'
    custom_field1 = 'hadoop'
    custom_field2 = 'MongoDB'
    new_custom_field1 = CustomField(domain_id=domain_id, name=custom_field1, type='string',
                                    category_id=custom_field_cat_id, added_time=datetime.datetime.now())
    db.session.add(new_custom_field1)

    new_custom_field2 = CustomField(domain_id=domain_id, name=custom_field2, type='string',
                                    category_id=custom_field_cat_id, added_time=datetime.datetime.now())
    db.session.add(new_custom_field2)
    db.session.commit()
    custom_field1_id = new_custom_field1.id
    custom_field2_id = new_custom_field2.id
    # refresh_custom_fields_cache
    candidates_cf1 = populate_candidates(sample_user.id, count=3, custom_fields_dict={custom_field1_id: custom_field1})
    candidates_cf2 = populate_candidates(sample_user.id, count=4, custom_fields_dict={custom_field2_id: custom_field2})

    response1 = get_response_from_authorized_user(user_auth, sample_user, '?cf-%d=hadoop' % custom_field1_id)
    _assert_results(candidates_cf1, response1.json())
    response2 = get_response_from_authorized_user(user_auth, sample_user, '?cf-%d=MongoDB' % custom_field2_id)
    _assert_results(candidates_cf2, response2.json())


def _assert_results(candidate_ids, response):
    """
    Assert statements for all search results
    :param candidate_ids: list of candidate ids created by the authorized user under same domain
    :param resultant_candidates: list of candidate ids from the search results
    :return:
    """
    resultant_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
    print "response: {}".format(response)
    print 'candidate_ids: {}'.format(candidate_ids)
    print 'resultant_candidate_ids: {}'.format(resultant_candidate_ids)
    # Test whether every element in the set candidate_ids is in resultant_candidate_ids.
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def get_response_from_authorized_user(auth_user, owner_user, arguments_to_url):
    # wait for cloudsearch to update the candidates.
    time.sleep(25)
    auth_token = auth_user.get_auth_token(owner_user, get_bearer_token=True)
    response = requests.get(
        url=SEARCH_URI + arguments_to_url,
        headers={'Authorization': 'Bearer %s' % auth_token['access_token'],
                 'Content-type': 'application/json'}
    )
    return response
