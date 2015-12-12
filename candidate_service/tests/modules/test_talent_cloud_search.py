"""
Test cases for Talent Cloud Search functionality
"""
from candidate_service.common.tests.conftest import *
from candidate_service.common.models.candidate import (Candidate, CandidateAddress, CandidateStatus, CandidateSource)
from candidate_service.candidate_app import db, logger
from candidate_service.common.models.misc import CustomField, CustomFieldCategory, AreaOfInterest
from flask.ext.common.common.geo_services.geo_coordinates import get_geocoordinates_bounding
from candidate_service.cloudsearch_constants import SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH
from faker import Faker
from random import randint
import datetime
import time


fake = Faker()

# Various U.S. locations in (city, state, zipcode) format, which can be used to populate candidate locations
VARIOUS_US_LOCATIONS = (('San Jose', 'CA', '95132'), ('Providence', 'Rhode Island', '02905'),
                        ('Lubbock', 'Texas', '79452'), ('Philadelphia', 'Pennsylvania', '19184'),
                        ('Delray Beach', 'Florida', '33448'), ('Houston', 'Texas', '77080'),
                        ('Boston', 'Massachusetts', '02163'), ('Fairbanks', 'Alaska', '99709'),
                        ('Los Angeles', 'California', '90087'), ('Clearwater', 'Florida', '34615'),
                        ('Seattle', 'Washington', '98158'))


def populate_candidates(owner_user_id, count=1, first_name=True, middle_name=False,last_name=True, added_time=True, objective=False,
                        phone=False, current_company=False, current_title=False, candidate_text_comment=False,
                        source_id=None, city=False, state=False, zip_code=False, area_of_interest_ids=None,
                        university=False, major=False, degree=False, university_start_year=False,
                        university_start_month=False, graduation_year=False, graduation_month=False,
                        military_branch=False, military_status=False, military_grade=False, military_to_date=False,
                        military_from_date=False, candidate_skill_dicts=None, custom_fields_dict=None,
                        candidate_experience_dicts=None, update_now=True):
    """
    :param count:
    :param owner_user_id:
    :param first_name:
    :type first_name: bool | str
    :param middle_name:
    :type middle_name: bool | str
    :param last_name:
    :type last_name: bool | str
    :param added_time:
    :type added_time: bool | datetime.date
    :param objective:
    :type objective: bool | str
    :param phone:
    :param current_company:
    :type current_company: bool | str
    :param current_title:
    :type current_title: bool | str
    :param candidate_text_comment:
    :type candidate_text_comment: bool | str
    :param source_id:
    :type source_id: None | int
    :param city:
    :type city: bool | str
    :param state:
    :type state: bool | str
    :param zip_code:
    :type zip_code: bool | str | long
    :param area_of_interest_ids: List of areas of interest ids
    :type area_of_interest_ids: None | list[int]
    :param university:
    :type university: bool | str
    :param major:
    :type major: bool | str
    :param degree:
    :type degree: bool | str
    :param university_start_year:
    :param university_start_month:
    :param graduation_year:
    :param graduation_month:
    :param military_branch:
    :type military_branch: bool | str
    :param military_status:
    :type military_status: bool | str
    :param military_grade:
    :type military_grade: bool | str
    :param military_to_date:
    :type military_to_date: datetime.date
    :param military_from_date:
    :type military_from_date: datetime.date
    :param candidate_skill_dicts
    :type candidate_skill_dicts: None | list[dict[basestring, basestring | integer | datetime.date]]
    :param custom_fields_dict: custom_field_id -> value
    :type custom_fields_dict: dict[int, str] | None
    :param candidate_experience_dicts: dicts of organization, position, startMonth, startYear, endMonth, endYear,
    isCurrent
    :type candidate_experience_dicts: None | list[dict[basestring, int | basestring | list]]
    :param update_now: Will update immediately after creating all candidates. Set it to False, if willing to create
    different combination of candidates and update at last to save time.
    :return:
    """
    candidate_ids = []
    work_experiences = {}
    addresses = {}
    educations = {}
    email_address = {}
    military_services = {}
    degree_dict = {}
    degree_bullets_dict = {}
    aoi_ids = list()
    custom_fields_list = list()

    for i in range(count):
        data = {
            'id': 'Not yet assigned',
            'first_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(first_name, first_name),
            'middle_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(middle_name, middle_name),
            'last_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(last_name, last_name),
            'added_time': {True: datetime.datetime.now(), False: None}.get(added_time, added_time),
            'email': '%s@candidate.example.com' % (uuid.uuid4().__str__()),
            'objective': {True: uuid.uuid4().__str__()[0:8], False: None}.get(objective, objective),
            'candidate_text_comment': {True: '\n'.join(fake.sentences()), False: None}.get(
                candidate_text_comment, candidate_text_comment),
            'city': {True: VARIOUS_US_LOCATIONS[0][0], False: None}.get(city, city),
            'state': {True: VARIOUS_US_LOCATIONS[0][1], False: None}.get(state, state),
            'zip_code': {True: VARIOUS_US_LOCATIONS[0][2], False: None}.get(zip_code, zip_code),
            'current_company': {True: uuid.uuid4().__str__()[0:8], False: None}.get(current_company, current_company),
            'current_title': {True: uuid.uuid4().__str__()[0:8], False: None}.get(current_title, current_title),
            'university': {True: uuid.uuid4().__str__()[0:8], False: None}.get(university, university),
            'major_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(major, major),
            'degree': {True: uuid.uuid4().__str__()[0:8], False: None}.get(degree, degree),
            'military_branch': {True: uuid.uuid4().__str__()[0:8], False: None}.get(military_branch, military_branch),
            'military_status': {True: uuid.uuid4().__str__()[0:8], False: None}.get(military_status, military_status),
            'military_grade': {True: uuid.uuid4().__str__()[0:8], False: None}.get(military_grade, military_grade),
            'military_from_date': {True: datetime.datetime.strptime(fake.date(), "%Y-%m-%d"), False: None}.get(military_from_date, military_from_date),
            'military_to_date': {True: datetime.datetime.today(), False: None}.get(military_to_date, military_to_date),
            'source_id': source_id,
            'area_of_interest_ids': area_of_interest_ids,
            'candidate_skill_dicts': candidate_skill_dicts,
            'custom_fields_dict': custom_fields_dict,
            'candidate_experience_dicts': candidate_experience_dicts,
        }

        if data['email']:
            email_address['address'] = data['email']
        if data['current_company'] or data['current_title']:
            work_experiences['organization'] = data['current_company']
            work_experiences['position'] = data['current_title']
        if data['city'] or data['state'] or data['zip_code']:
            addresses['city'] = data['city']
            addresses['state'] = data['state']
            addresses['zip_code'] = data['zip_code']
        if data['university'] or data['degree'] or data['major_name']:
            educations['school_name'] = data['university']
            degree_dict['type'] = data['degree']
            educations['degrees'] = [degree_dict]
            degree_bullets_dict['major'] = data['major_name']
            degree_dict['degree_bullets'] = [degree_bullets_dict]
        if data['military_branch'] or data['military_status'] or data['military_grade']:
            military_services['service_status'] = data['military_status']
            military_services['branch'] = data['military_branch']
            military_services['highest_grade'] = data['military_grade']
            military_services['from_date'] = data['military_from_date']
            military_services['to_date'] = data['military_to_date']
            military_services['highest_rank'] = randint(0, 3)
        if data['area_of_interest_ids']:
            aoi_ids = [{"area_of_interest_id": aoi_id} for aoi_id in data['area_of_interest_ids']]
        if data['custom_fields_dict']:
            custom_fields_list.append(data['custom_fields_dict'])

        candidate = create_or_update_candidate_from_params(
            owner_user_id,
            is_creating=True,
            first_name=data['first_name'],
            middle_name=data['middle_name'],
            last_name=data['last_name'],
            added_time=data['added_time'],
            objective=data['objective'],
            emails=[email_address],
            work_experiences=[work_experiences] if work_experiences else None,
            source_id=data['source_id'],
            addresses=[addresses] if addresses else None,
            educations=[educations] if educations else None,
            areas_of_interest=aoi_ids,
            military_services=[military_services] if military_services else None,
            skills=data['candidate_skill_dicts'],
            custom_fields=custom_fields_list
            # major=data['major_name'],
            # candidate_experience_dicts=data['candidate_experience_dicts'],
            )
        candidate_ids.append(candidate['candidate_id'])

    if update_now:
        # Update cloud_search
        upload_candidate_documents(candidate_ids)
    return candidate_ids


