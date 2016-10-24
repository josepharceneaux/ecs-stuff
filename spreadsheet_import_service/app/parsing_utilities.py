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
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import literal
from spreadsheet_import_service.app import logger, app, celery_app
from spreadsheet_import_service.common.utils.talent_s3 import *
from spreadsheet_import_service.common.utils.validators import is_valid_email, is_number
from spreadsheet_import_service.common.models.user import User, db
from spreadsheet_import_service.common.models.misc import AreaOfInterest
from spreadsheet_import_service.common.models.candidate import CandidateSource, SocialNetwork
from spreadsheet_import_service.common.utils.talent_reporting import email_error_to_admins, email_notification_to_admins
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
            if isinstance(cell_value, basestring):
                cell_value = cell_value.strip()
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
                            oauth_token, user_id, is_scheduled=False, source_id=None,
                            formatted_candidate_tags=None):
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
    :type formatted_candidate_tags: list[dict[str]]
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

        candidate_ids, erroneous_data = [], []
        candidate_tags = formatted_candidate_tags or []

        for i, row in enumerate(table):
            # Candidate state variables: These can be populated for each candidate
            first_name, middle_name, last_name, formatted_name, status_id = None, None, None, None, None
            summary = None
            emails, phones, areas_of_interest, addresses, degrees, candidate_notes = [], [], [], [], [], []
            school_names, work_experiences, educations, custom_fields, social_networks = [], [], [], [], []
            skills = []

            talent_pool_dict = {'add': talent_pool_ids}
            this_source_id = source_id
            number_of_educations = 0

            # Go through each row of the spreadsheet and set the state variables
            for column_index, column in enumerate(row):
                if column_index >= len(header_row):
                    continue
                column_name = header_row[column_index]
                if not column_name or not column:
                    continue

                if column_name == 'candidate.formattedName':
                    formatted_name = column
                elif column_name == 'candidate.statusId':
                    status_id = int(column) if is_number(column) else column
                elif column_name == 'candidate.firstName':
                    first_name = column
                elif column_name == 'candidate.middleName':
                    middle_name = column
                elif column_name == 'candidate.lastName':
                    last_name = column
                elif column_name == 'candidate.summary':
                    summary = column
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

                # `graduation_year` and `student_year` are mutually exclusive i.e. they cannot come together
                elif column_name == 'candidate_education.graduation_year' and is_number(column):
                    prepare_candidate_data(degrees, 'end_year', int(column))
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
                elif column_name == 'candidate.tags':
                    prepare_candidate_data(candidate_tags, 'name', column)
                elif column_name == 'candidate.skills':
                    if ',' in column:
                        # Comma Separated Skills
                        column = [skill.strip() for skill in column.split(',') if skill.strip()]
                        for skill in column:
                            prepare_candidate_data(skills, 'name', skill)
                    else:
                        prepare_candidate_data(skills, 'name', column)
                elif column_name == 'candidate.notes':
                    prepare_candidate_data(candidate_notes, 'comment', column)
                elif column_name == 'candidate.social_profile_url':
                    social_network_object = SocialNetwork.query.filter(literal(column.lower()).contains(
                            func.lower(SocialNetwork.name))).first()
                    if social_network_object:
                        prepare_candidate_data(social_networks, 'profile_url', column)
                        prepare_candidate_data(social_networks, 'name', social_network_object.name)
                    else:
                        logger.warning("Couldn't add social profile url: (%s) of candidate ", column)

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

            # Create candidate object based on candidate state variables
            candidate_data = dict(full_name=formatted_name,
                                  status_id=status_id,
                                  first_name=first_name,
                                  middle_name=middle_name,
                                  last_name=last_name,
                                  summary=summary,
                                  emails=emails,
                                  phones=phones,
                                  work_experiences=work_experiences,
                                  educations=educations,
                                  addresses=addresses,
                                  source_id=this_source_id,
                                  social_networks=social_networks,
                                  talent_pool_ids=talent_pool_dict,
                                  areas_of_interest=areas_of_interest,
                                  custom_fields=custom_fields,
                                  skills=skills)

            # Remove null values from candidate object
            candidate_data = {key: value for key, value in candidate_data.items() if value is not None}

            # Create the candidate and handle the response
            created, response = create_candidates_from_parsed_spreadsheet(candidate_data, oauth_token)
            if created:
                response_candidate_ids = [candidate.get('id') for candidate in response.get('candidates', [])]
                candidate_ids += response_candidate_ids

                # Adding Notes and Tags to Candidate Object
                if response_candidate_ids:
                    add_extra_fields_to_candidate(response_candidate_ids[0], oauth_token,
                                                  tags=candidate_tags,
                                                  notes=candidate_notes)

                logger.info("Successfully imported %s candidates with ids: (%s)",
                            len(response_candidate_ids), response_candidate_ids)
            else:
                # Continue with the rest of the spreadsheet imports despite errors returned from candidate-service
                logger.info("SpreadSheet Import Service: Could not import candidate row %s: `%s` in file: `%s`",
                            i, row, get_s3_url('CSVResumes', spreadsheet_filename))
                row.insert(0, i + 1)  # Make row number first element in array
                erroneous_data.append(row)
                continue

        logger.info("SpreadSheet Import Service: Successfully imported %s candidates from CSV: User %s" % (
            len(candidate_ids), user.id))

        if erroneous_data:
            erroneous_data_str = '\n'.join(map(str, erroneous_data))
            msg_body = """
            import_from_spreadsheet: Some candidates not imported.
            User ID: %s
            S3_URL: %s
            Erroneous rows (%s):
            %s"""
            email_notification_to_admins(msg_body % (user_id,
                                                     get_s3_url('CSVResumes', spreadsheet_filename),
                                                     len(erroneous_data),
                                                     erroneous_data_str),
                                         subject="import_from_csv")

        if not is_scheduled:
            return jsonify(dict(count=len(candidate_ids), status='complete')), 201

    except Exception as e:
        logger.exception("Error importing from CSV (outer loop), user ID: %s, S3 filename: %s", user_id,
                         spreadsheet_filename)
        email_error_to_admins("Error importing from CSV. User ID: %s, S3_URL: %s, Error: %s" % (
            user_id, get_s3_url('CSVResumes', spreadsheet_filename), e), subject="import_from_csv")
        message = "Error importing from CSV. User ID: %s, S3 filename: %s. Reason: %s" % (
            user_id, spreadsheet_filename, e)
        if not is_scheduled:
            raise InternalServerError(message)


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


