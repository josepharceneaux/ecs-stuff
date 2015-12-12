__author__ = 'ufarooqi'

import json
from flask import Blueprint, jsonify
from flask import request
from flask.ext.cors import CORS
from . import logger
from .parsing_utilities import convert_spreadsheet_to_table, import_from_spreadsheet
from spreadsheet_import_service.common.utils.auth_utils import require_oauth, require_all_roles
from spreadsheet_import_service.common.utils.talent_s3 import *

mod = Blueprint('spreadsheet_import_api', __name__)

# Enable CORS
CORS(mod, resources={
    r'/parse_spreadsheet': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@mod.route('/parse_spreadsheet/convert_to_table/', methods=['GET'])
@require_oauth
@require_all_roles('CAN_ADD_CANDIDATES')
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


@mod.route('/parse_spreadsheet/import_from_table', methods=['POST'])
@require_oauth
@require_all_roles('CAN_ADD_CANDIDATES')
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

    if not header_row or not file_picker_key:
        raise InvalidUsage(error_message="FilePicker key or header_row is missing")

    logger.info("import_from_table: Converting spreadsheet (key=%s) into table", file_picker_key)
    file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
    file_obj = download_file(file_picker_bucket, file_picker_key)

    candidates_table = convert_spreadsheet_to_table(file_obj, file_picker_key)

    delete_from_filepicker_s3(file_picker_key)

    # Check if first row of spreadsheet was header
    if 'first_name' in candidates_table[0] or 'last_name' in candidates_table[0] or 'email' in candidates_table[0]:
        candidates_table.pop(0)

    file_obj.seek(0)

    url, key = upload_to_s3(file_obj.read(), folder_path="CSVResumes", name=file_picker_key, public=False)
    logger.info("import_from_table: Uploaded CSV of user ID %s to %s", user_id, url)

    import_from_spreadsheet_kwargs = dict(header_row=header_row,
                                          source_id=source_id,
                                          spreadsheet_filename=file_picker_key,
                                          candidates_table=candidates_table)

    # TODO: Integrate scheduler with this API
    return import_from_spreadsheet(**import_from_spreadsheet_kwargs)