def _update_now(candidate_ids):
    """
    If update_now is set to False in populate_candidates function, then call this function to update them all at once.
    :param candidate_ids: list of candidate ids to sent to cloud_search to update candidate.
    :return:
    """
    # Update cloud_search
    upload_candidate_documents(candidate_ids)
    return


def get_source_product_id(candidate_ids):
    source_product_id = []
    for candidate_id in candidate_ids:
        candidate_row = Candidate.query.filter_by(id=candidate_id).one()
        source_product_id.append(candidate_row.source_product_id)
    return source_product_id


def test_search_all_candidates_in_domain(sample_user):
    """
    Test search functionality should return all inserted candidates for domain
    :param sample_user:
    :return:
    """
    candidate_ids = populate_candidates(count=2, owner_user_id=sample_user.id, first_name=True, last_name=True)
    _assert_search_results(sample_user.domain_id, {'query': ''}, candidate_ids)


def test_search_by_first_name(sample_user):
    """
    Test search candidates by first name
    :param sample_user:
    :return:
    """
    # Create candidate with first name and last name
    first_name = 'Marilyn'
    candidate_ids = populate_candidates(owner_user_id=sample_user.id, first_name=first_name, last_name=True)
    _assert_search_results(sample_user.domain_id, {'query': first_name}, candidate_ids)


def test_search_by_last_name(sample_user):
    """
    Test to search candidates by last name
    :param sample_user:
    :return:
    """
    last_name = 'Lynn'
    # Create candidate with last name
    candidate_ids = populate_candidates(owner_user_id=sample_user.id, last_name=last_name)
    _assert_search_results(sample_user.domain_id, {'query': last_name}, candidate_ids)


def test_search_by_current_company(sample_user):
    """
    Test to search candidates by current company
    :param sample_user:
    :return:
    """
    company_name = "Google"
    candidate_ids = populate_candidates(count=5, owner_user_id=sample_user.id, objective=True, phone=True,
                                        current_company=company_name)
    _assert_search_results(sample_user.domain_id, {'query': company_name}, candidate_ids, check_for_equality=True)


def test_search_by_position_facet(sample_user):
    """
    Test to search candidates by position
    :param sample_user:
    :return:
    """
    current_title = "Senior Developer"
    candidate_ids = populate_candidates(count=12, owner_user_id=sample_user.id, objective=True, phone=True,
                                        current_company=True, current_title=current_title)
    _assert_search_results(sample_user.domain_id, {'positionFacet': current_title}, candidate_ids)


def test_position_and_company(sample_user):
    """
    Test to search candidates by position and company
    :param sample_user:
    :return:
    """
    company = "Apple"
    position = "CEO"
    # 10 other candidates at apple
    populate_candidates(count=10, owner_user_id=sample_user.id, current_company=company, current_title=True)
    ceo_at_apple = populate_candidates(count=1, owner_user_id=sample_user.id, current_company=company,
                                       current_title=position)
    # Query for company Apple and position CEO, it should only return 1 candidate although Apple has 10 other employees
    search_vars = {'query': company, 'job_title': position}
    _assert_search_results(sample_user.domain_id, search_vars, ceo_at_apple, check_for_equality=True)


def test_owner_facet(test_domain, sample_user, sample_user_2):
    """
    Search by username
    :param test_domain:
    :param sample_user:
    :param sample_user_2:
    :return:
    """
    domain_id = test_domain.id
    # Populate 8 candidates for user_manager
    user1_candidates = populate_candidates(count=8, owner_user_id=sample_user.id, current_company=True,
                                           current_title=True, update_now=False)
    # Populate 4 candidates for passive user
    user2_candidates = populate_candidates(count=4, owner_user_id=sample_user_2.id, current_company=True,
                                           current_title=True, update_now=False)
    total_candidates = user1_candidates + user2_candidates
    _update_now(total_candidates)
    # Search for user_manager_candidates
    _assert_search_results(domain_id, {'user_ids': sample_user.id}, user1_candidates, check_for_equality=True)
    # Search for normal user candidates
    _assert_search_results(domain_id, {'user_ids': sample_user_2.id}, user2_candidates, check_for_equality=True,
                           wait=False)
    # All 8+4 = 12 candidates should appear in search if searched by both users
    _assert_search_results(domain_id, {'user_ids': [sample_user.id, sample_user_2.id]}, total_candidates,
                           check_for_equality=True, wait=False)


def OK_test_sort_by_match(sample_user):
    """
    TODO: Remove OK_ in name once comments in candidates creation is fixed.
    """
    candidate1 = populate_candidates(owner_user_id=sample_user.id, current_company="Newvision", update_now=False)
    candidate2 = populate_candidates(owner_user_id=sample_user.id, current_company="Newvision", objective="Willing to join Newvision",
                                     update_now=False)
    candidate3 = populate_candidates(owner_user_id=sample_user.id, current_company="Newvision", objective="Willing to join Newvision",
                                     candidate_text_comment="Eligible for joining Newvision", update_now=False)
    worst_match_order = candidate1+candidate2+candidate3
    best_match_order = worst_match_order[::-1]
    _update_now(worst_match_order)
    # search for Newvision - worst-match
    worst_match = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~match']
    _assert_search_results(sample_user.domain_id, {'query': 'Newvision', 'sort_by': worst_match}, worst_match_order,
                           check_for_sorting=True)
    # search for Newvision - Best match
    best_match = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['match']
    _assert_search_results(sample_user.domain_id, {'query': 'Newvision', 'sort_by': best_match}, best_match_order,
                           check_for_sorting=True)


