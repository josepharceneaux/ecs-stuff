"""
    This module defines following utilities:

    * Convert Spreadsheet to Table: This utility will convert a spreadsheet file object to JSON Array
    * Convert CSV to Table: This utility will convert a csv file object to JSON Array
    * Import Candidates from Spreadsheet: This utility will create candidates from JSON Array of candidate data

"""
import datetime
import xlrd
import csv
import chardet
import json
import requests
from flask import request, jsonify
from spreadsheet_import_service.app import logger, app, celery_app
from spreadsheet_import_service.common.utils.talent_s3 import *
from spreadsheet_import_service.common.models.user import User, db
from spreadsheet_import_service.common.models.misc import AreaOfInterest
from spreadsheet_import_service.common.models.candidate import CandidateSource
from spreadsheet_import_service.common.utils.talent_reporting import email_error_to_admins
from spreadsheet_import_service.common.error_handling import InvalidUsage
from spreadsheet_import_service.common.error_handling import InternalServerError
from spreadsheet_import_service.common.routes import CandidateApiUrl, SchedulerApiUrl, SpreadsheetImportApiUrl


DEFAULT_AREAS_OF_INTEREST = ['Production & Development', 'Marketing', 'Sales', 'Design', 'Finance',
                             'Business & Legal Affairs', 'Human Resources', 'Technology', 'Other']


def convert_spreadsheet_to_table(spreadsheet_file, filename):
    """
    Convert a spreadsheet file object to a python table object (array of arrays)
    :param spreadsheet_file: python file object
    :param filename: spreadsheet file name
    :return: An array containing rows of spreadsheets
    """
    is_csv = ".csv" in filename
    if is_csv:
        return convert_csv_to_table(spreadsheet_file)

    book = xlrd.open_workbook(filename=None, file_contents=spreadsheet_file.read())
    first_sheet = book.sheet_by_index(0)

    table = []
    for row_index in range(first_sheet.nrows):
        cells = first_sheet.row(row_index)  # array of cell objects

        cell_values = []
        for cell in cells:
            cell_value = cell.value
            if isinstance(cell_value, float):  # there should be no float-type data
                cell_value = str(int(cell_value))
            if cell_value:
                cell_values.append(cell_value)

        table.append(cell_values)
    table = [row for row in table if row]
    return table


def convert_csv_to_table(csv_file):
    """
    Convert a CSV file object to a python table object (array of arrays)
    :param csv_file: python file object
    :return: An array containing rows of csv file
    """
    catalog = None
    new_catalog = []
    try:
        # Guess dialect with sniffer and read in CSV
        dialect = csv.Sniffer().sniff(csv_file.readline())
        csv_file.seek(0)
        catalog = csv.reader(csv_file.read().splitlines(), dialect=dialect)
        csv_table = []

        # First, count maximum number of columns in any row. This will be # of cols in table
        num_columns = 0
        for row in catalog:
            if len(row) > num_columns:
                num_columns = len(row)
            new_catalog.append(row)

        # Make new candidates from CSV results
        for row in new_catalog:
            row_array = []
            is_row_empty = True
            for column_index in range(num_columns):  # 0, ..., num_columns-1
                column = row[column_index] if len(row) > column_index else ''
                if column:
                    is_row_empty = False  # to ignore empty rows
                row_array.append(column.strip(' ').decode(chardet.detect(column.strip(' '))['encoding'] or 'cp1252'))
            if not is_row_empty:
                csv_table.append(row_array)
        return csv_table

    except Exception as e:
        from spreadsheet_import_service.common.utils.talent_reporting import email_error_to_admins
        email_error_to_admins("Error message: %s\nNew catalog: %s\nCatalog: %s" % (e, catalog, new_catalog),
                              "Error importing CSV")
        raise InvalidUsage(error_message="Error importing csv because %s" % e.message)


