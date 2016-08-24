"""
    This test module defines functions to test spreadsheet_import_service

        * test_convert_spreadsheet_to_table: It'll test functionality of '/parse_spreadsheet/convert_to_table' endpoint
        * test_import_candidates_from_spreadsheet: It'll test functionality of '/parse_spreadsheet/import_from_table' endpoint
        * test_health_check: It'll test either the service is up
"""
from time import sleep
from spreadsheet_import_service.common.tests.conftest import *
from spreadsheet_import_service.common.utils.test_utils import send_request, response_info
from spreadsheet_import_service.common.routes import CandidateApiUrl
from common_functions import candidate_test_data, import_spreadsheet_candidates, SpreadsheetImportApiUrl


def test_convert_spreadsheet_to_table(access_token_first, user_first, domain_custom_fields,
                                      talent_pool):
    print "user: {}".format(user_first)
    domain_custom_field = domain_custom_fields[0]
    candidate_data = candidate_test_data()


    # Logged-in user trying to convert a csv spreadsheet to table
    # from candidate_service.tests.api.helpers import response_info
    response, status_code = import_spreadsheet_candidates(talent_pool,
                                                          access_token_first, candidate_data=candidate_data,
                                                          domain_custom_field=domain_custom_field)
    print "\nresponse_content: {}".format(response)

    assert status_code == 200
    for i, row in enumerate(response.get('table')):
        assert row == candidate_data[i]

    # Logged-in user trying to convert a excel spreadsheet to table
    response, status_code = import_spreadsheet_candidates(talent_pool,
            access_token_first, spreadsheet_file_name='test_spreadsheet_2.xls', is_csv=False,
            domain_custom_field=domain_custom_field)

    assert status_code == 200
    assert len(response.get('table')) == 10


def test_import_candidates_from_spreadsheet(access_token_first, user_first, talent_pool,
                                            domain_custom_fields):
    print "user: {}".format(user_first)
    candidate_data = candidate_test_data()

    # Logged-in user trying to import 15 candidates from a csv spreadsheet
    response, status_code = import_spreadsheet_candidates(talent_pool.id, access_token=access_token_first,
                                                          candidate_data=candidate_data, import_candidates=True,
                                                          domain_custom_field=domain_custom_fields[0])
    print "\nresponse_content: {}".format(response)
    assert status_code == 201
    assert response.get('count') == len(candidate_data)
    assert response.get('status') == 'complete'

    candidate_data = candidate_test_data(501)

    # Logged-in user trying to import 501 candidates from a csv spreadsheet
    response, status_code = import_spreadsheet_candidates(talent_pool.id, access_token_first,
                                                          candidate_data=candidate_data, import_candidates=True,
                                                          domain_custom_field=domain_custom_fields[0])
    assert response.get('count') == len(candidate_data)
    assert response.get('status') == 'pending'

    sleep(10)


def test_health_check():
    response = requests.get(SpreadsheetImportApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(SpreadsheetImportApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == 200


def test_import_candidates_from_file(access_token_first, talent_pool, domain_custom_fields):

    # Logged-in user trying to import 15 candidates from a csv spreadsheet
    # Candidates with erroneous data will not be added, so the count will reflect only successfully added candidates
    response, status_code = import_spreadsheet_candidates(
        talent_pool_id=talent_pool.id, access_token=access_token_first,
        spreadsheet_file_name="test_spreadsheet_2.xls", is_csv=False, import_candidates=True,
        domain_custom_field=domain_custom_fields[0]
    )
    print "\nresponse_content: {}".format(response)
    assert status_code == 201
    assert response.get('status') == 'complete'

    # Another file containing candidates' addresses too
    response, status_code = import_spreadsheet_candidates(
        talent_pool_id=talent_pool.id, access_token=access_token_first,
        spreadsheet_file_name="chineese_eng.xls", is_csv=False, import_candidates=True,
        domain_custom_field=domain_custom_fields[0]
    )
    print "\nresponse_content: {}".format(response)
    assert status_code == 201
    assert response.get('status') == 'complete'


def test_create_candidate_from_excel_file(access_token_first, talent_pool, domain_custom_fields):
    """
    Test:  Import, parse, and create candidates from excel file. If a candidate already exists, it should
             still continue with the rest of the candidates
    """
    # Create candidate
    data = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]},
                            'emails': [{'address': 'Wadlejitu86+22222@gmail.com'}]}]}
    create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
    print response_info(create_resp)

    # Logged-in user trying to import 15 candidates from a csv spreadsheet
    response, status_code = import_spreadsheet_candidates(
        talent_pool_id=talent_pool.id, access_token=access_token_first,
        spreadsheet_file_name="test_spreadsheet_2.xls", is_csv=False, import_candidates=True,
        domain_custom_field=domain_custom_fields[0]
    )
    print "\nresponse_content: {}".format(response)
    assert status_code == 201
    assert response.get('status') == 'complete'


class TestCreateCandidateFromExcelFile(object):
    """
    Class contains functional tests that attempt to create candidate(s) via an excel file
    """
    pass
    # def test_candidate_with_tags_and_skills(self, access_token_first, talent_pool, domain_custom_fields):
    #     """
    #     Test: Add candidates with tags & skills column
    #     """
    #     response, status_code = import_spreadsheet_candidates(talent_pool_id=talent_pool.id,
    #                                                           access_token=access_token_first,
    #                                                           spreadsheet_file_name="tags_skills.xls",
    #                                                           is_csv=False,
    #                                                           import_candidates=True,
    #                                                           domain_custom_field=domain_custom_fields[0])
    #     print "\nstatus_code: {}".format(status_code)
    #     print "\nresponse: {}".format(response)
    #     assert status_code == requests.codes.CREATED
    #     assert response.get('status') == 'complete'
