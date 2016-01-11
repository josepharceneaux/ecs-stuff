"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for campaign services.

Functions in this file are
    - validate_headers()
    - validate_datetime_format()
    - is_datetime_in_future()
    - validation_of_data_to_schedule_campaign() etc.
"""

# Standard Imports
import re
from dateutil.tz import tzutc
from flask import current_app
from datetime import (datetime, timedelta)
from werkzeug.exceptions import BadRequest

# Third Party
from dateutil.parser import parse

# Common utils
from ..models.smartlist import Smartlist
from campaign_utils import frequency_id_to_seconds
from ..talent_config_manager import TalentConfigKeys
from ..error_handling import (InvalidUsage, ResourceNotFound)
from ..utils.handy_functions import (JSON_CONTENT_TYPE_HEADER, find_missing_items)


def validate_header(request):
    """
    Proper header should be {'content-type': 'application/json'} for POSTing
    some data on SMS campaign API.
    If header of request is not proper, it raises InvalidUsage exception
    :return:
    """
    if not request.headers.get('CONTENT_TYPE') == JSON_CONTENT_TYPE_HEADER['content-type']:
        raise InvalidUsage('Invalid header provided')


def validate_datetime_format(str_datetime):
    """
    This validates the given datetime is in ISO UTC format or not. Proper format should be like
    '2015-10-08T06:16:55Z'.

    :param str_datetime: str
    :type str_datetime: str
    :exception: Invalid Usage
    :return: True if given datetime is valid, False otherwise.
    :rtype: bool
    """
    if not isinstance(str_datetime, basestring):
        raise InvalidUsage('datetime should be provided in str format as 2015-10-08T06:16:55Z')
    utc_pattern = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
    if re.match(utc_pattern, str_datetime):
        return True
    else:
        raise InvalidUsage('Invalid DateTime: Kindly specify UTC datetime in ISO-8601 format '
                           'like 2015-10-08T06:16:55Z. Given Date is %s' % str_datetime)


def is_datetime_in_future(dt):
    """
    This function validates that given datetime obj has date and time in future by comparing
    with current UTC datetime object.
    :param dt: datetime obj
    :type dt: datetime
    :exception: Invalid usage
    :return: True if given datetime is ahead of current datetime
    :rtype: bool
    """
    if not isinstance(dt, datetime):
        raise InvalidUsage('param should be a datetime object')
    return dt > datetime.utcnow().replace(tzinfo=tzutc())


def is_datetime_in_valid_format_and_in_future(datetime_str):
    """
    Here we check given string datetime is in valid format, then we convert it into datetime obj.
    Finally we check if it is in future.
    This uses if_str_datetime_in_valid_format_get_datetime_obj() and is_datetime_in_future() functions.
    :param datetime_str:
    :type datetime_str: str
    :return:
    """
    if not is_datetime_in_future(if_str_datetime_in_valid_format_get_datetime_obj(datetime_str)):
        current_app.config[TalentConfigKeys.LOGGER].error('Datetime str should be in future. %s' % datetime_str)
        raise InvalidUsage("Given datetime(%s) should be in future" % datetime_str)


def is_valid_url_format(url):
    """
    Reference: https://github.com/django/django-old/blob/1.3.X/django/core/validators.py#L42
    """
    regex = re.compile(
        r'^(http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


def if_str_datetime_in_valid_format_get_datetime_obj(str_datetime):
    """
    This converts given string datetime into UTC datetime obj.
    This uses validate_datetime_format() to validate the format of given str.
    Valid format should be like 2015-10-08T06:16:55Z
    :param str_datetime:
    :return: datetime obj
    :rtype: datetime
    """
    if not isinstance(str_datetime, basestring):
        raise InvalidUsage('param should be a string of datetime')
    validate_datetime_format(str_datetime)
    return parse(str_datetime).replace(tzinfo=tzutc())


def validation_of_data_to_schedule_campaign(campaign_obj, request):
    """
    This validates the data provided to schedule a campaign.
    1- Get JSON data from request and raise Invalid Usage exception if no data is found or
            data is not JSON serializable.
    2- If start datetime is not provide/given in invalid format/is in past, we raise Invalid usage
        error as start_datetime is required field for both 'periodic' and 'one_time' schedule.
    3- Get number of seconds by validating given frequency_id
    4- If end_datetime and frequency, both are provided then we validate same checks for
        end_datetime as we did in step 2 for start_datetime.
    5- Removes the frequency_id from given dict of data and put frequency (number of seconds) in it.
    6- Returns data_to_schedule

    This function is used in pre_process_schedule() of CampaignBase class.

    :param campaign_obj: campaign obj
    :param request: request received on API
    :return: data_to_schedule
    :rtype: dict
    """
    try:
        data_to_schedule_campaign = request.get_json()
    except BadRequest:
        raise InvalidUsage('Given data is not JSON serializable.')
    if not data_to_schedule_campaign:
        raise InvalidUsage('No data provided to schedule %s (id:%s)'
                           % (campaign_obj.__tablename__, campaign_obj.id))
    # check if data has start_datetime
    if not data_to_schedule_campaign.get('start_datetime'):
        raise InvalidUsage('start_datetime is required field.')
    # start datetime should be in valid format and in future
    is_datetime_in_valid_format_and_in_future(data_to_schedule_campaign.get('start_datetime'))
    # get start_datetime object
    start_datetime = if_str_datetime_in_valid_format_get_datetime_obj(
        data_to_schedule_campaign.get('start_datetime'))
    end_datetime_str = data_to_schedule_campaign.get('end_datetime')
    # get number of seconds from frequency id
    frequency = frequency_id_to_seconds(data_to_schedule_campaign.get('frequency_id'))
    # check if task to be schedule is periodic
    if end_datetime_str and frequency:
        # check if end_datetime is greater than start_datetime
        end_datetime_plus_frequency = \
            if_str_datetime_in_valid_format_get_datetime_obj(end_datetime_str)\
            + timedelta(seconds=frequency)
        if end_datetime_plus_frequency < start_datetime:
            raise InvalidUsage("end_datetime must be greater than start_datetime")
    data_to_schedule_campaign['frequency'] = frequency
    return data_to_schedule_campaign


def validate_blast_candidate_url_conversion_in_db(campaign_blast_obj, candidate,
                                                  url_conversion_obj):
    """
    This method is used for the pre-processing of URL redirection
        It checks if campaign blast object, candidate, campaign and url_conversion object
        is present in database. If any of them is missing it raise ResourceNotFound.

    :param campaign_blast_obj: campaign blast object
    :param candidate: candidate object
    :param url_conversion_obj: url_conversion obj
    :type campaign_blast_obj: SmsCampaignBlast | EmailCampaignBlast or any other campaign type
    :type candidate: Candidate
    :type url_conversion_obj: UrlConversion
    :exception: ResourceNotFound

    **See Also**
    .. see also:: process_url_redirect() method of CampaignBase class
    """
    # check if candidate exists in database
    if not candidate:
        raise ResourceNotFound(
            'validate_blast_candidate_url_conversion_in_db: Candidate not found.',
            error_code=ResourceNotFound.http_status_code())
    # check if campaign_blasts exists in database
    if not campaign_blast_obj:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: campaign blast'
                               ' not found.', error_code=ResourceNotFound.http_status_code())
    if not campaign_blast_obj.campaign:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: '
                               'Campaign not found for %s.' % campaign_blast_obj.__tablename__,
                               error_code=ResourceNotFound.http_status_code())
    # check if url_conversion record exists in database
    if not url_conversion_obj:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: '
                               'Url Conversion(id=%s) not found.' % url_conversion_obj.id,
                               error_code=ResourceNotFound.http_status_code())
    return campaign_blast_obj.campaign


def validate_form_data(form_data, required_fields):
    """
    This does the validation of the data received to create/update a campaign.

        1- If any key from (name, body_text, smartlist_ids) is missing from form data or
            has no value we raise Invalid Usage error..
        2- If smartlist_ids are not present in database, we raise ResourceNotFound exception.

    :param form_data: Data from the UI
    :type form_data: dict
    :return: tuple of lists
                    1)ids of smartlists which were not found in database.
                    2)ids of unknown smartlist ids (not, int)
    :rtype: tuple
    """
    if not isinstance(form_data, dict):
        raise InvalidUsage('form_data should be instance of dict.')
    # find if any required key is missing from data
    missing_fields = filter(lambda required_key: required_key not in form_data, required_fields)
    if missing_fields:
        raise InvalidUsage('Required fields not provided to save sms_campaign. '
                           'Missing fields are %s' % missing_fields)
    # find if any required key has no value
    missing_field_values = find_missing_items(form_data, required_fields)
    if missing_field_values:
        raise InvalidUsage(
            'Required fields are empty to save '
            'sms_campaign. Empty fields are %s' % missing_field_values)

    # validate smartlist ids are in a list
    if not isinstance(form_data.get('smartlist_ids'), list):
        raise InvalidUsage('Include smartlist id(s) in a list.')

    not_found_smartlist_ids = []
    invalid_smartlist_ids = []
    for smartlist_id in form_data.get('smartlist_ids'):
        try:
            if not isinstance(smartlist_id, (int, long)):
                invalid_smartlist_ids.append(smartlist_id)
                raise InvalidUsage('Include smartlist id as int|long')
            if not Smartlist.get_by_id(smartlist_id):
                not_found_smartlist_ids.append(smartlist_id)
                raise ResourceNotFound
        except InvalidUsage:
            current_app.config[TalentConfigKeys.LOGGER].exception('validate_form_data: Invalid smartlist id')
        except ResourceNotFound:
            current_app.config[TalentConfigKeys.LOGGER].exception(
                'validate_form_data: Smartlist(id:%s) not found in database.' % str(smartlist_id))
    # If all provided smartlist ids are invalid, raise InvalidUsage
    if len(form_data.get('smartlist_ids')) == len(invalid_smartlist_ids):
        raise InvalidUsage(
            'smartlists(id(s):%s are invalid. Valid id must be int|long'
            % form_data.get('smartlist_ids'))
    # If all provided smartlist ids do not exist in database, raise ResourceNotFound
    if len(form_data.get('smartlist_ids')) == len(not_found_smartlist_ids):
        raise ResourceNotFound('smartlists(id(s):%s not found in database.'
                               % form_data.get('smartlist_ids'))
    # filter out unknown smartlist ids, and keeping the valid ones
    form_data['smartlist_ids'] = list(set(form_data.get('smartlist_ids')) -
                                      set(invalid_smartlist_ids + not_found_smartlist_ids))
    return invalid_smartlist_ids, not_found_smartlist_ids
