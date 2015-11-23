"""
Test cases for candidate-search-service-API
"""
from candidate_service.tests.modules.test_talent_cloud_search import populate_candidates, VARIOUS_US_LOCATIONS, \
    create_area_of_interest_facets, get_or_create_status
from common.tests.conftest import *
from candidate_service.candidate_app import db
from candidate_service.common.models.candidate import Candidate, CandidateSource
from candidate_service.app.views.talent_cloud_search import upload_candidate_documents
import requests
import random
import datetime


BASE_URI = "http://127.0.0.1:8005/candidates"


def test_get_with_invalid_token():
    """
    Test to search candidates with unauthorized user
    """
    response = requests.get(BASE_URI, headers=dict(Authorization='Bearer %s' % 'invalid_token'))
    assert response.status_code == 401, 'It should be unauthorized (401)'


def test_search_all_candidates(sample_user, user_auth):
    """
    Test to search all candidates under the same domain
    :param sample_user: user to create candidates under the same domain
    :param user_auth: User Authentication
    :return:
    """
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id)
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    response = requests.get(
        url=BASE_URI,
        headers={'Authorization': 'Bearer %s' % auth_token['access_token'],
                 'Content-type': 'application/json'}
    )
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_location(sample_user, user_auth):
    """
    Test to search candidates using location
    :param sample_user: user-row
    :param user_auth: User Authentication
    :return:
    """
    city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, city=city, state=state,
                                        zip_code=zip_code)
    response = get_response_from_authorized_user(user_auth, sample_user, '?location=%s' % city)
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


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
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)
    assert len(candidate_ids) == len(resultant_candidates)


def test_search_skills(sample_user, user_auth):
    """
    Test to search all candidates based on skills
    :param sample_user: user-row
    :param user_auth: User Authentication
    :return:
    """
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id,
                                        candidate_skill_dicts=[{'description': 'hadoop', 'total_months': 36}],
                                        update_now=True)
    response = get_response_from_authorized_user(user_auth, sample_user, '?skills=hadoop')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


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
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_status(sample_user, user_auth):
    """
    Test to search all candidates by status
    :param sample_user: user-row
    :param user_auth: User Authentication
    :return:
    """
    user_id = sample_user.id
    candidate_ids = populate_candidates(count=5, owner_user_id=user_id)
    status_id = get_or_create_status(db, status_name="Hired")
    # Change status of candidate
    for candidate_id in candidate_ids:
        db.session.query(Candidate).filter_by(id=candidate_id).update(dict(candidate_status_id=status_id))
        db.session.commit()
        # Update cloud_search
        upload_candidate_documents(candidate_id)
    response = get_response_from_authorized_user(user_auth, sample_user, '?status_ids=%d' % status_id)
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_source(sample_user, user_auth):
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
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


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
    response = get_response_from_authorized_user(user_auth, sample_user, '?minimum_experience=0&maximum_experience=2')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_position(sample_user, user_auth):
    """
    Test to search candidates by job_title/position

    """
    candidate_ids = populate_candidates(count=4, owner_user_id=sample_user.id, current_title="Developer")
    response = get_response_from_authorized_user(user_auth, sample_user, '?job_title=Developer')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_degree(sample_user, user_auth):
    """
    Test to search candidates by degree type

    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, degree="Masters", university=True)
    response = get_response_from_authorized_user(user_auth, sample_user, '?degree_type=Masters')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_school_name(sample_user, user_auth):
    """
    Test to search candidates by university/school_name

    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, university='Oklahoma State University')
    response = get_response_from_authorized_user(user_auth, sample_user, '?school_name=Oklahoma State University')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_concentration(sample_user, user_auth):
    """
    Test to search candidates by higher education
    """
    candidate_ids = populate_candidates(count=4, owner_user_id=sample_user.id, major='Post Graduate', university=True)
    response = get_response_from_authorized_user(user_auth, sample_user, '?major=Post Graduate')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_military_service_status(sample_user, user_auth):
    """
    Test to search candidates by military service status
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, military_status="Retired")
    response = get_response_from_authorized_user(user_auth, sample_user, '?military_service_status=Retired')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_military_branch(sample_user, user_auth):
    """
    Test to search candidates by military branch
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, military_branch="Army")
    response = get_response_from_authorized_user(user_auth, sample_user, '?military_branch=Army')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_military_highest_grade(sample_user, user_auth):
    """
    Test to search candidates by military highest grade
    :param sample_user:
    :param user_auth:
    :return:
    """
    candidate_ids = populate_candidates(count=3, owner_user_id=sample_user.id, military_grade="W-1")
    response = get_response_from_authorized_user(user_auth, sample_user, '?military_highest_grade=W-1')
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)


def test_search_military_date_of_separation(sample_user, user_auth):
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
    resultant_candidates = response1.json()['candidate_ids']
    _assert_results(test1_candidate_ids, resultant_candidates)

    test2_candidate_ids=candidates_2012+candidates_2014 + candidates_today
    response2 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_from=2010')
    resultant_candidates = response2.json()['candidate_ids']
    _assert_results(test2_candidate_ids, resultant_candidates)

    test3_candidate_ids=candidates_2012+candidates_2014
    response3 = get_response_from_authorized_user(user_auth, sample_user,
                                                  '?military_end_date_from=2010&military_end_date_to=2014')
    resultant_candidates = response3.json()['candidate_ids']
    _assert_results(test3_candidate_ids, resultant_candidates)

    test4_candidate_ids=candidates_2012
    response4 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_to=2012')
    resultant_candidates = response4.json()['candidate_ids']
    _assert_results(test4_candidate_ids, resultant_candidates)

    test5_candidate_ids=candidates_2012+candidates_2014
    response5 = get_response_from_authorized_user(user_auth, sample_user, '?military_end_date_to=2014')
    resultant_candidates = response5.json()['candidate_ids']
    _assert_results(test5_candidate_ids, resultant_candidates)


def test_search_query_with_name(sample_user, user_auth):
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
    resultant_candidates = response.json()['candidate_ids']
    _assert_results(candidate_ids, resultant_candidates)
    assert response.status_code == 200


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


def _assert_results(candidate_ids, resultant_candidates):
    """
    Assert statements for all search results
    :param candidate_ids: list of candidate ids created by the authorized user under same domain
    :param resultant_candidates: list of candidate ids from the search results
    :return:
    """
    resultant_candidate_ids = map(lambda x: long(x), resultant_candidates)
    print candidate_ids
    print resultant_candidate_ids
    # Test whether every element in the set candidate_ids is in resultant_candidate_ids.
    assert set(candidate_ids).issubset(resultant_candidate_ids)


def get_response_from_authorized_user(auth_user, owner_user, arguments_to_url):
    auth_token = auth_user.get_auth_token(owner_user, get_bearer_token=True)
    response = requests.get(
        url=BASE_URI + arguments_to_url,
        headers={'Authorization': 'Bearer %s' % auth_token['access_token'],
                 'Content-type': 'application/json'}
    )
    return response