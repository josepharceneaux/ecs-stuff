__author__ = 'ufarooqi'

import json
from flask import Blueprint
from flask import request
from flask.ext.cors import CORS
from . import logger, app
from .parsing_utilities import convert_spreadsheet_to_table, import_from_csv
from spreadsheet_import_service.common.utils.auth_utils import require_oauth
from spreadsheet_import_service.common.utils.talent_s3 import *

mod = Blueprint('spreadsheet_import_api', __name__)

# Enable CORS
CORS(mod, resources={
    r'/parse_spreadsheet': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


def spreadsheet_to_table():
    """
    POST /parse_spreadsheet/convert_to_table  Convert given spreadsheet to table of candidates
    Input: {'file_picker_key': 'XDmR4dqbz56OWgdNkvP8', 'filename': 'candidates.csv'}

    :return A dictionary containing row of candidates
    :rtype: dict
    """
    posted_data = request.get_json(silent=True)
    if not posted_data or 'file_picker_key' not in posted_data or 'filename' not in posted_data:
        raise InvalidUsage(error_message="Request body is empty or not provided")

    filename = posted_data.get('filename')
    file_picker_key = posted_data.get('file_picker_key')

    file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
    file_obj = download_file(file_picker_bucket, file_picker_key)

    csv_table = convert_spreadsheet_to_table(file_obj, filename)
    first_rows = csv_table[:10]

    return dict(table=first_rows)


# TODO: Integrate scheduler with this API
def import_from_table():
    """
    POST: Downloads spreadsheet from S3 and converts into table format. If the table has more than 100 rows,
    will use scheduler and email user when completed. Otherwise, will return in same request.
    Input: {
        'file_picker_key': 'XDmR4dqbz56OWgdNkvP8',
        'header_row_json': ['name', 'education'..],
        'source_id': 12
    }
    :return:
    """

    user_id = request.user.id

    posted_data = request.get_json(silent=True)
    if not posted_data or 'file_picker_key' not in posted_data or 'filename' not in posted_data:
        raise InvalidUsage(error_message="Request body is empty or not provided")

    file_picker_key = posted_data.get('file_picker_key')
    header_row_json = posted_data.get('header_row_json')
    header_row = json.loads(header_row_json) if header_row_json else None
    source_id = posted_data.get('source_id')

    if not header_row or not file_picker_key:
        raise InvalidUsage(error_message="FilePicker key or header_row is missing")

    logger.info("import_from_table: Converting spreadsheet (key=%s) into table", file_picker_key)
    file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
    file_obj = download_file(file_picker_bucket, file_picker_key)

    csv_table = convert_spreadsheet_to_table(file_obj, file_picker_key)
    file_obj.seek(0)

    url, key = upload_to_s3(file_obj.read(), folder_path="CSVResumes", name=file_picker_key, public=False)
    logger.info("import_from_table: Uploaded CSV of user ID %s to %s", user_id, url)

    import_from_csv_kwargs = dict(header_row=header_row,
                                  source_id=source_id,
                                  user_id=user_id,
                                  csv_filename=file_picker_key,
                                  csv_table=csv_table)

    return import_from_csv(**import_from_csv_kwargs)