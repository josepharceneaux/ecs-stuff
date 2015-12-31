"""
    This test module defines functions to test spreadsheet_import_service

        * test_convert_spreadsheet_to_table: It'll test functionality of '/parse_spreadsheet/convert_to_table' endpoint
        * test_import_candidates_from_spreadsheet: It'll test functionality of '/parse_spreadsheet/import_from_table' endpoint
        * test_health_check: It'll test either the service is up
"""

from spreadsheet_import_service.app import app
from spreadsheet_import_service.common.tests.conftest import *
from spreadsheet_import_service.common.utils.common_functions import add_role_to_test_user
from common_functions import *


def test_convert_spreadsheet_to_table(access_token_first, user_first):

    candidate_data = candidate_test_data()

    # Logged-in user trying to convert a csv spreadsheet to table without appropriate roles
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data)
    assert status_code == 401

    add_role_to_test_user(user_first, ['CAN_ADD_CANDIDATES'])

    # Logged-in user trying to convert a csv spreadsheet to table
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data)

    assert status_code == 200
    for i, row in enumerate(response.get('table')):
        assert row == candidate_data[i]

    # Logged-in user trying to convert a excel spreadsheet to table
    response, status_code = import_spreadsheet_candidates(access_token_first,
                                                          spreadsheet_file_name='test_spreadsheet.xlsx', is_csv=False)

    assert status_code == 200
    assert len(response.get('table')) == 10


def test_import_candidates_from_spreadsheet(access_token_first, user_first):

    candidate_data = candidate_test_data()

    # Logged-in user trying to import 15 candidates from a csv spreadsheet without appropriate roles
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data,
                                                          import_candidates=True)
    assert status_code == 401

    add_role_to_test_user(user_first, ['CAN_ADD_CANDIDATES'])

    # Logged-in user trying to import 15 candidates from a csv spreadsheet
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data,
                                                          import_candidates=True)

    assert status_code == 201
    assert response.get('count') == len(candidate_data)
    assert response.get('status') == 'complete'

    candidate_data = candidate_test_data(501)

    # Logged-in user trying to import 501 candidates from a csv spreadsheet
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data,
                                                          import_candidates=True, is_import_scheduled=True)
    assert response.get('count') == len(candidate_data)
    assert response.get('status') == 'complete'


def test_health_check():
    response = requests.get(HEALTH_ENDPOINT)
    assert response.status_code == 200
