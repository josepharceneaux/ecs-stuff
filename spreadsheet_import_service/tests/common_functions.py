"""
    This module has utilities which perform following operations:

        * Generate test data for testing spreadsheet import service
        * Hit endpoints of spreadsheet import service with appropriate parameters and request body
"""
import uuid
import csv
import os
import json
import StringIO
import requests
from spreadsheet_import_service.common.utils.talent_s3 import upload_to_filepicker_s3

SPREADSHEET_IMPORT_HOST = 'http://127.0.0.1:8009/%s'
SPREADSHEET_IMPORT_ENDPOINT = SPREADSHEET_IMPORT_HOST % 'v1/parse_spreadsheet/%s'
CONVERT_TO_TABLE_ENDPOINT = SPREADSHEET_IMPORT_ENDPOINT % 'convert_to_table'
IMPORT_FROM_TABLE_ENDPOINT = SPREADSHEET_IMPORT_ENDPOINT % 'import_from_table'
HEALTH_ENDPOINT = SPREADSHEET_IMPORT_HOST % 'healthcheck'


def import_spreadsheet_candidates(access_token, candidate_data=None, spreadsheet_file_name=None, is_csv=True,
                                  import_candidates=False):

    header_row = ['candidate.formattedName', 'candidate_email.address', 'candidate_phone.value',
                  'candidate_experience.organization', 'candidate_experience.position',
                  'candidate_education.schoolName', 'student_year', 'candidate_address.city', 'candidate_address.state',
                  'candidate_education_degree_bullet.concentrationType', 'area_of_interest.description',
                  'custom_field.3', 'area_of_interest.description', 'candidate_experience.organization',
                  'candidate_experience.position']

    headers = {'Authorization': 'Bearer %s' % access_token, 'Content-Type': 'application/json'}

    if is_csv:

        csv_file = StringIO.StringIO()

        # Write to CSV file
        writer = csv.writer(csv_file, delimiter=',')
        for line in candidate_data:
            writer.writerow(line)

        csv_file.seek(0)
        s3_key_name = str(uuid.uuid4())[0:8] + '.csv'
        spreadsheet_file_data = csv_file.read()
    else:
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, 'test_spreadsheets/{}'.format(spreadsheet_file_name)), 'rb') as spreadsheet_file:
            spreadsheet_file_data = spreadsheet_file.read()
            s3_key_name = str(uuid.uuid4())[0:8] + spreadsheet_file_name.split('.')[1]

    upload_to_filepicker_s3(file_content=spreadsheet_file_data, file_name=s3_key_name)

    if import_candidates:
        response = requests.post(IMPORT_FROM_TABLE_ENDPOINT, headers=headers,
                                 data=json.dumps({"file_picker_key": s3_key_name, 'header_row': header_row}))
    else:
        response = requests.get(CONVERT_TO_TABLE_ENDPOINT, headers=headers, params={'file_picker_key': s3_key_name})

    return response.json(), response.status_code


def candidate_test_data(num_candidates=15):

    candidate_data = []
    for x in xrange(num_candidates):
        random_str = str(uuid.uuid4())[0:6]
        candidate_data.append(['John %s Smith' % random_str, 'johnsmith%s@example.com' % random_str, '408-555-1212',
                               'NVIDIA', 'Embedded Software Developer', 'San Jose State University', 'MS', 'San Jose',
                               'CA', 'Electrical Engineering', 'Production & Development', '24', 'Technology', 'Google',
                               'Summer Software Intern'])
    return candidate_data