def test_search_by_university(sample_user):
    """
    university > school_name
    :param sample_user:
    :return:
    """

    university1 = 'University Of Washington'
    university2 = 'Oklahoma State University'
    university1_candidates = populate_candidates(owner_user_id=sample_user.id, university=university1)
    # Create other candidates with other university, check
    university2_candidates = populate_candidates(count=2, owner_user_id=sample_user.id, university=university2)
    _assert_search_results(sample_user.domain_id, {'school_name': university1}, university1_candidates)
    total_candidates = university1_candidates + university2_candidates
    _assert_search_results(sample_user.domain_id, {'school_name': [university1, university2]},
                           total_candidates, wait=False)
    # Select owner facet + both universities should return all candidates in domain
    _assert_search_results(sample_user.domain_id, {'school_name': [university1, university2],
                                                   'user_ids': sample_user.id}, total_candidates, wait=False)


def test_search_by_location(sample_user):
    """
    Search by City name, State name
    :param sample_user:
    :return:
    """

    city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
    candidate_ids = populate_candidates(count=2, owner_user_id=sample_user.id, city=city, state=state,
                                        zip_code=zip_code)
    # With city and state only
    _assert_search_results(sample_user.domain_id, {'location': '%s, %s' % (city, state)}, candidate_ids)
    # With city, state and zip
    _assert_search_results(sample_user.domain_id, {'location': '%s, %s, %s' % (city, state, zip_code)}, candidate_ids,
                           wait=False)
    # With zipcode only
    _assert_search_results(sample_user.domain_id, {'location': '%s' % zip_code}, candidate_ids, wait=False)


def test_location_with_radius(sample_user):
    """
    Search by city, state + radius
    Search by zip + radius
    Distance in miles
    Ref: http://www.timeanddate.com/worldclock/distances.html?n=283
    :param sample_user:
    :return:
    """
    base_location = "San Jose, CA, 95113"                                             # distance from san jose, in miles
    location_within_10_miles = {"city": "Santa Clara", "state": "CA", "zip_code": "95050"}       # 4.8
    location_within_10_miles_2 = {"city": "Milpitas", "state": "CA", "zip_code": "95035"}        # 7.9
    location_within_25_miles = {"city": "Newark", "state": "CA", "zip_code": "94560"}            # 19.2
    location_within_25_miles_2 = {"city": "Stanford", "state": "CA", "zip_code": "94305"}        # 22.3
    location_within_50_miles = {"city": "Oakland", "state": "CA", "zip_code": "94601"}           # 38
    location_within_75_miles = {"city": "Novato", "state": "CA", "zip_code": "94945"}            # 65
    location_within_100_miles = {'city': 'Sacramento', "state": "CA", "zip_code": "95405"}       # 89
    location_more_than_100_miles = {'city': "Oroville", "state": "CA", "zip_code": "95965"}      # 151
    # 10 mile candidates with city & state
    _10_mile_candidate = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_10_miles)
    _10_mile_candidate_2 = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_10_miles_2)
    # 25 mile candidates with city state
    _25_mile_candidate = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_25_miles)
    _25_mile_candidate_2 = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_25_miles_2)
    _50_mile_candidate = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_50_miles)
    _75_mile_candidate = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_75_miles)
    _100_mile_candidate = populate_candidates(owner_user_id=sample_user.id, update_now=False, **location_within_100_miles)
    # The following candidate will not appear in search with radius
    _more_than_100_mile_candidate = populate_candidates(owner_user_id=sample_user.id, update_now=False,
                                                        **location_more_than_100_miles)

    candidates_within_10_miles = _10_mile_candidate + _10_mile_candidate_2
    candidates_within_25_miles = candidates_within_10_miles + _25_mile_candidate + _25_mile_candidate_2
    candidates_within_50_miles = candidates_within_25_miles + _50_mile_candidate
    candidates_within_75_miles = candidates_within_50_miles + _75_mile_candidate
    candidates_within_100_miles = candidates_within_75_miles + _100_mile_candidate
    all_candidates = candidates_within_100_miles + _more_than_100_mile_candidate

    # Update database and cloudsearch now.
    _update_now(all_candidates)

    # All candidates in domain; it will include more_than_100_mile_candidate also,
    # which will not appear in other searches with radius.
    _assert_search_results(sample_user.domain_id, {'location': ''},
                           candidate_ids=all_candidates)
    # With city, state and radius within 10 miles

    _assert_search_results(sample_user.domain_id, {'location': base_location, 'radius': 10},
                           candidate_ids=candidates_within_10_miles,
                           check_for_equality=True, wait=False)
    # Search with zipcode within 10 miles
    _assert_search_results(sample_user.domain_id, {'location': base_location.split()[-1], 'radius': 10},
                           candidate_ids=candidates_within_10_miles,
                           check_for_equality=True, wait=False)
    # With city, state and radius within 25 miles
    _log_bounding_box_and_coordinates(base_location, 25, candidates_within_25_miles)
    _assert_search_results(sample_user.domain_id, {'location': base_location, 'radius': 25},
                           candidate_ids=candidates_within_25_miles,
                           check_for_equality=True, wait=False)
    # default radius is 50 miles; search for 50 miles radius
    _log_bounding_box_and_coordinates(base_location, 50, candidates_within_50_miles)
    _assert_search_results(sample_user.domain_id, {'location': base_location, 'radius': 50},
                           candidate_ids=candidates_within_50_miles,
                           check_for_equality=True, wait=False)
    # 75 miles
    _log_bounding_box_and_coordinates(base_location, 75, candidates_within_75_miles)
    _assert_search_results(sample_user.domain_id, {'location': base_location, 'radius': 75},
                           candidate_ids=candidates_within_75_miles,
                           check_for_equality=True, wait=False)
    # 100 miles
    _log_bounding_box_and_coordinates(base_location, 100, candidates_within_100_miles)
    _assert_search_results(sample_user.domain_id, {'location': base_location, 'radius': 100},
                           candidate_ids=candidates_within_100_miles,
                           check_for_equality=True, wait=False)


