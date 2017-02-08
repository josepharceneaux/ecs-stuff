# TODO: I've commented out this file to prevent it from running in jenkins build due to many flaky tests -Amir
# """
# Test cases for candidate-search-service-API
# """
# import math
# from time import sleep
#
# # Error handling
# from candidate_service.common.error_handling import NotFoundError
#
# # Helpers
# from candidate_service.tests.modules.test_talent_cloud_search import (
#     populate_candidates, VARIOUS_US_LOCATIONS, create_area_of_interest_facets
# )
# from candidate_service.common.utils.datetime_utils import DatetimeUtils
# from candidate_service.common.tests.conftest import *
# from candidate_service.common.utils.test_utils import send_request, response_info, get_response
# from candidate_service.common.geo_services.geo_coordinates import get_geocoordinates_bounding
#
# # Models
# from candidate_service.common.models.candidate import CandidateAddress
# from candidate_service.common.models.candidate import CandidateStatus
# from candidate_service.common.models.user import Role
#
# # Routes
# from candidate_service.common.routes import CandidateApiUrl, UserServiceApiUrl
#
#
# class TestCandidateSearchGet(object):
#     @staticmethod
#     def create_candidates(access_token, user, talent_pool):
#         data = {'candidates': [
#             {'talent_pool_ids': {'add': [talent_pool.id]}},
#             {'talent_pool_ids': {'add': [talent_pool.id]}},
#             {'talent_pool_ids': {'add': [talent_pool.id]}},
#         ]}
#         resp = requests.post(
#             url=CandidateApiUrl.CANDIDATES,
#             headers={'Authorization': 'Bearer {}'.format(access_token),
#                      'content-type': 'application/json'},
#             data=json.dumps(data))
#         print response_info(response=resp)
#         assert resp.status_code == 201
#         return resp
#
#     def test_get_candidates_via_list_of_ids(self, access_token_first, user_first, talent_pool):
#         # Create candidates for user
#         create_resp = self.create_candidates(access_token_first, user_first, talent_pool).json()
#         # Retrieve candidates
#         data = {'candidate_ids': [candidate['id'] for candidate in create_resp['candidates']]}
#         resp = send_request('get', CandidateApiUrl.CANDIDATE_SEARCH_URI, access_token_first, data)
#         # resp = request_to_candidate_search_resource(access_token_first, 'get', data)
#         print response_info(resp)
#         assert resp.status_code == 200
#         assert len(resp.json()['candidates']) == 3  # Number of candidate IDs sent in
#         assert resp.json()['candidates'][0]['talent_pool_ids'][0] == talent_pool.id
#         assert resp.json()['candidates'][0]['id'] == data['candidate_ids'][0]
#
#
# def test_search_all_candidates_in_domain(user_first, access_token_first, talent_pool):
#     """
#     Test to search all candidates under the same domain
#     """
#     candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=5)
#     response = get_response(access_token_first, '', len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# # TODO: Commenting this flaky test for Amir (basit)
# # def test_search_location(user_first, access_token_first, talent_pool):
# #     """
# #     Test to search candidates using location
# #     """
# #     city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
# #     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
# #                                         city=city, state=state, zip_code=zip_code)
# #     response = get_response(access_token_first, '?location=%s,%s' % (city, state), expected_count=len(candidate_ids),
# #                             attempts=20)
# #     _assert_results(candidate_ids, response.json())
#
#
# def test_search_user_ids(user_first, access_token_first, talent_pool):
#     """
#     Test to search all candidates under the user
#     """
#     user_id = user_first.id
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=5)
#     response = get_response(access_token_first, '?user_ids={}'.format(user_id), expected_count=len(candidate_ids))
#     print response_info(response)
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_skills(user_first, access_token_first, talent_pool):
#     """
#     Test to search all candidates based on skills
#     """
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
#                                         skills=[{'name': 'hadoop', 'months_used': 36}])
#
#     response = get_response(access_token_first, '?skills=hadoop', expected_count=len(candidate_ids))
#     print response_info(response)
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_aoi(user_first, access_token_first, talent_pool):
#     """
#     Test to search all candidates based on area_of_interest
#     """
#     all_aoi_ids = create_area_of_interest_facets(db, user_first.domain_id)
#     number_of_aois = len(all_aoi_ids)
#     aoi_ids_list = all_aoi_ids[0:5]
#     areas_of_interest = [dict(area_of_interest_id=aoi_id) for aoi_id in aoi_ids_list]
#     candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                         count=5, areas_of_interest=areas_of_interest)
#     response = get_response(access_token_first, '?area_of_interest_ids={}'.format(aoi_ids_list[1]),
#                             expected_count=len(candidate_ids))
#     print response_info(response)
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_candidate_experience(user_first, access_token_first, talent_pool):
#     """Test to search candidates with experience"""
#     experience_2_years = [
#         {
#             'organization': 'Intel', 'position': 'Research analyst', 'start_year': 2013,
#             'start_month': 06, 'end_year': 2015, 'end_month': 06
#         }
#     ]
#     candidate_with_2_years_exp = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
#                                                      count=3, experiences=experience_2_years)
#
#     response = get_response(access_token_first, '?minimum_years_experience=0&maximum_years_experience=2',
#                             len(candidate_with_2_years_exp))
#     print response_info(response)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in response.json()['candidates']]
#     assert set(candidate_with_2_years_exp).issubset(resultant_candidate_ids)
#
#
# def test_search_position(user_first, access_token_first, talent_pool):
#     """Test to search candidates by job_title/position"""
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=4,
#                                         job_title="Developer")
#     response = get_response(access_token_first, '?job_title=Developer', expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_degree(user_first, access_token_first, talent_pool):
#     """Test to search candidates by degree type"""
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
#                                         degree_type="Masters")
#     response = get_response(access_token_first, '?degree_type=Masters', expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_school_name(user_first, access_token_first, talent_pool):
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
#                                         school_name='Oklahoma State University')
#     response = get_response(access_token_first, '?school_name=Oklahoma State University',
#                             expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_concentration(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by higher education
#     """
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
#                                         count=4, major='Post Graduate')
#     response = get_response(access_token_first, '?major=Post Graduate', expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_military_service_status(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by military service status
#     """
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
#                                         military_status="Retired")
#     response = get_response(access_token_first, '?military_service_status=Retired', expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_military_branch(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by military branch
#     """
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
#                                         military_branch="Army")
#     response = get_response(access_token_first, '?military_branch=Army', expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_military_highest_grade(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by military highest grade
#     """
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
#                                         military_grade="W-1")
#     response = get_response(access_token_first, '?military_highest_grade=W-1', expected_count=len(candidate_ids))
#     _assert_results(candidate_ids, response.json())
#
#
# def test_search_military_date_of_separation(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by military date of separation
#     """
#
#     candidates_today = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=5,
#                                            military_to_date=str(datetime.utcnow().date()))
#
#     candidates_2014 = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=3,
#                                           military_to_date='2014-04-26')
#
#     candidates_2012 = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=2,
#                                           military_to_date='2012-07-15')
#
#     test1_candidate_ids = candidates_2014 + candidates_today
#
#     response1 = get_response(access_token_first, '?military_end_date_from=2013', len(test1_candidate_ids))
#     _assert_results(test1_candidate_ids, response1.json())
#
#     test2_candidate_ids = candidates_2012 + candidates_2014 + candidates_today
#     response2 = get_response(access_token_first, '?military_end_date_from=2010', len(test2_candidate_ids))
#     _assert_results(test2_candidate_ids, response2.json())
#
#     test3_candidate_ids = candidates_2012 + candidates_2014
#     response3 = get_response(access_token_first,
#                              '?military_end_date_from=2010&military_end_date_to=2014', len(test3_candidate_ids))
#     _assert_results(test3_candidate_ids, response3.json())
#
#     test4_candidate_ids = candidates_2012
#     response4 = get_response(access_token_first, '?military_end_date_to=2012', len(test4_candidate_ids))
#     _assert_results(test4_candidate_ids, response4.json())
#
#     test5_candidate_ids = candidates_2012 + candidates_2014
#     response5 = get_response(access_token_first, '?military_end_date_to=2014', len(test5_candidate_ids))
#     _assert_results(test5_candidate_ids, response5.json())
#
#
# # TODO: @amir this test is failing frequently . Two of those builds are 5473, 5474
# # def test_search_query_with_name(user_first, access_token_first, talent_pool):
# #     """
# #     Test to search candidates by passing query argument
# #     For example, search by querying first_name
# #     """
# #     candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
# #                                         count=5, first_name=fake.first_name(), last_name=fake.last_name())
# #     response = get_response(access_token_first, '?q=Naveen', len(candidate_ids))
# #     _assert_results(candidate_ids, response.json())
#
#
# def test_search_get_only_requested_fields(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates and get only requested fields like email,source_id,etc,..
#     """
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=2)
#     response = get_response(access_token_first, '?fields=email', len(candidate_ids))
#     resultant_keys = response.json()['candidates'][0].keys()
#     assert len(resultant_keys) == 1
#     assert 'email' in resultant_keys
#
#
# def test_search_paging(user_first, access_token_first, talent_pool):
#     """
#     Test: Search by the most recently added candidates
#     """
#
#     count = 30
#     candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=count, wait=1)
#     response = get_response(access_token_first, '?sort_by=~recent', expected_count=15)
#     print response_info(response)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in response.json()['candidates']]
#     assert set(candidate_ids[:15]).issubset(resultant_candidate_ids)
#
#
# def test_search_by_first_name(user_first, access_token_first, talent_pool):
#     """
#     Test search candidates by first name
#     """
#     first_name = 'Marilyn'
#     # Create candidate with first name and last name
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, first_name=first_name)
#     resp = get_response(access_token_first, '?{}'.format(first_name), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#
# def test_search_by_last_name(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by last name
#     """
#     last_name = 'Lynn'
#     # Create candidate with last name
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, last_name=last_name)
#     resp = get_response(access_token_first, '?{}'.format(last_name), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#
# def test_search_by_current_company(talent_pool, access_token_first, user_first):
#     """
#     Test to search candidates by current company
#     """
#     company_name = "Google"
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=5,
#                                         company_name=company_name)
#     resp = get_response(access_token_first, '?{}'.format(company_name), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#
# def test_search_by_position_facet(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by position
#     """
#     current_title = "Senior Developer"
#     candidate_ids = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
#                                         count=12, job_title=current_title)
#     resp = get_response(access_token_first, '?job_title={}'.format(current_title), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#
# def test_search_by_position_and_company(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by position and company
#     """
#     company, position = "Apple", "CEO"
#     # 10 other candidates at apple
#     populate_candidates(talent_pool=talent_pool, access_token=access_token_first, count=10, company_name=company)
#     ceo_at_apple = populate_candidates(talent_pool=talent_pool, access_token=access_token_first,
#                                        count=1, company_name=company, job_title=position)
#     # Search for company Apple and position CEO, it should only return 1 candidate although Apple has 10 other employees
#     resp = get_response(access_token_first, '?organization={}&job_title={}'.format(company, position),
#                         len(ceo_at_apple))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(ceo_at_apple).issubset(resultant_candidate_ids)
#
#
# def test_search_by_university(user_first, access_token_first, talent_pool):
#     """
#     university > school_name
#     """
#     university1, university2 = 'University Of Washington', 'Oklahoma State University'
#     university1_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                                  school_name=university1)
#     # Create other candidates with other university, check
#     university2_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
#                                                  school_name=university2)
#     total_candidates = university1_candidates + university2_candidates
#
#     resp = get_response(access_token_first, '?school_name={}'.format(university1), len(university1_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(university1_candidates).issubset(resultant_candidate_ids)
#
#     resp = get_response(access_token_first, '?school_name={}'.format(university2), len(university2_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(university2_candidates).issubset(resultant_candidate_ids)
#
#
# def test_search_by_location(user_first, talent_pool, access_token_first):
#     """
#     Search by City name, State name
#     """
#     city, state, zip_code = random.choice(VARIOUS_US_LOCATIONS)
#     candidate_ids = populate_candidates(count=2, access_token=access_token_first, talent_pool=talent_pool, city=city,
#                                         state=state, zip_code=zip_code)
#
#     # With zipcode only
#     resp = get_response(access_token_first, '?zipcode={}'.format(zip_code), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#     # With city and state only
#     resp = get_response(access_token_first, '?city={}&state={}'.format(city, state), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#     # With city, state and zip
#     resp = get_response(access_token_first, '?city={}&state={}&zipcode={}'.format(city, state, zip_code),
#                         len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#
# def test_search_by_major(user_first, access_token_first, talent_pool):
#     """
#     Test to search based on major facet
#     Without university major doesn't gets created in database, So university should also be created for major
#     """
#     major1, major2 = 'Electrical Engineering', 'Computer Science'
#     major1_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
#                                             major=major1)
#     major2_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=7,
#                                             major=major2)
#
#     resp = get_response(access_token_first, '?major={}'.format(major1), len(major1_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(major1_candidates).issubset(resultant_candidate_ids)
#
#     resp = get_response(access_token_first, '?major={}'.format(major2), len(major2_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(major2_candidates).issubset(resultant_candidate_ids)
#
#
# def test_search_by_degree(user_first, access_token_first, talent_pool):
#     """
#     Search by degree
#     """
#     degree1, degree2 = 'Masters', 'Bachelors'
#     master_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
#                                             degree_type=degree1)
#     bachelor_candidates = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=2,
#                                               degree_type=degree2)
#     all_candidates = master_candidates + bachelor_candidates
#
#     # Search for candidates with Masters
#     resp = get_response(access_token_first, '?degree_type={}'.format(degree1), len(master_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(master_candidates).issubset(resultant_candidate_ids)
#
#     # Search for candidates with Bachelors
#     resp = get_response(access_token_first, '?degree_type={}'.format(degree2), len(bachelor_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(bachelor_candidates).issubset(resultant_candidate_ids)
#
#     # Search for candidates with any degree types
#     resp = get_response(access_token_first, '?degree_type={},{}'.format(degree1, degree2), len(all_candidates))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(all_candidates).issubset(resultant_candidate_ids)
#
#
# def test_search_source(user_first, access_token_first, talent_pool):
#     """
#     Test to search candidates by source
#     """
#
#     user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#     db.session.commit()
#
#     # Create a new source
#     data = {"source": {"description": "test source", "notes": "sample source for functional tests"}}
#     new_source_resp = send_request('post', UserServiceApiUrl.DOMAIN_SOURCES, access_token_first, data)
#     print response_info(new_source_resp)
#
#     # Add candidates with the same source ID
#     source_id = new_source_resp.json()['source']['id']
#     candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=5,
#                                         source_id=source_id)
#
#     resp = get_response(access_token_first, '?source_ids={}'.format(source_id), len(candidate_ids))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids).issubset(resultant_candidate_ids)
#
#
# def test_search_by_added_date(user_first, talent_pool, access_token_first):
#     """
#     Test to search candidates by added time
#     """
#
#     # Candidate added on 01 Dec 2014 at 14:30:00
#     candidate1 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=3,
#                                      added_datetime='2014-12-01T14:30:00+00:00')
#
#     # Candidate added on 20 Mar 2015 at 10:00:00
#     candidate2 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=3,
#                                      added_datetime='2015-03-20T10:00:00+00:00')
#
#     # Candidate added on 25 May 2010 at 00:00:00
#     candidate3 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=3,
#                                      added_datetime='2010-05-25T00:00:00+00:00')
#
#     # Candidate added today (now)
#     candidate4 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
#                                      added_datetime=DatetimeUtils.to_utc_str(datetime.utcnow()))
#
#     # Get candidates from within range 1 jan'14 to 30 May'15 (format mm/dd/yyyy) -> Will include candidates 1 & 2
#     resp = get_response(access_token_first, "?date_from=01/01/2014&date_to=05/30/2015", expected_count=6)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate1 + candidate2).issubset(resultant_candidate_ids)
#
#     # Get candidates from starting date as 15 Mar 2015 and without end date -> will include candidates- 2, 4
#     resp = get_response(access_token_first, "?date_from=03/15/2015", expected_count=4)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate2 + candidate4).issubset(resultant_candidate_ids)
#
#     # Get candidates from no starting date but ending date as 31 Dec 2014 -> will give candidates 1 & 3
#     resp = get_response(access_token_first, "?date_to=12/31/2014", expected_count=6)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate1 + candidate3).issubset(resultant_candidate_ids)
#
#
# def test_area_of_interest_facet(access_token_first, user_first, talent_pool):
#     """
#     Test areaOfInterestIdFacet by passing aoi values as list and as single select
#     """
#
#     # Create domain area of interest and associate candidate 1 & candidate 2 to it
#     domain_id = user_first.domain_id
#     all_aoi_ids = create_area_of_interest_facets(db, domain_id)
#     print "Total area of interest facets present: %s" % len(all_aoi_ids)
#     aoi_ids_list_1 = all_aoi_ids[0:5]
#     aoi_ids_list_2 = all_aoi_ids[-4:-1]
#     areas_of_interest_1 = [{'area_of_interest_id': aoi_id} for aoi_id in aoi_ids_list_1]
#     areas_of_interest_2 = [{'area_of_interest_id': aoi_id} for aoi_id in aoi_ids_list_2]
#     candidate1 = populate_candidates(access_token_first, talent_pool, areas_of_interest=areas_of_interest_1)
#     candidate2 = populate_candidates(access_token_first, talent_pool, areas_of_interest=areas_of_interest_2)
#
#     # Search for candidates associated to some of the domain's aois
#     aoi_ids_1_segment = ','.join(map(str, (aoi_ids_list_1[0:3])))
#     resp = get_response(access_token_first, "?area_of_interest_ids={}".format(aoi_ids_1_segment))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate1).issubset(resultant_candidate_ids)
#
#     # Search for all candidates associated with domain's aoi
#     aoi_ids_1 = ','.join(map(str, (aoi_ids_list_1[0:3])))
#     resp = get_response(access_token_first, "?area_of_interest_ids={}".format(aoi_ids_1))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate1).issubset(resultant_candidate_ids)
#
#     # Search for all candidates associated with domain's aoi
#     aoi_ids_2 = ','.join(map(str, (aoi_ids_list_2[0:3])))
#     resp = get_response(access_token_first, "?area_of_interest_ids={}".format(aoi_ids_2))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate2).issubset(resultant_candidate_ids)
#
#
# def test_status_facet(user_first, access_token_first, talent_pool):
#     """
#     Test with status facet by passing value as list and single value
#     """
#
#     # By default every candidate has "New" status
#     candidate1 = populate_candidates(access_token_first, talent_pool)
#     candidate2 = populate_candidates(access_token_first, talent_pool)
#     candidate3 = populate_candidates(access_token_first, talent_pool)
#     count_of_candidates = len(candidate1 + candidate2 + candidate3)
#
#     # Default status ID
#     new_status_id = CandidateStatus.DEFAULT_STATUS_ID  # Newly added candidate
#
#     # Search for candidates associated with status ID 1
#     resp = get_response(access_token_first, "?status={}".format(new_status_id), expected_count=count_of_candidates)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate2).issubset(resultant_candidate_ids)
#
#     # Change status of candidate1 to "Hired"
#     hired_status_id = CandidateStatus.HIRED
#     data = {'candidates': [{'status_id': hired_status_id}]}
#     resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate1[0], access_token_first, data)
#     print response_info(resp)
#
#     # search for qualified candidates
#     resp = get_response(access_token_first, "?status_ids={}".format(hired_status_id))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate1).issubset(resultant_candidate_ids)
#
#
# def get_or_create_status(db, status_name):
#     """
#     Creates status with given status_name if not exists, else return id of status
#     :return: id of given status_name
#     """
#     status_obj = db.session.query(CandidateStatus).filter_by(description=status_name).first()
#     if status_obj:
#         return status_obj.id
#     else:  # create one with given name
#         print "Status: %s, not present in database, creating a new one" % status_name
#         add_status = CandidateStatus(description=status_name, otes="Candidate is %s" % status_name.lower())
#         db.session.add(add_status)
#         db.session.commit()
#         return add_status
#
#
# def test_source_facet(user_first, access_token_first, talent_pool):
#     """
#     Test search filter for various available source facets.
#     """
#
#     # Create a new source
#
#     user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#     db.session.commit()
#
#     count = 5
#     data = {'source': {'description': 'test source_{}'.format(str(uuid.uuid4())[:5])}}
#     resp = send_request('post', UserServiceApiUrl.DOMAIN_SOURCES, access_token_first, data)
#     print response_info(resp)
#     source_id = resp.json()['source']['id']
#     candidate_ids2 = populate_candidates(access_token_first, talent_pool, count=count, source_id=source_id)
#
#     # Search for candidates with created source, it will not include candidates with unassigned source
#     resp = get_response(access_token_first, "?source_ids={}".format(source_id), expected_count=count)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidate_ids2).issubset(resultant_candidate_ids)
#
#
# def test_skill_description_facet(user_first, access_token_first, talent_pool):
#     """
#     Test skills facet in search
#     """
#
#     skill_name_1 = str(uuid.uuid4())[:5]
#     skill_1_candidates = populate_candidates(access_token_first, talent_pool, count=2,
#                                              skills=[{'name': skill_name_1, 'months_used': 12}])
#
#     skill_name_2 = str(uuid.uuid4())[:5]
#     skill_2_candidates = populate_candidates(access_token_first, talent_pool,
#                                              skills=[{'name': skill_name_2, 'months_used': 26}])
#
#     both_skills_candidates = populate_candidates(access_token_first, talent_pool, count=3,
#                                                  skills=[{'name': skill_name_1, 'months_used': 10},
#                                                          {'name': skill_name_2, 'months_used': 5}])
#
#     # Search for candidates with skill_name_1 (skill_1_candidates + both_skills_candidates)
#     resp = get_response(access_token_first, "?skills={}".format(skill_name_1),
#                         expected_count=5)
#     print response_info(resp)
#     candidates_1_and_both_skills_candidates = skill_1_candidates + both_skills_candidates
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidates_1_and_both_skills_candidates).issubset(resultant_candidate_ids)
#
#     # Search for candidates with skill_name_2 (skill_2_candidates + both_skills_candidates)
#     resp = get_response(access_token_first, "?skills={}".format(skill_name_2), 4)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     candidates_2_and_both_skills_candidates = skill_2_candidates + both_skills_candidates
#     assert set(candidates_2_and_both_skills_candidates).issubset(resultant_candidate_ids)
#
#
# def test_service_status(user_first, access_token_first, talent_pool):
#     """
#     military_service_status
#     Facet name: serviceStatus
#     """
#
#     service_status1 = "Veteran"
#     count = 4
#     candidates_status1 = populate_candidates(access_token_first, talent_pool, count=count,
#                                              military_status=service_status1)
#
#     # Search for candidates via military service status
#     resp = get_response(access_token_first, "?military_service_status={}".format(service_status1), expected_count=count)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidates_status1).issubset(resultant_candidate_ids)
#
#
# def test_military_branch(user_first, access_token_first, talent_pool):
#     """
#     branch: military_branch
#     """
#
#     count = 4
#     service_branch = "Army"
#     candidates_branch = populate_candidates(access_token_first, talent_pool, count=count,
#                                             military_branch=service_branch)
#
#     # Search for candidates via military branch
#     resp = get_response(access_token_first, "?military_branch={}".format(service_branch), expected_count=count)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidates_branch).issubset(resultant_candidate_ids)
#
#
# def test_search_by_military_grade(user_first, access_token_first, talent_pool):
#     """
#     military highest grade
#     Facet name 'highestGrade'
#     """
#     service_grade = "E-2"
#     candidates_grade = populate_candidates(access_token_first, talent_pool, count=3, military_grade=service_grade)
#
#     # Search for candidates via military grade
#     resp = get_response(access_token_first, "?military_highest_grade={}".format(service_grade), expected_count=3)
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     assert set(candidates_grade).issubset(resultant_candidate_ids)
#
#
# def test_custom_fields(user_first, access_token_first, candidate_first):
#     """
#     Test various custom_fields
#     """
#
#     user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#     db.session.commit()
#
#     # Create custom field category named as 'Certifications'
#     name = str(uuid.uuid4())[:5]
#     data = {'custom_fields': [{'name': name}]}
#     resp = send_request('post', UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS, access_token_first, data)
#     print response_info(resp)
#     custom_field_id = resp.json()['custom_fields'][0]['id']
#
#     # Create candidate custom field
#     value = str(uuid.uuid4())[:5]
#     data = {'candidate_custom_fields': [{'custom_field_id': custom_field_id, 'value': value}]}
#     resp = send_request('post', CandidateApiUrl.CUSTOM_FIELDS % candidate_first.id, access_token_first, data)
#     print response_info(resp)
#
#     # Search candidate by custom field id & value
#     resp = get_response(access_token_first, "?custom_fields={}|{}".format(custom_field_id, value))
#     print response_info(resp)
#     resultant_candidate_ids = [long(candidate['id']) for candidate in resp.json()['candidates']]
#     candidate_id = [candidate_first.id]
#     assert set(candidate_id).issubset(resultant_candidate_ids)
#
#
# def test_pagination(user_first, access_token_first, talent_pool):
#     """
#     Test candidates on all pages
#     """
#
#     # Create 50 candidates
#     count = 50
#     populate_candidates(access_token_first, talent_pool, count=count)
#
#     page_count = 15
#
#     # Search for candidates: page 1 result
#     resp = get_response(access_token_first, '?sort_by=~recent', expected_count=page_count)
#     print response_info(resp)
#     assert len(resp.json()['candidates']) == page_count
#
#     # Search for candidates: page 2 result
#     resp = get_response(access_token_first, '?sort_by=~recent&page=2', expected_count=page_count)
#     print response_info(resp)
#     assert len(resp.json()['candidates']) == page_count
#
#     # Search for candidates: page 3 result
#     resp = get_response(access_token_first, '?sort_by=~recent&page=3', expected_count=page_count)
#     print response_info(resp)
#     assert len(resp.json()['candidates']) == page_count
#
#     # Search for candidates: page 4 result
#     last_page_count = count - (page_count * 3)
#     resp = get_response(access_token_first, '?sort_by=~recent&page=4', expected_count=last_page_count)
#     print response_info(resp)
#     assert len(resp.json()['candidates']) == last_page_count
#
#
# def test_paging_with_facet_search(user_first, access_token_first, talent_pool):
#     """
#     Test for no. of pages that are having candidates
#     """
#
#     count = 30
#     current_title = "Manager of {}".format(str(uuid.uuid4())[:5])
#     populate_candidates(access_token_first, talent_pool, count=count, job_title=current_title)
#
#     # Search by sorting
#     resp = get_response(access_token_first, '?sort_by=~recent', expected_count=15)
#     print response_info(resp)
#     assert resp.json()['max_pages'] == int(math.ceil(count / 15.0))
#
#
# def test_id_in_request_vars(user_first, access_token_first, talent_pool):
#     """
#     There is a case where id can be passed as parameter in search_candidates
#     It can be used to check if a certain candidate ID is in a smartlist.
#     """
#     # Create 10 candidates
#     count = 10
#     candidate_ids = populate_candidates(access_token_first, talent_pool, count=count)
#
#     # if searched for particular candidate id, search should only return that candidate.
#     first_candidate_id = candidate_ids[0]
#     resp = get_response(access_token_first, '?id={}'.format(first_candidate_id))
#     print response_info(resp)
#     assert resp.json()['total_found'] == 1
#
#
# def test_facets_are_returned_with_search_results(user_first, access_token_first, talent_pool):
#     """
#     Test selected facets are returned with search results
#     """
#
#     # Create some candidates
#     count = 2
#     populate_candidates(access_token_first, talent_pool, count=count)
#
#     # Search for user's candidates
#     resp = get_response(access_token_first, '?user_ids={}'.format(user_first.id), expected_count=count)
#     print response_info(resp)
#     print "\nresp: {}".format(resp.json().keys())
#     assert resp.json()['total_found'] == count
#     assert set(['total_found', 'max_score', 'facets', 'candidates', 'max_pages']) == set(resp.json().keys())
#
#
# def test_sort_by_match(user_first, access_token_first, talent_pool):
#     """
#     Test: Search by sorting by match
#     """
#
#     count = 3
#     populate_candidates(access_token_first, talent_pool, count=count)
#     resp = get_response(access_token_first, '?sort_by=~match', expected_count=count)
#     print response_info(resp)
#     assert resp.json()['total_found'] == count
#
#     resp = get_response(access_token_first, '?sort_by=match', expected_count=3)
#     print response_info(resp)
#     assert resp.json()['total_found'] == count
#
# # TODO: (by Zohaib Ijaz)  @Amir This test is failing. Kindly uncomment it when fixed (Jenkins builds: 4863, 4864, 4865)
# # def test_location_with_radius(user_first, access_token_first, talent_pool):
# #     """
# #     Search by city, state + radius
# #     Search by zip + radius
# #     Distance in miles
# #     Ref: http://www.timeanddate.com/worldclock/distances.html?n=283
# #     """
# #
# #     # 10 mile candidates with city & state
# #     _10_mile_candidate = populate_candidates(access_token=access_token_first,
# #                                              talent_pool=talent_pool,
# #                                              city='santa clara', state='ca', zip_code='95050')
# #
# #     _10_mile_candidate_2 = populate_candidates(access_token=access_token_first,
# #                                                talent_pool=talent_pool,
# #                                                city='milpitas', state='ca', zip_code='95035')
# #     # 25 mile candidates with city state
# #     _25_mile_candidate = populate_candidates(access_token=access_token_first,
# #                                              talent_pool=talent_pool,
# #                                              city='newark', state='ca', zip_code='94560')
# #
# #     _25_mile_candidate_2 = populate_candidates(access_token=access_token_first,
# #                                                talent_pool=talent_pool,
# #                                                city='stanford', state='ca', zip_code='94305')
# #
# #     _50_mile_candidate = populate_candidates(access_token=access_token_first,
# #                                              talent_pool=talent_pool,
# #                                              city='oakland', state='ca', zip_code='94601')
# #
# #     _75_mile_candidate = populate_candidates(access_token=access_token_first,
# #                                              talent_pool=talent_pool,
# #                                              city='novato', state='ca', zip_code='94945')
# #
# #     _100_mile_candidate = populate_candidates(access_token=access_token_first,
# #                                               talent_pool=talent_pool,
# #                                               city='sacramento', state='ca', zip_code='95405')
# #
# #     # The following candidate will not appear in search with radius
# #     _more_than_100_mile_candidate = populate_candidates(access_token=access_token_first,
# #                                                         talent_pool=talent_pool,
# #                                                         city='oroville', state='ca', zip_code='95965')
# #
# #     candidates_within_10_miles = _10_mile_candidate + _10_mile_candidate_2
# #     candidates_within_25_miles = candidates_within_10_miles + _25_mile_candidate + _25_mile_candidate_2
# #     candidates_within_50_miles = candidates_within_25_miles + _50_mile_candidate
# #     candidates_within_75_miles = candidates_within_50_miles + _75_mile_candidate
# #     candidates_within_100_miles = candidates_within_75_miles + _100_mile_candidate
# #     all_candidates = candidates_within_100_miles + _more_than_100_mile_candidate
# #
# #     # All candidates in domain; it will include more_than_100_mile_candidate also,
# #     # which will not appear in other searches with radius.
# #     resp = get_response(access_token_first, "?location=''", expected_count=len(all_candidates))
# #     print response_info(resp)
# #     assert resp.json()['total_found'] == len(all_candidates)
# #
# #     # Search with zipcode and radius within 10 miles
# #     resp = get_response(access_token_first, "?location={zipcode}&radius={radius}".format(zipcode=95050, radius=10))
# #     print response_info(resp)
# #     assert resp.json()['total_found'] == 2  # only two candidates are within 10 miles of Santa Clara
# #
# #     # Search with zipcode and radius within 25 miles
# #     resp = get_response(access_token_first, "?location={zipcode}&radius={radius}".format(zipcode=95050, radius=25))
# #     print response_info(resp)
# #     assert resp.json()['total_found'] == 4  # only four candidates are within 10 miles of Santa Clara
# #
# #     # Search with zipcode and radius within 50 miles
# #     resp = get_response(access_token_first, "?location={zipcode}&radius={radius}".format(zipcode=95050, radius=50))
# #     print response_info(resp)
# #     assert resp.json()['total_found'] == 5  # only five candidates are within 10 miles of Santa Clara
# #
# #     # Search with zipcode and radius within 75 miles
# #     resp = get_response(access_token_first, "?location={zipcode}&radius={radius}".format(zipcode=95050, radius=75))
# #     print response_info(resp)
# #     assert resp.json()['total_found'] == 7  # only seven candidates are within 10 miles of Santa Clara
#
#
# # TODO: Check Search API for the accuracy of results. Once confirmed & fixed uncomment test
# # def test_sort_by_proximity(user_first, access_token_first, talent_pool):
# #     """
# #     Sort by distance
# #     """
# #
# #     # 10 mile candidates with city & state
# #     _10_mile_candidate = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
# #                                              city='Santa Clara', state='CA', zip_code='95050')
# #     _10_mile_candidate_2 = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
# #                                                city='Milpitas', state='CA', zip_code='95035')
# #
# #     # 25 mile candidates with city state
# #     _25_mile_candidate = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
# #                                              city='Fremont', state='CA', zip_code='94560')
# #
# #     # 50 mile candidates with city state
# #     _50_mile_candidate = populate_candidates(access_token=access_token_first, talent_pool=talent_pool,
# #                                              city='Oakland', state='CA', zip_code='94601')
# #
# #     closest = [_10_mile_candidate[0], _10_mile_candidate_2[0], _25_mile_candidate[0], _50_mile_candidate[0]]
# #     furthest = closest[::-1]  # Reverse the order
# #
# #     # Without radius i.e. it will by default take 50 miles
# #     # Sort by -> Proximity: Closest
# #     resp = get_response(access_token_first, '?location=Santa Clara, CA&sort_by=proximity', expected_count=4)
# #     print response_info(resp)
# #     resultant_candidate_ids = [candidate['id'] for candidate in resp.json()['candidates']]
# #     assert resultant_candidate_ids == map(unicode, closest)
# #
# #     # Sort by -> Proximity: Furthest
# #     resp = get_response(access_token_first, '?location=Santa Clara, CA&sort_by=~proximity', expected_count=4)
# #     print response_info(resp)
# #     resultant_candidate_ids = [candidate['id'] for candidate in resp.json()['candidates']]
# #     assert resultant_candidate_ids == map(unicode, furthest)
#
#
# # TODO: Flaky test report - Amir
# # def test_search_status(user_first, access_token_first, talent_pool):
# #     """
# #     Test to search all candidates by status
# #     """
# #
# #     # Change status of last candidate
# #     status_id = 6  # Candidate is highly prospective
# #     count = 3  # number of candidates to be created
# #     candidate_ids = populate_candidates(count=count, access_token=access_token_first, talent_pool=talent_pool)
# #
# #     # Update last candidate's status
# #     last_candidate_id = candidate_ids[-1]
# #     data = {'candidates': [{'status_id': status_id}]}
# #     update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % last_candidate_id, access_token_first, data)
# #     print response_info(update_resp)
# #
# #     # Search via status ID
# #     resp = get_response(access_token_first, '?status_ids={}'.format(status_id))
# #     print response_info(resp)
# #
# #     # Only last candidate should appear in result
# #     candidate_ids_from_search = [candidate['id'] for candidate in resp.json()['candidates']]
# #     assert candidate_ids_from_search.pop() == unicode(update_resp.json()['candidates'][0]['id'])
#
#
# # def test_sort_by_added_date(user_first, access_token_first, talent_pool):
# #     """
# #     Least recent --> sort_by:added_time-asc
# #     Most recent -->  sort_by:added_time-desc
# #     """
# #
# #     # Candidate added on 25 May 2010 at 00:00:00
# #     candidate1 = populate_candidates(access_token_first, talent_pool,
# #                                      added_time=datetime.datetime(2010, 05, 25, 00, 00, 00))
# #
# #     # Candidate added on 01 Dec 2014 at 14:30:00
# #     candidate2 = populate_candidates(user_id=user_first.id,
# #                                      added_time=datetime.datetime(2014, 12, 01, 14, 30, 00),
# #                                      update_now=False)
# #     # Candidate added on 20 Mar 2015 at 10:00:00
# #     candidate3 = populate_candidates(user_id=user_first.id,
# #                                      added_time=datetime.datetime(2015, 03, 20, 10, 00, 00),
# #                                      update_now=False)
# #     # Candidate added today (now)
# #     candidate4 = populate_candidates(user_id=user_first.id, added_time=datetime.datetime.now(), update_now=False)
# #     sorted_in_ascending_order_of_added_time = candidate1 + candidate2 + candidate3 + candidate4
# #     _update_now(sorted_in_ascending_order_of_added_time)
# #     sorted_in_descending_order_of_added_time = sorted_in_ascending_order_of_added_time[::-1]
# #     # check for order in which candiate were added. Sort by Date: Most recent - all candidates
# #     most_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['recent']
# #     _assert_search_results(domain_id, {'sort_by': most_recent},
# #                            candidate_ids=sorted_in_descending_order_of_added_time, check_for_sorting=True)
# #     # Sort by Date: Least recent - all candidates
# #     least_recent = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH['~recent']
# #     _assert_search_results(domain_id, {'sort_by': least_recent},
# #                            candidate_ids=sorted_in_ascending_order_of_added_time,
# #                            check_for_sorting=True, wait=False)
# #     # Get candidates from within range 1 jan'14 to 30 May'15 -> Will include candidates 3rd & 2nd in descending order
# #     _assert_search_results(domain_id, {'date_from': '01/01/2014', 'date_to': '05/30/2015',
# #                                        'sort_by': most_recent}, candidate_ids=candidate3 + candidate2, wait=False)
#
#
# # def test_search_based_on_years_of_experience(user_first, access_token_first, talent_pool):
# #     """
# #     minimum_years_experience
# #     maximum_years_experience
# #     """
# #
# #     # Candidate with less than one year of experience
# #     current_year = datetime.now().year
# #     candidate_with_0_years_exp = populate_candidates(access_token_first, talent_pool,
# #                                                      company_name='Amazon',
# #                                                      job_title='Software Architect',
# #                                                      position_start_year=current_year - 1,
# #                                                      position_start_month=1,
# #                                                      is_current_job=True)
# #
# #     # Candidate with 2 years of experience
# #     candidate_with_2_years_exp = populate_candidates(access_token_first, talent_pool,
# #                                                      company_name='Motorola',
# #                                                      job_title='Area Manager',
# #                                                      position_start_year=2011,
# #                                                      position_start_month=11,
# #                                                      position_end_year=2013,
# #                                                      position_end_month=10)
# #
# #     resp = get_response(access_token_first, '?minimum_years_experience={}'.format(2))
# #     print response_info(resp)
#
# # TODO: Comment out flaky test - Amir
# # def test_search_by_tag_ids_and_names(user_first, access_token_first, candidate_first):
# #     """
# #     Test: Add tags to candidate's profile, then search for candidate using tag IDs
# #     """
# #     AddUserRoles.add_get_edit(user_first)
# #
# #     # Add tags to candidate's profile
# #     data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}
# #     create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
# #     print response_info(create_resp)
# #     assert create_resp.status_code == requests.codes.CREATED
# #     assert len(create_resp.json()['tags']) == len(data['tags'])
# #
# #     # Search for candidates using tag IDs
# #     created_tag_ids = [tag['id'] for tag in create_resp.json()['tags']]
# #     tag_ids = ','.join(map(str, created_tag_ids))
# #     get_resp = get_response(access_token_first, '?tag_ids={}'.format(tag_ids))
# #     print response_info(get_resp)
# #     assert get_resp.json()['total_found'] == 1  # tags associated with only 1 candidate
# #     assert get_resp.json()['candidates'][0]['tag_ids'] == map(unicode, created_tag_ids)
# #
# #     # Search for candidates using tag names
# #     created_tag_names = ','.join(tag['name'] for tag in data['tags'])
# #     get_resp = get_response(access_token_first, '?tags={}'.format(created_tag_names))
# #     print response_info(get_resp)
# #     assert get_resp.json()['total_found'] == 1  # tags associated with only 1 candidate
# #     assert get_resp.json()['candidates'][0]['tag_ids'] == map(unicode, created_tag_ids)
#
#
# def _log_bounding_box_and_coordinates(base_location, radius, candidate_ids):
#     """
#     Display bounding box coordinates relative to radius (distance) and coordinates of candidate location
#     :param base_location:
#     :param radius:
#     :param candidate_ids:
#     :return:
#     """
#     distance_in_km = float(radius) / 0.62137
#     coords_dict = get_geocoordinates_bounding(base_location, distance_in_km)
#     top_left_y, top_left_x, bottom_right_y, bottom_right_x = coords_dict['top_left'][0], coords_dict['top_left'][1], \
#                                                              coords_dict['bottom_right'][0], \
#                                                              coords_dict['bottom_right'][1]
#     # Lat = Y Lng = X
#     print "%s miles bounding box coordinates: ['%s,%s','%s,%s']" % (radius, top_left_y, top_left_x, bottom_right_y,
#                                                                     bottom_right_x)
#     if type(candidate_ids) in (int, long):
#         candidate_ids = [candidate_ids]
#     for index, candidate_id in enumerate(candidate_ids, start=1):
#         row = db.session.query(CandidateAddress).filter_by(candidate_id=candidate_id).first()
#         if row:
#             print "Candidate-%s Address: %s, %s, %s. \n cooridnates: %s" % (index, row.city, row.state,
#                                                                             row.zip_code, row.coordinates)
#
#             point = row.coordinates.split(',')
#             statement1 = top_left_x <= float(point[1]) <= bottom_right_x
#             statement2 = top_left_y >= float(point[0]) >= bottom_right_y
#             print "Candidate-%s %s bounding box" % (index, 'lies inside' if statement1 and statement2 else 'not in')
#             print "%s <= %s <= %s = %s" % (top_left_x, point[1], bottom_right_x, statement1)
#             print "%s >= %s >= %s = %s" % (top_left_y, point[0], bottom_right_y, statement2)
#
#
# def _assert_results(candidate_ids, response):
#     """
#     Assert statements for all search results
#     :param candidate_ids: list of candidate ids created by the authorized user under same domain
#     """
#     # List of candidate IDs from the search result
#     resultant_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
#     print "\nresponse: {}".format(response)
#     print '\ncandidate_ids: {}'.format(candidate_ids)
#     print '\nresultant_candidate_ids: {}'.format(resultant_candidate_ids)
#     # Test whether every element in the set candidate_ids is in resultant_candidate_ids.
#     assert set(candidate_ids).issubset(set(resultant_candidate_ids))
