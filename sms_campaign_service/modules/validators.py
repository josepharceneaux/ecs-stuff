"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for SMS campaign service.
"""
# Standard Imports

# Service Specific
from sms_campaign_service.sms_campaign_app import logger
from sms_campaign_service.modules.custom_exceptions import (InvalidUrl, MissingRequiredField)

# Database models
from sms_campaign_service.common.models.talent_pools_pipelines import Smartlist

# Common stuff
from sms_campaign_service.common.error_handling import (InvalidUsage, ResourceNotFound)
from sms_campaign_service.common.campaign_services.validators import is_valid_url_format
from sms_campaign_service.common.utils.common_functions import (http_request, find_missing_items)
from sms_campaign_service.modules.handy_functions import search_urls_in_text


def validate_form_data(form_data):
    """
    This does the validation of the data received to create/update SMS campaign.

        1- If any key from (name, body_text, smartlist_ids) is missing from form data or
            has no value we raise MissingRequiredFieldError.
        2- If smartlist_ids are not present in database, we raise ResourceNotFound exception.

    :param form_data:
    :return: list of ids of smartlists which were not found in database.
    :rtype: list
    """
    required_fields = ['name', 'body_text', 'smartlist_ids']
    # find if any required key is missing from data
    missing_fields = filter(lambda required_key: required_key not in form_data, required_fields)
    if missing_fields:
        raise MissingRequiredField('Required fields not provided to save sms_campaign. '
                                   'Missing fields are %s' % missing_fields)
    # find if any required key has no value
    missing_field_values = find_missing_items(form_data, required_fields)
    if missing_field_values:
        raise MissingRequiredField(
            'Required fields are empty to save '
            'sms_campaign. Empty fields are %s' % missing_field_values)
    # validate URLs present in SMS body text
    valid_urls, invalid_urls = validate_urls_in_body_text(form_data['body_text'])
    if invalid_urls:
        raise InvalidUrl('Invalid URL(s) in body_text. %s' % invalid_urls)

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
            logger.exception('validate_form_data: Invalid smartlist id')
        except ResourceNotFound:
            logger.exception('validate_form_data: Smartlist(id:%s) not found in database.'
                             % str(smartlist_id))
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


def validate_url_format(url):
    """
    This validates if given URL is valid or not
    :param url: URL to be validate
    :type url: str
    :exception: InvalidUrl if URL is in improper format
    :return:
    """
    if not is_valid_url_format(url):
        raise InvalidUrl('Given URL (%s) is not valid.' % url)
    return True


def validate_url_by_http_request(url):
    """
    This function makes HTTP GET call to given URL, and return True if we get OK response,
    It returns False otherwise
    :param url:
    :return: True or False
    :rtype: bool
    """
    try:
        http_request('GET', url)
    except Exception:
        return False
    return True


def validate_urls_in_body_text(text):
    """
    This function validates the URLs present in SMS body text. It first check if they
    are in valid format, then it makes HTTP GET call to that URL to verify the URL is live.
    :param text:
    :return:
    """
    urls = search_urls_in_text(text)
    valid_urls = []
    invalid_urls = []
    for url in urls:
        try:
            validate_url_format(url)
            validate_url_by_http_request(url)
            valid_urls.append(url)
        except Exception:
            invalid_urls.append(url)
    return valid_urls, invalid_urls