def test_sort_by_proximity(sample_user):
    """
    Sort by distance
    :param sample_user:
    :return:
    """
    user_id = sample_user.id
    domain_id = sample_user.domain_id
    base_location = "San Jose, CA"                                                    # distance from san jose, in miles
    location_within_10_miles = {"city": "Santa Clara", "state": "CA", "zip_code": "95050"}       # 4.8
    location_within_10_miles_2 = {"city": "Milpitas", "state": "CA", "zip_code": "95035"}        # 7.9
    location_within_25_miles = {"city": "Fremont", "state": "CA", "zip_code": "94560"}           # 16
    location_within_50_miles = {"city": "Oakland", "state": "CA", "zip_code": "94601"}           # 38

    # 10 mile candidates with city & state
    _10_mile_candidate = populate_candidates(owner_user_id=user_id, update_now=False, **location_within_10_miles)
    _10_mile_candidate_2 = populate_candidates(owner_user_id=user_id, update_now=False, **location_within_10_miles_2)
    # 25 mile candiates with city state
    _25_mile_candidate = populate_candidates(owner_user_id=user_id, update_now=False, **location_within_25_miles)
    _50_mile_candidate = populate_candidates(owner_user_id=user_id, update_now=False, **location_within_50_miles)
    candidates_within_10_miles = [_10_mile_candidate[0], _10_mile_candidate_2[0]]
    closest_to_furthest = [_10_mile_candidate[0], _10_mile_candidate_2[0], _25_mile_candidate[0], _50_mile_candidate[0]]
    # Update database and cloud_search
    _update_now(closest_to_furthest)
    furthest_to_closest = closest_to_furthest[::-1]  # Reverse the order

    # Without radius i.e. it will by default take 50 miles
    # Sort by -> Proximity: Closest
    proximity_closest = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['proximity']
    _assert_search_results(domain_id, {'location': base_location, 'sort_by': proximity_closest},
                           candidate_ids=closest_to_furthest, check_for_sorting=True)

    # Sort by -> Proximity: Furthest
    proximity_furthest = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~proximity']
    _assert_search_results(domain_id, {'location': base_location, 'sort_by': proximity_furthest},
                           candidate_ids=furthest_to_closest, check_for_sorting=True,  wait=False)

    # With city, state and radius within 10 miles. Sort by -> Proximity: closest
    _assert_search_results(domain_id, {'location': base_location, 'radius': 10, 'sort_by': proximity_closest},
                           candidate_ids=candidates_within_10_miles,
                           check_for_sorting=True, wait=False)

    # With city, state and radius within 10 miles. Sort by -> Proximity: Furthest
    _assert_search_results(domain_id, {'location': base_location, 'radius': 10, 'sort_by': proximity_furthest},
                           candidate_ids=candidates_within_10_miles[::-1],
                           check_for_sorting=True, wait=False)


def to_fix_test_search_by_major(sample_user):
    """
    Test to search based on major facet
    Without university major doesn't gets created in database, So university should also be created for major
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    major1 = 'Electrical Engineering'
    major2 = 'Computer Science'
    major1_candidates = populate_candidates(count=2, owner_user_id=sample_user.id, major=major1,
                                            university=True, update_now=False)
    major2_candidates = populate_candidates(count=7, owner_user_id=sample_user.id, major=major2,
                                            university=True, update_now=False)
    _update_now(major1_candidates + major2_candidates)
    _assert_search_results(domain_id, {'major': major1}, major1_candidates)
    _assert_search_results(domain_id, {'major': major2}, major2_candidates, wait=False)
    # major is an 'and' query so no list? Below query will not give any result
    # TODO: Check if major will be 'and query' or 'or query'


def test_search_by_degree(sample_user):
    """
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    degree1 = 'Masters'
    degree2 = 'Bachelors'
    master_candidates = populate_candidates(count=3, owner_user_id=sample_user.id, degree=degree1,
                                            university=True, update_now=False)
    bachelor_candidates = populate_candidates(count=4, owner_user_id=sample_user.id, degree=degree2,
                                              university=True, update_now=False)
    all_candidates = master_candidates + bachelor_candidates
    _update_now(all_candidates)
    _assert_search_results(domain_id, {'degree_type': degree1}, master_candidates)
    _assert_search_results(domain_id, {'degree_type': degree2}, bachelor_candidates, wait=False)
    _assert_search_results(domain_id, {'degree_type': [degree2, degree1]},
                           all_candidates, wait=False)


def test_search_by_added_date(sample_user):
    """
    Test to search candidates by added time
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    # Candidate added on 01 Dec 2014 at 14:30:00
    candidate1 = populate_candidates(count=3, owner_user_id=sample_user.id,
                                     added_time=datetime.datetime(2014, 12, 01, 14, 30, 00), update_now=False)
    # Candidate added on 20 Mar 2015 at 10:00:00
    candidate2 = populate_candidates(count=3, owner_user_id=sample_user.id,
                                     added_time=datetime.datetime(2015, 03, 20, 10, 00, 00), update_now=False)
    # Candidate added on 25 May 2010 at 00:00:00
    candidate3 = populate_candidates(count=3, owner_user_id=sample_user.id,
                                     added_time=datetime.datetime(2010, 05, 25, 00, 00, 00), update_now=False)
    # Candidate added today (now)
    candidate4 = populate_candidates(sample_user.id, added_time=datetime.datetime.now(), update_now=False)
    _update_now(candidate1+candidate2+candidate3+candidate4)
    # Get candidates from within range 1 jan'14 to 30 May'15 (format mm/dd/yyyy) -> Will include candidates 1 & 2
    _assert_search_results(domain_id, {'date_from': '01/01/2014', 'date_to': '05/30/2015'},
                           candidate_ids=candidate1+candidate2)
    # Get candidates from starting date as 15 Mar 2015 and without end date -> will include candidates- 2, 4
    _assert_search_results(domain_id, {'date_from': '03/15/2015', 'date_to': ''},
                           candidate_ids=candidate2+candidate4, wait=False)
    # Get candidates from no starting date but ending date as 31 Dec 2014 -> will give candidates 1 & 3
    _assert_search_results(domain_id, {'date_from': '', 'date_to': '12/31/2014'},
                           candidate_ids=candidate1+candidate3, wait=False)
    # Get candidates from no starting and no ending date i.e. all candidates
    _assert_search_results(domain_id, {'date_from': '', 'date_to': ''},
                           candidate_ids=candidate1+candidate2+candidate3+candidate4, wait=False)


def to_fix_test_sort_by_added_date(sample_user):
    """
    Least recent --> sort_by:added_time-asc
    Most recent -->  sort_by:added_time-desc
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    # Candidate added on 25 May 2010 at 00:00:00
    candidate1 = populate_candidates(owner_user_id=sample_user.id, added_time=datetime.datetime(2010, 05, 25, 00, 00, 00),
                                     update_now=False)
    # Candidate added on 01 Dec 2014 at 14:30:00
    candidate2 = populate_candidates(owner_user_id=sample_user.id, added_time=datetime.datetime(2014, 12, 01, 14, 30, 00),
                                     update_now=False)
    # Candidate added on 20 Mar 2015 at 10:00:00
    candidate3 = populate_candidates(owner_user_id=sample_user.id, added_time=datetime.datetime(2015, 03, 20, 10, 00, 00),
                                     update_now=False)
    # Candidate added today (now)
    candidate4 = populate_candidates(owner_user_id=sample_user.id, added_time=datetime.datetime.now(), update_now=False)
    sorted_in_ascending_order_of_added_time = candidate1+candidate2+candidate3+candidate4
    _update_now(sorted_in_ascending_order_of_added_time)
    sorted_in_descending_order_of_added_time = sorted_in_ascending_order_of_added_time[::-1]
    # check for order in which candiate were added. Sort by Date: Most recent - all candidates
    most_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['recent']
    _assert_search_results(domain_id, {'sort_by': most_recent},
                           candidate_ids=sorted_in_descending_order_of_added_time, check_for_sorting=True)
    # Sort by Date: Least recent - all candidates
    least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
    _assert_search_results(domain_id, {'sort_by': least_recent},
                           candidate_ids=sorted_in_ascending_order_of_added_time,
                           check_for_sorting=True, wait=False)
    # Get candidates from within range 1 jan'14 to 30 May'15 -> Will include candidates 3rd & 2nd in descending order
    _assert_search_results(domain_id, {'date_from': '01/01/2014', 'date_to': '05/30/2015',
                                       'sort_by': most_recent}, candidate_ids=candidate3+candidate2,
                           wait=False)


