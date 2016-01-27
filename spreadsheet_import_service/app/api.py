"""
    This module defines endpoints to create candidates and get candidate
    data from spreadsheet
"""

from flask import Blueprint, jsonify
from flask import request

from . import logger
from .parsing_utilities import convert_spreadsheet_to_table, import_from_spreadsheet, schedule_spreadsheet_import
from spreadsheet_import_service.common.error_handling import InvalidUsage
from spreadsheet_import_service.common.routes import SpreadsheetImportApi
from spreadsheet_import_service.common.utils.auth_utils import require_oauth, require_all_roles
from spreadsheet_import_service.common.utils.talent_s3 import *
from spreadsheet_import_service.common.models.user import DomainRole

mod = Blueprint('spreadsheet_import_api', __name__)

HEADER_ROW_PARAMS = ['first_name', 'last_name', 'email']


@mod.route(SpreadsheetImportApi.CONVERT_TO_TABLE, methods=['GET'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_ADD_CANDIDATES)
def spreadsheet_to_table():
    """
    POST /parse_spreadsheet/convert_to_table:  Convert given spreadsheet to table of candidates
    Input: {'file_picker_key': 'XDmR4dqbz56OWgdNkvP8.csv'}

    :return A dictionary containing row of candidates
    :rtype: dict
    """

    file_picker_key = request.args.get('file_picker_key', '')
    if not file_picker_key:
        raise InvalidUsage(error_message="A valid file_picker_key should be provided")

    file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
    file_obj = download_file(file_picker_bucket, file_picker_key)

    csv_table = convert_spreadsheet_to_table(file_obj, file_picker_key)
    first_rows = csv_table[:10]

    return jsonify(dict(table=first_rows))


@mod.route(SpreadsheetImportApi.IMPORT_CANDIDATES, methods=['POST'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_ADD_CANDIDATES)
def import_from_table():
    """
    POST /parse_spreadsheet/import_from_table: Import candidates from a python table object (arrays of arrays)
    Input: {
        'file_picker_key': 'XDmR4dqbz56OWgdNkvP8.xlsx',
        'header_row_json': ['name', 'education'..],
        'source_id': 12
    }
    :return:
    """

    user_id = request.user.id

    posted_data = request.get_json(silent=True)
    if not posted_data or 'file_picker_key' not in posted_data or 'header_row' not in posted_data:
        raise InvalidUsage(error_message="Request body is empty or not provided")

    file_picker_key = posted_data.get('file_picker_key')
    header_row = posted_data.get('header_row')
    source_id = posted_data.get('source_id')
    is_import_scheduled = posted_data.get('is_import_scheduled')

    if not header_row or not file_picker_key:
        raise InvalidUsage(error_message="FilePicker key or header_row is missing")

    logger.info("import_from_table: Converting spreadsheet (key=%s) into table", file_picker_key)
    file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
    file_obj = download_file(file_picker_bucket, file_picker_key)

    candidates_table = convert_spreadsheet_to_table(file_obj, file_picker_key)

    # Check if first row of spreadsheet was header
    if any(param in candidates_table[0] for param in HEADER_ROW_PARAMS):
        candidates_table.pop(0)

    if len(candidates_table) > 500 and not is_import_scheduled:
        file_obj.close()
        posted_data['is_import_scheduled'] = True
        schedule_spreadsheet_import(posted_data)
        return jsonify(dict(count=len(candidates_table), status='pending')), 201

    delete_from_filepicker_s3(file_picker_key)

    file_obj.seek(0)

    url, key = upload_to_s3(file_obj.read(), folder_path="CSVResumes", name=file_picker_key, public=False)
    logger.info("import_from_table: Uploaded CSV of user ID %s to %s", user_id, url)

    file_obj.close()

    return import_from_spreadsheet(candidates_table, file_picker_key, header_row, source_id)