@celery_app.task()
def import_from_spreadsheet(table, spreadsheet_filename, header_row, talent_pool_ids,
                            oauth_token, user_id, is_scheduled=False, source_id=None):
    """
    This function will create new candidates from information of candidates given in a csv file
    :param source_id: Id of candidates source
    :param table: An array of candidate's dicts
    :param spreadsheet_filename: Name of spreadsheet file from which candidates are being imported
    :param header_row: An array of headers of candidate's spreadsheet
    :param talent_pool_ids: An array on talent_pool_ids
    :param oauth_token: OAuth token of logged-in user
    :param is_scheduled: Is this method called asynchronously ?
    :param user_id: User id of logged-in user
    :return: A dictionary containing number of candidates successfully imported
    :rtype: dict
    """

    assert table
    assert spreadsheet_filename
    assert header_row

    user = User.query.get(user_id)
    domain_id = user.domain_id

    try:

        domain_areas_of_interest = get_or_create_areas_of_interest(user.domain_id, include_child_aois=True)

        candidate_ids, error_messages = [], []
        for i in xrange(0, len(table), 50):
            candidates_list = []
            for row in table[i: i + 50]:
                first_name, middle_name, last_name, formatted_name, status_id,  = None, None, None, None, None
                emails, phones, areas_of_interest, addresses, degrees = [], [], [], [], []
                school_names, work_experiences, educations, custom_fields = [], [], [], []
                talent_pool_dict = {'add': talent_pool_ids}

                this_source_id = source_id

                number_of_educations = 0

                for column_index, column in enumerate(row):
                    if column_index >= len(header_row):
                        continue
                    column_name = header_row[column_index]
                    if not column_name or not column:
                        continue

                    if column_name == 'candidate.formattedName':
                        formatted_name = column
                    elif column_name == 'candidate.statusId':
                        status_id = column
                    elif column_name == 'candidate.firstName':
                        first_name = column
                    elif column_name == 'candidate.middleName':
                        middle_name = column
                    elif column_name == 'candidate.lastName':
                        last_name = column
                    elif column_name == 'candidate_email.address':
                        emails.append({'address': column})
                    elif column_name == 'candidate_phone.value':
                            phones.append({'value': column})
                    elif column_name == 'candidate.source':
                        source = CandidateSource.query.filter_by(description=column, domain_id=domain_id).all()
                        if len(source):
                            this_source_id = source[0].id
                        else:
                            source = CandidateSource(description=column, domain_id=domain_id)
                            db.session.add(source)
                            db.session.commit()
                            this_source_id = source.id
                    elif column_name == 'area_of_interest.description':
                        column = column.strip()
                        matching_areas_of_interest = filter(lambda aoi_row: aoi_row.name.lower().
                                                            replace(' ', '') == column.lower().replace(' ', ''),
                                                            domain_areas_of_interest)
                        if matching_areas_of_interest:
                            areas_of_interest.append({'area_of_interest_id': matching_areas_of_interest[0].id})
                        else:
                            logger.warning("Unknown AOI when importing from CSV, user %s: %s", user_id, column)
                    elif column_name == 'candidate_experience.organization':
                        prepare_candidate_data(work_experiences, 'organization', column)
                    elif column_name == 'candidate_experience.position':
                        prepare_candidate_data(work_experiences, 'position', column)
                    elif column_name == 'candidate_education.schoolName':
                        school_names.append(column)
                    elif column_name == "candidate_education_degree_bullet.concentrationType":
                        prepare_candidate_data(degrees, 'bullets', [{'major': column}])
                    elif column_name == 'student_year':
                        column = column.lower()
                        current_year = datetime.datetime.now().year
                        if 'freshman' in column:
                            graduation_year = current_year + 3
                            university_start_year = current_year - 1  # TODO this is a bug lol
                            degree_title = 'Bachelors'
                        elif 'sophomore' in column:
                            graduation_year = current_year + 2
                            university_start_year = current_year - 2
                            degree_title = 'Bachelors'
                        elif 'junior' in column:
                            graduation_year = current_year + 1
                            university_start_year = current_year - 3
                            degree_title = 'Bachelors'
                        elif 'senior' in column:
                            graduation_year = current_year
                            university_start_year = current_year - 4
                            degree_title = 'Bachelors'
                        elif 'ms' in column or 'mba' in column:
                            graduation_year = current_year
                            university_start_year = current_year - 2
                            degree_title = 'Masters'
                        else:
                            continue

                        prepare_candidate_data(degrees, 'title', degree_title)
                        prepare_candidate_data(degrees, 'start_year', university_start_year)
                        prepare_candidate_data(degrees, 'end_year', graduation_year)
                        prepare_candidate_data(degrees, 'start_month', 6)
                        prepare_candidate_data(degrees, 'end_month', 6)

                    elif column_name == 'candidate_address.address_line_1':
                        prepare_candidate_data(addresses, 'address_line_1', column)
                    elif column_name == 'candidate_address.address_line_2':
                        prepare_candidate_data(addresses, 'address_line_2', column)
                    elif column_name == 'candidate_address.city':
                        prepare_candidate_data(addresses, 'city', column)
                    elif column_name == 'candidate_address.state':
                        prepare_candidate_data(addresses, 'state', column)
                    elif column_name == 'candidate_address.subdivision_code':
                        prepare_candidate_data(addresses, 'subdivision_code', column)
                    elif column_name == 'candidate_address.zipCode':
                        prepare_candidate_data(addresses, 'zip_code', column)
                    elif column_name == 'candidate_address.country_code':
                        prepare_candidate_data(addresses, 'country_code', column)
                    elif 'custom_field.' in column_name:
                        custom_fields_dict = {}
                        if isinstance(column, basestring):
                            custom_fields_dict['custom_field_id'] = int(column_name.split('.')[1])
                            custom_fields_dict['value'] = column.strip()
                        if custom_fields_dict:
                            custom_fields.append(custom_fields_dict)
                    elif 'talent_pool.' in column_name:
                        if isinstance(column, basestring):
                            talent_pool_dict['add'].append(int(column_name.split('.')[1]))

                    number_of_educations = max(len(degrees), len(school_names))

                # Prepare candidate educational data
                for index in range(0, number_of_educations):
                    education = {}
                    if index < len(school_names):
                        education['school_name'] = school_names[index]

                    if index < len(degrees):
                        education['degrees'] = [degrees[index]]

                    educations.append(education)

                candidates_list.append(dict(full_name=formatted_name,
                                            status_id=status_id,
                                            first_name=first_name,
                                            middle_name=middle_name,
                                            last_name=last_name,
                                            emails=emails,
                                            phones=phones,
                                            work_experiences=work_experiences,
                                            educations=educations,
                                            addresses=addresses,
                                            source_id=this_source_id,
                                            talent_pool_ids=talent_pool_dict,
                                            areas_of_interest=areas_of_interest,
                                            custom_fields=custom_fields))

            status_code, response = create_candidates_from_parsed_spreadsheet(candidates_list, oauth_token)

            if status_code == 201:
                response_candidate_ids = [candidate.get('id') for candidate in response.get('candidates')]
                candidate_ids += response_candidate_ids
                logger.info("Successfully imported %s candidates with ids: (%s)", len(response_candidate_ids), response_candidate_ids)
            else:  # continue with the rest of the spreadsheet imports despite errors returned from candidate-service
                error_messages.append(response.get('error'))
                logger.error(response.get('error'))
                continue

        delete_from_s3(spreadsheet_filename, 'CSVResumes')

        logger.info("Successfully imported %s candidates from CSV: User %s, Error Messages %s" % (len(
                candidate_ids), user.id, error_messages))
        if not is_scheduled:
            return jsonify(dict(count=len(candidate_ids), status='complete', error_messages=error_messages)), 201

    except Exception as e:
        email_error_to_admins("Error importing from CSV. User ID: %s, S3 filename: %s, S3_URL: %s" %
                              (user_id, spreadsheet_filename, get_s3_url('CSVResumes', spreadsheet_filename)),
                              subject="import_from_csv")
        raise InvalidUsage(error_message="Error importing from CSV. User ID: %s, S3 filename: %s. Reason: %s" %
                                         (user_id, spreadsheet_filename, e.message))