def to_fix_test_area_of_interest_facet(sample_user):
    """
    Test areaOfInterestIdFacet by passing aoi values as list and as single select
    areaOfInterestIdFacet:<id>
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    all_aoi_ids = create_area_of_interest_facets(db, domain_id)
    print "Total area of interest facets present: %s" % len(all_aoi_ids)
    aoi_ids_list_1 = all_aoi_ids[0:5]
    aoi_ids_list_2 = all_aoi_ids[-4:-1]
    candidate1 = populate_candidates(owner_user_id=sample_user.id, area_of_interest_ids=aoi_ids_list_1, update_now=False)
    candidate2 = populate_candidates(owner_user_id=sample_user.id, area_of_interest_ids=aoi_ids_list_2, update_now=False)
    _update_now(candidate1+candidate2)
    _assert_search_results(domain_id, {"area_of_interest_ids": ','.join(aoi_ids_list_1[0:3])}, candidate1,
                           check_for_equality=True, wait=False)
    _assert_search_results(domain_id, {"area_of_interest_ids": ','.join(aoi_ids_list_2[0])}, candidate2,
                           check_for_equality=True, wait=False)
    _assert_search_results(domain_id, {"area_of_interest_ids": ','.join([aoi_ids_list_2[-1], aoi_ids_list_1[-2]])},
                           candidate1+candidate2,
                           check_for_equality=True, wait=False)


def to_fix_test_status_facet(sample_user):
    """
    Test with status facet by passing value as list and single value
    statusFacet: <status_id>
    :param sample_user:
    :return:
    """

    domain_id = sample_user.domain_id
    # By default every candidate has "New" status
    candidate1 = populate_candidates(owner_user_id=sample_user.id)
    candidate2 = populate_candidates(owner_user_id=sample_user.id)
    candidate3 = populate_candidates(owner_user_id=sample_user.id)
    new_status_id = get_or_create_status(db, status_name="New")
    _assert_search_results(domain_id, {'status': new_status_id}, candidate1+candidate2+candidate3)
    status1_id = get_or_create_status(db, status_name="Qualified")
    status2_id = get_or_create_status(db, status_name="Hired")
    # Change status of candidate1
    db.session.query(Candidate).filter_by(id=candidate1[0]).update(dict(candidate_status_id=status1_id))
    db.session.query(Candidate).filter_by(id=candidate2[0]).update(dict(candidate_status_id=status2_id))
    # Update cloud_search for status changes
    _update_now(candidate1+candidate2)
    # search for qualified candidates
    _assert_search_results(domain_id, {'status_ids': str(status1_id)}, candidate1, check_for_equality=True)
    _assert_search_results(domain_id, {'status_ids': str(status2_id)}, candidate2, check_for_equality=True, wait=False)
    _assert_search_results(domain_id, {'status_ids': ','.join([status1_id, status2_id])}, candidate2+candidate1,
                           check_for_equality=True, wait=False)
    _assert_search_results(domain_id, {'status_ids': str(new_status_id)}, candidate3, check_for_equality=True, wait=False)


def to_fix_test_source_facet(sample_user):
    """
    Test search filter for various available source facets.
    sourceFacet:<source id>
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    # by default all candidates have "Unassigned" source
    candidate_ids1 = populate_candidates(owner_user_id=sample_user.id, count=5, update_now=False)
    # Create a new source
    source_id = CandidateSource(description="Test source-%s" % uuid.uuid4().__str__()[0:8],
                                domain_id=domain_id, notes="Source created for functional tests")
    db.session.add(source_id)
    db.session.commit()
    candidate_ids2 = populate_candidates(owner_user_id=sample_user.id, count=5, source_id=source_id, update_now=False)
    # Update database and cloud_search
    all_candidates = candidate_ids1+candidate_ids2
    _update_now(all_candidates)
    # Search for candidates with created source, it will not include candidates with unassigned source
    _assert_search_results(domain_id, {"source_ids": str(source_id)}, candidate_ids2, check_for_equality=True)


