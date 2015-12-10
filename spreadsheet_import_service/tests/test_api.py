__author__ = 'ufarooqi'

from spreadsheet_import_service.spreadsheet_import_app import app
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

    # Logged-in user trying to convert a csv spreadsheet to table without appropriate roles
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data,
                                                          import_candidates=True)
    assert status_code == 401

    add_role_to_test_user(user_first, ['CAN_ADD_CANDIDATES'])

    # Logged-in user trying to convert a csv spreadsheet to table
    response, status_code = import_spreadsheet_candidates(access_token_first, candidate_data=candidate_data,
                                                          import_candidates=True)

    assert status_code == 201
    assert response.get('count') == len(candidate_data)
    assert response.get('status') == 'complete'


def test_health_check():
    import requests
    response = requests.get('http://127.0.0.1:8009/healthcheck')
    assert response.status_code == 200
