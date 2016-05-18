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
import random
from faker import Faker
from nameparser import HumanName
from spreadsheet_import_service.common.tests.fake_testing_data_generator import college_majors
from spreadsheet_import_service.app import app
from spreadsheet_import_service.common.utils.talent_s3 import upload_to_filepicker_s3
from spreadsheet_import_service.common.routes import SpreadsheetImportApiUrl

fake = Faker()


def import_spreadsheet_candidates(talent_pool_id, access_token, candidate_data=None,
                                  spreadsheet_file_name=None, is_csv=True,
                                  import_candidates=False, domain_custom_field=None):
    if domain_custom_field:
        custom_field = 'custom_field.{}'.format(domain_custom_field.id)
    else:
        custom_field = 'custom_field.3'

    header_row = [
        'candidate.formattedName', 'candidate.firstName', 'candidate.middleName', 'candidate.lastName',
        'candidate_email.address', 'candidate_phone.value', 'candidate_address.address_line_1',
        'candidate_address.address_line_2', 'candidate_address.city', 'candidate_address.state',
        'candidate_address.zipCode', 'candidate_address.country_code', 'candidate.objective',
        'candidate_experience.organization', 'candidate_experience.position',
        'candidate_education.schoolName', 'candidate_education_degree_bullet.concentrationType', 'student_year',
        'candidate.source', 'area_of_interest.description', 'candidate.notes', custom_field
    ]

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
        with open(os.path.join(current_dir, 'test_spreadsheets/{}'.format(spreadsheet_file_name)),
                  'rb') as spreadsheet_file:
            spreadsheet_file_data = spreadsheet_file.read()
            s3_key_name = str(uuid.uuid4())[0:8] + spreadsheet_file_name.split('.')[1]

    with app.app_context():
        upload_to_filepicker_s3(file_content=spreadsheet_file_data, file_name=s3_key_name)

    if import_candidates:
        response = requests.post(SpreadsheetImportApiUrl.IMPORT_CANDIDATES, headers=headers,
                                 data=json.dumps({"file_picker_key": s3_key_name, 'header_row': header_row,
                                                  'talent_pool_ids': [talent_pool_id]}))
    else:
        response = requests.get(SpreadsheetImportApiUrl.CONVERT_TO_TABLE, headers=headers,
                                params={'file_picker_key': s3_key_name})

    return response.json(), response.status_code


def candidate_test_data(num_candidates=15):
    candidate_data = []
    for x in xrange(num_candidates):
        # TODO: Generate random international phone number

        # Generate full name & parse full name to easily extract first, middle, and last name
        full_name = fake.name()
        parsed_full_name = HumanName(full_name)

        # Randomly select a discipline, e.g. Engineering, Mathematics, Agriculture
        discipline = random.choice(college_majors().keys())
        candidate_data.append(
            [
                full_name, parsed_full_name.first, parsed_full_name.middle, parsed_full_name.last, fake.safe_email(),
                '+14084059988', fake.street_address(), fake.street_address(), fake.city(), fake.state(), fake.zipcode(),
                fake.country_code(), fake.bs(), fake.company(), fake.job(), fake.first_name() + ' University',
                random.choice(college_majors()[discipline]), fake.year(), '', fake.job(), fake.bs(), '24'
            ]
        )
    return candidate_data