def create_candidates_from_parsed_spreadsheet(candidate_dict, oauth_token):
    """
    Create a new candidate using candidate_service
    :param candidate_dict: A list of dicts containing information for new candidates
    :param oauth_token: OAuth token of logged-in user
    :return: A dictionary containing IDs of newly created candidates
    :rtype: dict
    """
    headers = {'Authorization': oauth_token, 'content-type': 'application/json'}
    r = requests.post(CandidateApiUrl.CANDIDATES,
                      data=json.dumps({'candidates': [candidate_dict]}),
                      headers=headers)

    status_code = r.status_code

    try:
        candidates_response = r.json()
        if status_code != requests.codes.CREATED:
            if candidates_response.get('error', {}).get('id'):
                candidate_dict['id'] = candidates_response.get('error', {}).get('id')
                is_updated, update_response = update_candidate_from_parsed_spreadsheet(candidate_dict, oauth_token)
                if is_updated:
                    return True, update_response
                else:
                    return False, update_response
            else:
                return False, candidates_response
        else:
            return True, candidates_response

    except:
        return False, {"error": "Couldn't create/update candidate from candidate dict %s" % candidate_dict}


def add_extra_fields_to_candidate(candidate_id, oauth_token, tags=None, notes=None):
    """
    This endpoint will add such fields to candidate object that cannot be added through Candidate API
    :param candidate_id: Id of candidate
    :param oauth_token: OAuth token
    :param secret_key_id: Secret key ID if V2 (JWT) auth
    :param tags: Candidate Tags
    :param notes: Candidate Notes
    :return:
    """
    headers = {'Authorization': oauth_token, 'content-type': 'application/json'}
    if tags:
        response = requests.post(CandidateApiUrl.TAGS % str(candidate_id), headers=headers,
                                 data=json.dumps({'tags': tags}))
        if response.status_code != 201:
            logger.error("Couldn't add Tags to candidate with id: %s. Response:", str(candidate_id), response)

    if notes:
        response = requests.post(CandidateApiUrl.NOTES % str(candidate_id), headers=headers,
                                 data=json.dumps({'notes': notes}))
        if response.status_code != 201:
            logger.error("Couldn't add Notes to candidate with id: %s. Response:", str(candidate_id), response)


def update_candidate_from_parsed_spreadsheet(candidate_dict, oauth_token):
    """
    This method will update an already existing candidates from candidate dict
    :param candidate_dict: Dictionaries of candidates to be cretaed
    :param oauth_token:
    :return:
    """
    headers = {'Authorization': oauth_token, 'content-type': 'application/json'}
    r = requests.patch(CandidateApiUrl.CANDIDATES, data=json.dumps({'candidates': [candidate_dict]}),
                       headers=headers)

    if r.status_code == 200:
        return True, r.json()
    else:
        return False, r.json()


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


