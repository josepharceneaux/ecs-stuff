__author__ = 'ufarooqi'

from flask import request
from . import db, logger, app
from spreadsheet_import_service.common.utils.talent_s3 import *
from spreadsheet_import_service.common.models.user import User
from spreadsheet_import_service.common.models.misc import AreaOfInterest
from spreadsheet_import_service.common.models.candidate import CandidateSource
from spreadsheet_import_service.common.utils.talent_reporting import email_error_to_admins

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
    import xlrd

    book = xlrd.open_workbook(filename=None, file_contents=spreadsheet_file.read())
    first_sheet = book.sheet_by_index(0)

    table = []
    for row_index in range(first_sheet.nrows):
        is_row_empty = True
        cells = first_sheet.row(row_index)  # array of cell objects
        table_row = []
        for cell in cells:
            table_row.append(cell.value)
            if cell.value:
                is_row_empty = False
        if not is_row_empty:
            table.append(table_row)
    return table


def convert_csv_to_table(csv_file):
    """
    Convert a CSV file object to a python table object (array of arrays)
    :param csv_file: python file object
    :return: An array containing rows of csv file
    """
    import csv
    import chardet
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

    except Exception as e:
        csv_table = []
        from spreadsheet_import_service.common.utils.talent_reporting import email_error_to_admins

        email_error_to_admins("Error message: %s\nNew catalog: %s\nCatalog: %s" % (e, catalog, new_catalog),
                              "Error importing CSV")

    return csv_table


def import_from_spreadsheet(*args, **kwargs):
    """
    This function will create new candidates from information of candidates given in a csv file
    :param source_id: Id of candidates source
    :param table: An array of candidate's dicts
    :param spreadsheet_filename: Name of spreadsheet file from which candidates are being imported
    :param header_row: An array of headers of candidate's spreadsheet
    :return: A dictionary containing number of candidates successfully imported
    :rtype: dict
    """
    source_id = kwargs.get('source_id')
    table = kwargs.get('candidates_table') or []
    spreadsheet_filename = kwargs.get('spreadsheet_filename') or []
    header_row = kwargs.get('header_row')

    user_id = request.user.id
    user = User.query.get(user_id)
    domain_id = user.domain_id

    try:

        domain_areas_of_interest = get_or_create_areas_of_interest(user.domain_id, include_child_aois=True)

        logger.info("import CSV table: %s", table)

        candidate_ids = []
        for row in table:
            first_name, middle_name, last_name, formatted_name, status_id,  = None, None, None, None, None
            emails, phones, areas_of_interest, addresses, degrees = [], [], [], [], []
            school_names, work_experiences, educations, custom_fields = [], [], [], []

            this_source_id = source_id

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
                    if column:
                        matching_aoi = domain_areas_of_interest.find(lambda aoi_row: aoi_row.name.lower().
                                                                     replace(' ', '') == column.lower().
                                                                     replace(' ', '')).first()
                        if matching_aoi:
                            areas_of_interest.append({'area_of_interest_id': matching_aoi.id})
                        else:
                            logger.warning("Unknown AOI when importing from CSV, user %s: %s", user_id, column)
                elif column_name == 'candidate_experience.organization':
                    prepare_candidate_data(work_experiences, 'company', column)
                elif column_name == 'candidate_experience.position':
                    prepare_candidate_data(work_experiences, 'position', column)
                elif column_name == 'candidate_education.schoolName':
                    school_names.append(column)
                elif column_name == "candidate_education_degree_bullet.concentrationType":
                    prepare_candidate_data(degrees, 'bullets', {'major': column})
                elif column_name == 'student_year':
                    column = column.lower()
                    import datetime

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
                    elif 'ms' or 'mba' in column:
                        graduation_year = current_year
                        university_start_year = current_year - 2
                        degree_title = 'Masters'

                    prepare_candidate_data(degrees, 'title', degree_title)
                    prepare_candidate_data(degrees, 'start_year', university_start_year)
                    prepare_candidate_data(degrees, 'end_year', graduation_year)
                    prepare_candidate_data(degrees, 'start_month', 6)
                    prepare_candidate_data(degrees, 'end_month', 6)

                elif column_name == 'candidate_address.city':
                    prepare_candidate_data(addresses, 'city', column)
                elif column_name == 'candidate_address.state':
                    prepare_candidate_data(addresses, 'state', column)
                elif column_name == 'candidate_address.zipCode':
                    prepare_candidate_data(addresses, 'zip_code', column)
                elif 'custom_field.' in column_name:
                    custom_fields_dict = {}
                    if isinstance(column, basestring):
                        custom_fields_dict['custom_field_id'] = int(column_name.split('.')[1])
                        custom_fields_dict['value'] = column.strip()
                    if custom_fields_dict:
                        custom_fields.append(custom_fields_dict)

                number_of_educations = max(len(degrees), len(school_names))

            # Prepare candidate educational data
            for index in range(0, number_of_educations):
                education = {}
                if index < len(school_names):
                    education['school_name'] = school_names[index]

                if index < len(degrees):
                    education['degrees'] = [degrees[index]]

                educations.append(education)

            result = create_candidates_from_parsed_spreadsheet(dict(full_name=formatted_name,
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
                                                                    areas_of_interest=areas_of_interest,
                                                                    custom_fields=custom_fields))

            candidate_ids.append(result['candidate_id'])

        # TODO: Upload candidate documents to cloud

        delete_from_s3(spreadsheet_filename, 'CSVResumes')

        logger.info("Successfully imported %s candidates from CSV: User %s", len(candidate_ids), user.id)
        return dict(count=len(candidate_ids), status='complete')

    except Exception:
        email_error_to_admins("Error importing from CSV. User ID: %s, S3 filename: %s" % (user_id, spreadsheet_filename),
                              subject="import_from_csv")
        raise InvalidUsage("Error importing from CSV. User ID: %s, S3 filename: %s", user_id, spreadsheet_filename)


def get_or_create_areas_of_interest(domain_id, include_child_aois=False):
    """
    This function will create or get the areas of interest of a given domain
    :param domain_id: Id of domain
    :param include_child_aois: Do you want to include child areas_of_interest ?
    :return: A Dictionary containing Areas_of_interest of a given domain
    :rtype: list
    """
    if not domain_id:
        logger.error("get_or_create_areas_of_interest: domain_id is %s!", domain_id)

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
        areas = areas.find(lambda aoi: not aoi.parent_id)

    return areas


def create_candidates_from_parsed_spreadsheet(candidate_dict):
    """
    Create a new candidate using candidate_service
    :param candidate_dict: Dict containing information of new candidate
    :return: A dictionary containing IDs of newly created candidates
    :rtype: dict
    """
    import json, requests
    r = requests.post(app.config['CANDIDATE_CREATION_URI'], data=json.dumps({'candidates': [candidate_dict]}),
                      headers={'Authorization': request.oauth_token})
    return json.loads(r.text)


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