def test_search_based_on_years_of_experience(sample_user):
    """
    minimum_years_experience
    maximum_years_experience
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    experience_above_10_years = [{'organization': 'Amazon', 'position': 'Software Architect', 'startYear': 2014,
                                  'startMonth': '09', 'isCurrent': True},
                                 {'organization': 'Amazon', 'position': 'Sr. Software Developer',
                                  'startYear': '2008', 'startMonth': '04',
                                  'endYear': 2014, 'endMonth': '08'},
                                 {'organization': 'Amazon', 'position': 'Software Developer', 'startYear': 2004,
                                  'startMonth': '03', 'endYear': 2008, 'endMonth': '03',
                                  'candidate_experience_bullets': [{'description':
                                                                        'Developed An Online Complaint And Resolution '
                                                                        'Database System In Perl Under The Instruction '
                                                                        'Of Professor Brian Harvey For Students In '
                                                                        'Computer Science Classes. Various System '
                                                                        'Administration And Maintenance Tasks.'}]}]
    experience_5_years = [{'organization': 'Samsung', 'position': 'Area Manager', 'startYear': 2013, 'startMonth': 06,
                           'endYear': 2015, 'endMonth': '01'},
                          {'organization': 'Motorola', 'position': 'Area Manager', 'startYear': 2011, 'startMonth': 11,
                           'endYear': 2013, 'endMonth': '05'},
                          {'organization': 'Nokia', 'position': 'Marketing executive', 'startYear': 2010,
                           'startMonth': '01', 'endYear': 2011, 'endMonth': '10'}]  # 60 months exp
    experience_2_years = [{'organization': 'Intel', 'position': 'Research analyst', 'startYear': 2013, 'startMonth': 06,
                           'endYear': 2015, 'endMonth': '06'}]  # 24 months exp
    experience_0_years = [{'organization': 'Audi', 'position': 'Mechanic', 'startYear': 2015, 'startMonth': 01,
                           'endYear': 2015, 'endMonth': 02}]  # 2 month exp
    candidate_with_0_years_exp = populate_candidates(owner_user_id=sample_user.id, candidate_experience_dicts=experience_0_years,
                                                     update_now=False)
    candidate_with_2_years_exp = populate_candidates(owner_user_id=sample_user.id, candidate_experience_dicts=experience_2_years,
                                                     update_now=False)
    candidate_with_5_years_exp = populate_candidates(owner_user_id=sample_user.id, candidate_experience_dicts=experience_5_years,
                                                     update_now=False)
    candidate_above_10_years_exp = populate_candidates(owner_user_id=sample_user.id,
                                                       candidate_experience_dicts=experience_above_10_years,
                                                       update_now=False)
    # TODO: Check if there is still need of updating total_months_experience?
    db.session.commit()
    db.session.query(Candidate).filter_by(id=candidate_with_0_years_exp[0]).update(dict(total_months_experience=2))
    db.session.query(Candidate).filter_by(id=candidate_with_2_years_exp[0]).update(dict(total_months_experience=24))
    db.session.query(Candidate).filter_by(id=candidate_with_5_years_exp[0]).update(dict(total_months_experience=5*12))
    db.session.query(Candidate).filter_by(id=candidate_above_10_years_exp[0]).update(dict(total_months_experience=11*12))
    # Update cloudsearch
    all_candidates = candidate_with_0_years_exp+candidate_with_2_years_exp+candidate_with_5_years_exp + \
        candidate_above_10_years_exp
    _update_now(all_candidates)

    # Search for candidates with more than 10 years
    _assert_search_results(domain_id, {"minimum_years_experience": 10}, candidate_above_10_years_exp)
    _assert_search_results(domain_id, {"minimum_years_experience": 1, "maximum_years_experience": 6},
                           candidate_with_2_years_exp+candidate_with_5_years_exp, wait=False)
    _assert_search_results(domain_id, {"maximum_years_experience": 4}, candidate_with_0_years_exp +
                           candidate_with_2_years_exp, wait=False)
    _assert_search_results(domain_id, {"minimum_years_experience": "", "maximum_years_experience": ""},
                           candidate_with_0_years_exp+candidate_with_2_years_exp+candidate_with_5_years_exp +
                           candidate_above_10_years_exp,
                           wait=False)


def test_skill_description_facet(sample_user):
    """
    skillDescriptionFacet
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    network_candidates = populate_candidates(owner_user_id=sample_user.id, count=2,
                                             candidate_skill_dicts=[{'last_used': datetime.datetime.now(),
                                                                     'name': 'Network', 'months_used': 12}],
                                             update_now=True)

    excel_candidates = populate_candidates(owner_user_id=sample_user.id,
                                           candidate_skill_dicts=[{'last_used': datetime.datetime.now(),
                                                                   'name': 'Excel', 'months_used': 26}],
                                           update_now=True)
    network_and_excel_candidates = populate_candidates(sample_user.id, count=3,
                                                       candidate_skill_dicts=[{'last_used': datetime.datetime.now(),
                                                                               'name': 'Excel',
                                                                               'months_used': 10},
                                                                              {'last_used': datetime.datetime.now(),
                                                                               'name': 'Network',
                                                                               'months_used': 5}], update_now=True)
    # Update db and cloudsearch
    _update_now(network_candidates+excel_candidates+network_and_excel_candidates)
    _assert_search_results(domain_id, {'skills': 'Network'},
                           candidate_ids=network_candidates + network_and_excel_candidates)
    _assert_search_results(domain_id, {'skills': 'Excel'},
                           candidate_ids=excel_candidates + network_and_excel_candidates, wait=False)
    _assert_search_results(domain_id, {'skills': ['Excel', 'Network']},
                           candidate_ids=network_and_excel_candidates, wait=False)


def to_fix_test_date_of_separation(sample_user):
    """
    Date of separation -
    military_end_date_from
    military_end_date_to
    :param sample_user:
    :return:
    """
    """

    """
    domain_id = sample_user.domain_id
    candidates_today = populate_candidates(sample_user.id, count=5, military_to_date=datetime.datetime.now(),
                                           military_grade=True,
                                           military_status=True, military_branch=True, update_now=False)
    candidates_2014 = populate_candidates(sample_user.id, count=2,
                                          military_to_date=datetime.date(year=2014, month=03, day=31),
                                          update_now=False)
    candidates_2012 = populate_candidates(sample_user.id, military_to_date=datetime.date(2012, 07, 15),
                                          update_now=False)

    # Update db and cloudsearch
    _update_now(candidates_2012 + candidates_2014 + candidates_today)
    # get candidates where date of separation is
    _assert_search_results(domain_id, {'military_end_date_from': 2013}, candidate_ids=candidates_2014+candidates_today)
    _assert_search_results(domain_id, {'military_end_date_from': 2010},
                           candidate_ids=candidates_2012 + candidates_2014 + candidates_today, wait=False)
    _assert_search_results(domain_id, {'military_end_date_from': 2010, 'military_end_date_to': 2014},
                           candidate_ids=candidates_2012+candidates_2014, wait=False)
    _assert_search_results(domain_id, {'military_end_date_to': 2012}, candidate_ids=candidates_2012, wait=False)
    _assert_search_results(domain_id, {'military_end_date_to': 2014}, candidate_ids=candidates_2012+candidates_2014,
                           wait=False)


def to_fix_test_service_status(sample_user):
    """
    military_service_status
    Facet name: serviceStatus
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    service_status1 = "Veteran"
    service_status2 = "Guard"
    service_status3 = "Retired"
    candidates_status1 = populate_candidates(owner_user_id=sample_user.id, count=4, military_status=service_status1, update_now=False)
    candidates_status2 = populate_candidates(owner_user_id=sample_user.id, count=7, military_status=service_status2, update_now=False)
    candidates_status3 = populate_candidates(owner_user_id=sample_user.id, count=2, military_status=service_status3, update_now=False)
    # Update all candidates at once
    all_candidates = candidates_status1+candidates_status2+candidates_status3
    _update_now(all_candidates)

    _assert_search_results(domain_id, {'military_service_status': service_status1}, candidates_status1)
    _assert_search_results(domain_id, {'military_service_status': service_status2}, candidates_status2, wait=False)
    _assert_search_results(domain_id, {'military_service_status': [service_status1, service_status3]},
                           candidates_status1 + candidates_status3, wait=False)
    _assert_search_results(domain_id, {'military_service_status': [service_status1, service_status2, service_status3]},
                           all_candidates, wait=False)


def to_fix_test_military_branch(sample_user):
    """
    branch: military_branch
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    service_branch1 = "Army"
    service_branch2 = "Coast Guard"
    service_branch3 = "Air Force"
    candidates_branch1 = populate_candidates(owner_user_id=sample_user.id, count=4, military_branch=service_branch1, update_now=False)
    candidates_branch2 = populate_candidates(owner_user_id=sample_user.id, count=7, military_branch=service_branch2, update_now=False)
    candidates_branch3 = populate_candidates(owner_user_id=sample_user.id, count=2, military_branch=service_branch3, update_now=False)
    all_candidates = candidates_branch1+candidates_branch2+candidates_branch3
    # Update all candidates at once
    _update_now(all_candidates)

    _assert_search_results(domain_id, {'military_branch': service_branch1}, candidates_branch1)
    _assert_search_results(domain_id, {'military_branch': service_branch2}, candidates_branch2, wait=False)
    _assert_search_results(domain_id, {'military_branch': [service_branch1, service_branch3]}, candidates_branch1 +
                           candidates_branch3, wait=False)
    _assert_search_results(domain_id, {'military_branch': [service_branch1, service_branch2, service_branch3]}, all_candidates,
                           wait=False)