def get_or_create_areas_of_interest(domain_id, include_child_aois=False):
    """
    This function will create or get the areas of interest of a given domain
    :param domain_id: Id of domain
    :param include_child_aois: Do you want to include child areas_of_interest ?
    :return: A Dictionary containing Areas_of_interest of a given domain
    :rtype: list
    """
    if not domain_id:
        raise InvalidUsage(error_message="get_or_create_areas_of_interest: domain_id is not provided")

    areas = AreaOfInterest.get_domain_areas_of_interest(domain_id) or []

    # If no AOIs exist, create them
    if not len(areas):
        for name in DEFAULT_AREAS_OF_INTEREST:
            area_of_interest = AreaOfInterest(name=name, domain_id=domain_id)
            db.session.add(area_of_interest)
            areas.append(area_of_interest)
        db.session.commit()

    # If we only want parent AOIs, must filter for all AOIs that don't have parentIds
    if not include_child_aois:
        areas = filter(lambda aoi: not aoi.parent_id, areas)

    return areas


def create_candidates_from_parsed_spreadsheet(candidate_dicts, oauth_token):
    """
    Create a new candidate using candidate_service
    :param candidate_dicts: A list of dicts containing information for new candidates
    :param oauth_token: OAuth token of logged-in user
    :return: A dictionary containing IDs of newly created candidates
    :rtype: dict
    """
    r = requests.post(CandidateApiUrl.CANDIDATES, data=json.dumps({'candidates': candidate_dicts}),
                      headers={'Authorization': oauth_token, 'content-type': 'application/json'})

    try:
        return r.status_code, r.json()
    except:
        return r.status_code, {"error": "Couldn't create candidate from candidate dict %s" % candidate_dict}


def prepare_candidate_data(data_array, key, value):
    """
    Prepare candidate data arrays
    :param data_array: Array of data like work_experiences
    :param key: Key of the array data which is going to be appended
    :param value: Value of the data
    :return: None
    """
    for data in data_array:
        if key not in data:
            data[key] = value
            return

    data_array.append({key: value})


def schedule_spreadsheet_import(import_args):

    data = {
        "task_type": "one_time",
        "run_datetime": str(datetime.datetime.utcnow() + datetime.timedelta(seconds=10)),
        "url": SpreadsheetImportApiUrl.IMPORT_CANDIDATES,
        "post_data": import_args
    }
    headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}
    try:
        print SchedulerApiUrl.TASKS
        response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))
        print response
        if response.status_code != 201:
            raise Exception("Status Code: %s, Response: %s" % (response.status_code, response.json()))

    except Exception as e:
        raise InternalServerError("Couldn't schedule Spreadsheet import using scheduling service "
                                  "because: %s" % e.message)