def to_fix_test_search_by_military_grade(sample_user):
    """
    military highest grade
    Facet name 'highestGrade'
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    service_grade1 = "E-2"
    service_grade2 = "O-4"
    service_grade3 = "W-1"
    candidates_grade1 = populate_candidates(owner_user_id=sample_user.id, count=3, military_grade=service_grade1, update_now=False)
    candidates_grade2 = populate_candidates(owner_user_id=sample_user.id, count=2, military_grade=service_grade2, update_now=False)
    candidates_grade3 = populate_candidates(owner_user_id=sample_user.id, count=5, military_grade=service_grade3, update_now=False)
    all_candidates = candidates_grade1+candidates_grade2+candidates_grade3
    # Update all candidates at once
    _update_now(all_candidates)

    _assert_search_results(domain_id, {'military_highest_grade': service_grade1}, candidates_grade1)
    _assert_search_results(domain_id, {'military_highest_grade': service_grade2}, candidates_grade2, wait=False)
    _assert_search_results(domain_id, {'military_highest_grade': [service_grade1, service_grade3]}, candidates_grade1 +
                           candidates_grade3, wait=False)
    _assert_search_results(domain_id, {'military_highest_grade': [service_grade1, service_grade2, service_grade3]},
                           all_candidates, wait=False)


def to_fix_test_custom_fields_kaiser_nuid(sample_user):
    """
    Test kaiser specific custom field "Has NUID"
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    custom_field_obj = db.session.query(CustomField).filter(CustomField.name == "NUID").first()
    if custom_field_obj:
        custom_field_obj_id = custom_field_obj.id
    else:
        print "Creating custom field with name=NUID"
        new_custom_field_obj = CustomField(domain_id=domain_id, name="NUID", type='string',
                                           added_time=datetime.datetime.now())
        db.session.add(new_custom_field_obj)
        db.session.commit()
        custom_field_obj_id = new_custom_field_obj.id
    other_candidates = populate_candidates(owner_user_id=sample_user.id, count=2, update_now=False)
    candidate_cf1 = populate_candidates(owner_user_id=sample_user.id,
                                        custom_fields_dict={'custom_field_id': custom_field_obj_id,
                                                            'value': 'S264964'}, update_now=False)
    candidate_cf2 = populate_candidates(owner_user_id=sample_user.id,
                                        custom_fields_dict={'custom_field_id': custom_field_obj_id,
                                                            'value': 'D704398'}, update_now=False)
    candidate_cf3 = populate_candidates(owner_user_id=sample_user.id,
                                        custom_fields_dict={'custom_field_id': custom_field_obj_id,
                                                            'value': 'X073423'}, update_now=False)

    # Update all candidates in db and cloudsearch
    nuid_candidates = candidate_cf1+candidate_cf2+candidate_cf3
    all_candidates = other_candidates + nuid_candidates
    _update_now(all_candidates)

    _assert_search_results(domain_id, {"query": ""}, all_candidates)  # should give all candidates in domain
    # searched for cf-19; should return only nuid candidates
    _assert_search_results(domain_id, {"cf-%d" % custom_field_obj_id: "Has NUID"}, nuid_candidates, wait=False)


def test_custom_fields(sample_user):
    """
    Test various custom_fields
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    # Create custom field category named as 'Certifications'
    custom_field_cat = CustomFieldCategory(domain_id=domain_id, name="Certifications")
    db.session.add(custom_field_cat)
    custom_field_cat_id = custom_field_cat.id
    # Create custom fields under 'Certifications'
    custom_field1 = 'hadoop'
    custom_field2 = 'MangoDB'
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
    candidates_cf1 = populate_candidates(owner_user_id=sample_user.id, count=3,
                                         custom_fields_dict={'custom_field_id': custom_field1_id,
                                                             'value': custom_field1}, update_now=False)
    candidates_cf2 = populate_candidates(owner_user_id=sample_user.id, count=4,
                                         custom_fields_dict={'value': custom_field2,
                                                             'custom_field_id':custom_field2_id}, update_now=False)
    all_candidates = candidates_cf1+candidates_cf2
    _update_now(all_candidates)
    _assert_search_results(domain_id, {"cf-%s" % custom_field1_id: custom_field1}, candidates_cf1)
    _assert_search_results(domain_id, {"cf-%s" % custom_field2_id: custom_field2}, candidates_cf2, wait=False)
    _assert_search_results(domain_id, {"cf-%s" % custom_field1_id: custom_field1, "cf-%s" %
                                                                                  custom_field2_id: custom_field2},
                           all_candidates, wait=False)


def to_fix_test_paging(sample_user):
    """
    Test candidates on all pages
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    candidate_ids = populate_candidates(owner_user_id=sample_user.id, count=50, objective=True, added_time=True, phone=True,
                                        current_company=True, current_title=True, candidate_text_comment=True,
                                        city=True, state=True,
                                        zip_code=True, university=True, major=True, degree=True,
                                        university_start_year=True,
                                        university_start_month=True, graduation_year=True, graduation_month=True,
                                        military_branch=True,
                                        military_status=True, military_grade=True)
    # page 1 -> first 15 candidates
    least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
    _assert_search_results(domain_id, {'sort_by': least_recent}, candidate_ids[0:15], check_for_sorting=True)
    _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 1}, candidate_ids[0:15],
                           check_for_sorting=True, wait=False)  # explicitly passing page 1 as parameter
    # page2 -> next 15 candidates i.e. 15 to 30
    _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 2}, candidate_ids[15:30],
                           check_for_sorting=True, wait=False)
    # page3 -> next 15 candidates i.e. 30 to 45
    _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 3}, candidate_ids[30:45],
                           check_for_sorting=True, wait=False)
    # page4 -> next 15 candidates i.e. 45 to 50
    _assert_search_results(domain_id, {'sort_by': least_recent, 'page': 4}, candidate_ids[45:],
                           check_for_sorting=True, wait=False)


def to_fix_test_paging_with_facet_search(sample_user):
    """
    Test for no. of pages that are having candidates
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    current_title = "Sr. Manager"
    candidate_ids = populate_candidates(count=30, owner_user_id=sample_user.id, objective=True, phone=True,
                                         added_time=True, current_company=True, current_title=current_title)
    # Search by applying sorting so that candidates can be easily asserted
    least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
    _assert_search_results(domain_id, {'position': current_title, 'sort_by': least_recent},
                           candidate_ids[0:15])
    _assert_search_results(domain_id, {'position': current_title, 'sort_by': least_recent, 'page': 2},
                           candidate_ids[15:30], wait=False)


def test_id_in_request_vars(sample_user):
    """
    There is a case where id can be passed as parameter in search_candidates
    It can be used to check if a certain candidate ID is in a smartlist.
    :param sample_user:
    :return:
    """
    domain_id = sample_user.domain_id
    # Insert 10 candidates
    candidate_ids = populate_candidates(owner_user_id=sample_user.id, count=10, objective=True, phone=True, current_company=True,
                                        current_title=True, candidate_text_comment=True, city=True, state=True,
                                        zip_code=True, university=True, major=True, degree=True,
                                        university_start_year=True, university_start_month=True, graduation_year=True,
                                        graduation_month=True, military_branch=True, military_status=True,
                                        military_grade=True)
    # First candidate id
    first_candidate_id = candidate_ids[0]
    middle_candidate_id = candidate_ids[5]
    last_candidate_id = candidate_ids[-1]
    # if searched for particular candidate id, search should only return that candidate.
    _assert_search_results(domain_id, {'id': middle_candidate_id}, [middle_candidate_id], check_for_equality=True)
    _assert_search_results(domain_id, {'id': last_candidate_id}, [last_candidate_id], check_for_equality=True,
                           wait=False)
    _assert_search_results(domain_id, {'id': first_candidate_id}, [first_candidate_id], check_for_equality=True,
                           wait=False)


def to_fix_test_facets_are_returned_with_search_results(test_domain, sample_user, sample_user_2):
    """
    Test selected facets are returned with search results
    :param sample_user:
    :param sample_user_2:
    :return:
    """
    domain_id = test_domain.id

    sample_user_candidate_ids = populate_candidates(owner_user_id=sample_user.id, count=2, update_now=False)
    sample_user_2_candidate_ids = populate_candidates(owner_user_id=sample_user_2.id, count=1,
                                                      update_now=False)
    all_candidates = sample_user_candidate_ids + sample_user_2_candidate_ids
    # Update
    _update_now(all_candidates)

    # Default facets present
    sample_user = user_from_id(sample_user.id)
    sample_user_2 = user_from_id(sample_user_2.id)

    # There is always one 'unassigned' source for every domain.
    unassigned_candidate_source = db.session.query(CandidateSource).filter(CandidateSource.description == 'Unassigned',
                                                                           CandidateSource.domain_id == domain_id).first()
    # By default each candidate is assigned 'New' status
    new_status_id = get_or_create_status(db, status_name="New")
    facets = {'username': [{"value": sample_user.first_name + ' ' + sample_user.last_name,
                            "id": unicode(sample_user.id),
                            "count": 2},
                           {"value": sample_user_2.first_name + ' ' + sample_user_2.last_name,
                            "id": unicode(sample_user_2.id),
                            "count": 1}],
              'source': [{"value": unassigned_candidate_source.description,
                          "count": unicode(unassigned_candidate_source.id),
                          "id": 3}],
              'statusFacet': [{"value": 'New',
                               "id": unicode(new_status_id),
                               "count": 3}]
              }
    _assert_search_results(domain_id, {'query': ''}, all_candidates, check_for_equality=True, facets_dict=facets)

def _assert_search_results(domain_id, search_vars, candidate_ids, wait=True,
                           check_for_equality=False, check_for_sorting=False, facets_dict=None):
    """

    :param domain_id:
    :param search_vars:
    :param candidate_ids:
    :param wait:
    :param smart_wait:
    :param check_for_equality:
    :param check_for_sorting:
    :param facets_dict:
    :return:
    """
    # sometimes when asserting same uploaded candidates in a domain with several different queries,
    # its not worth waiting
    # so don't sleep as cloud_search is already updated
    if wait:
        time.sleep(30)  # Wait for cloud_search to update

    response = search_candidates(domain_id=domain_id, request_vars=search_vars)
    resultant_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
    print candidate_ids
    print resultant_candidate_ids
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


def _log_bounding_box_and_coordinates(base_location, radius, candidate_ids):
    """
    Display bounding box coordinates relative to radius (distance) and coordinates of candidate location
    :param base_location:
    :param radius:
    :param candidate_ids:
    :return:
    """


    distance_in_km = float(radius)/0.62137
    coords_dict = get_geocoordinates_bounding(base_location, distance_in_km)
    top_left_y, top_left_x, bottom_right_y, bottom_right_x = coords_dict['top_left'][0],coords_dict['top_left'][1], \
                                                             coords_dict['bottom_right'][0],coords_dict['bottom_right'][1]
    # Lat = Y Lng = X
    print "%s miles bounding box coordinates: ['%s,%s','%s,%s']" % (radius, top_left_y, top_left_x, bottom_right_y,
                                                                    bottom_right_x)
    if type(candidate_ids) in (int, long):
        candidate_ids = [candidate_ids]
    for index, candidate_id in enumerate(candidate_ids, start=1):
        row = db.session.query(CandidateAddress).filter_by(candidate_id=candidate_id).first()
        print "Candidate-%s Address: %s, %s, %s. \n cooridnates: %s" % (index, row.city, row.state,
                                                                        row.zip_code, row.coordinates)

        point = row.coordinates.split(',')
        statement1 = top_left_x <= float(point[1]) <= bottom_right_x
        statement2 = top_left_y >= float(point[0]) >= bottom_right_y
        print "Candidate-%s %s bounding box" % (index, 'lies inside' if statement1 and statement2 else 'not in')
        print "%s <= %s <= %s = %s" % (top_left_x, point[1], bottom_right_x, statement1)
        print "%s >= %s >= %s = %s" % (top_left_y, point[0], bottom_right_y, statement2)


def create_area_of_interest_facets(db, domain_id):
    """
    Create area of interest (aoi) facets in domain
    :param db:
    :param domain_id:
    :return: list of created area of interest ids
    """
    from candidate_service.modules.talent_areas_of_interest import KAISER_PARENT_TO_CHILD_AOIS
    all_aoi_ids = []
    for parent_aoi_name, child_aoi_names in KAISER_PARENT_TO_CHILD_AOIS.items():
        # Insert parent AOI if doesn't exist
        existing_parent_aoi = db.session.query(AreaOfInterest).filter(AreaOfInterest.domain_id == domain_id,
                                                                      AreaOfInterest.name == parent_aoi_name).first()
        if existing_parent_aoi:
            parent_aoi_id = existing_parent_aoi.id
        else:
            parent_aoi = AreaOfInterest(domain_id=domain_id, name=parent_aoi_name)
            db.session.add(parent_aoi)
            db.session.flush()
            parent_aoi_id = parent_aoi.id
        all_aoi_ids.append(parent_aoi_id)

        # Insert child AOIs if doesn't exist
        for child_aoi_name in child_aoi_names:
            existing_child_aoi = db.session.query(AreaOfInterest).filter(AreaOfInterest.domain_id == domain_id,
                                                                         AreaOfInterest.name == child_aoi_name,
                                                                         AreaOfInterest.parent_id == parent_aoi_id).first()
            if existing_child_aoi:
                child_aoi_id = existing_child_aoi.id
            else:
                child_aoi = AreaOfInterest(domain_id=domain_id, name=child_aoi_name, parent_id=parent_aoi_id)
                db.session.add(child_aoi)
                db.session.flush()
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


def user_from_id(user_id):
    """
    Get Id of user
    :param user_id:
    :return: User row object
    """

    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        logger.error("Couldn't find a user with user_id: %s", user_id)
        return None
    else:
        return user


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

from candidate_service.modules.talent_cloud_search import search_candidates, upload_candidate_documents
from candidate_service.modules.talent_candidates import create_or_update_candidate_from_params
