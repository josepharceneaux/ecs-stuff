"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Um-I-Hani, QC-Technologies, <haniqadri.qc@gmail.com>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    Here are the validator functions used in email-campaign-service
"""

# Standard Library
import datetime
from functools import wraps
from collections import Counter

# Third Party
import requests
from flask import request

# Application Specific
from email_campaign_service.common.utils.handy_functions import find_missing_items, validate_required_fields
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.modules.email_campaign_base import EmailCampaignBase
from email_campaign_service.modules.email_clients import EmailClientBase
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.common.models.user import (User, ForbiddenError, Domain)
from email_campaign_service.common.error_handling import (InvalidUsage, UnprocessableEntity)
from email_campaign_service.common.campaign_services.validators import validate_smartlist_ids
from email_campaign_service.common.talent_config_manager import (TalentConfigKeys, TalentEnvs)
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  MISSING_FIELD, INVALID_DATETIME_VALUE,
                                                                  INVALID_INPUT, INVALID_DATETIME_FORMAT,
                                                                  SMARTLIST_NOT_FOUND, SMARTLIST_FORBIDDEN)
from email_campaign_service.common.campaign_services.validators import validate_base_campaign_id
from email_campaign_service.common.models.email_campaign import (EmailClientCredentials, EmailClient)


def validate_data_to_schedule_campaign(campaign_data):
    """
    This validates the data provided to schedule a campaign.
    - Get number of seconds by validating given frequency_id
    - If end_datetime is not given and frequency is for periodic task, we raise Invalid usage.
    - Returns frequency_id, start_datetime and end_datetime
    This function is used in data_validation_for_campaign_schedule() of CampaignBase class.
    :param dict campaign_data: Campaign data
    :rtype: tuple
    """
    start_datetime_obj, end_datetime_obj = None, None
    frequency_id = campaign_data.get('frequency_id')  # required
    # Get number of seconds from frequency_id. If frequency is there then there must be a start time.
    try:
        frequency = Frequency.get_seconds_from_id(frequency_id)
    except InvalidUsage as error:
        raise InvalidUsage(error.message, error_code=INVALID_INPUT[1])
    # Get start datetime string
    start_datetime = campaign_data.get('start_datetime')
    # Get end datetime string
    end_datetime = campaign_data.get('end_datetime')

    if frequency and not start_datetime:
        raise UnprocessableEntity("Frequency requires `start_datetime`.", error_code=MISSING_FIELD[1])

    if frequency and not end_datetime:
        raise UnprocessableEntity("`end_datetime` is required to schedule a periodic task",
                                  error_code=MISSING_FIELD[1])
    # Validate format and value
    if start_datetime:
        start_datetime_obj = DatetimeUtils.get_datetime_obj_if_format_is_valid(start_datetime,
                                                                               error_code=INVALID_DATETIME_FORMAT[1])
        if not DatetimeUtils(start_datetime_obj).is_in_future():
            raise UnprocessableEntity('`start_datetime` must be in future. Given %s' % start_datetime,
                                      error_code=INVALID_DATETIME_VALUE[1])
    if end_datetime:
        end_datetime_obj = DatetimeUtils.get_datetime_obj_if_format_is_valid(end_datetime,
                                                                             error_code=INVALID_DATETIME_FORMAT[1])
        if not DatetimeUtils(end_datetime_obj).is_in_future():
            raise UnprocessableEntity('`end_datetime` must be in future. Given %s' % end_datetime,
                                      error_code=INVALID_DATETIME_VALUE[1])

    if start_datetime and end_datetime and start_datetime_obj > end_datetime_obj:
        raise UnprocessableEntity("`end_datetime` cannot be before `start_datetime`",
                                  error_code=INVALID_DATETIME_VALUE[1])
    return frequency_id, frequency, start_datetime, end_datetime


def validate_and_format_request_data(data, current_user):
    """
    Validates the request form data and returns the formatted data with leading and trailing
    white spaces stripped.
    :param dict data: Data received from UI
    :param User current_user: Logged-in user's object
    :return: Dictionary of formatted data
    :rtype: dict
    """
    name = data.get('name')  # required
    subject = data.get('subject')  # required
    description = data.get('description', '')  # required
    _from = data.get('from')
    reply_to = data.get('reply_to')
    body_html = data.get('body_html')  # required
    body_text = data.get('body_text')
    list_ids = data.get('list_ids')  # required
    email_client_id = data.get('email_client_id')
    frequency_id = data.get('frequency_id')  # required
    email_client_credentials_id = data.get('email_client_credentials_id')
    base_campaign_id = data.get('base_campaign_id')

    # Find if any required key has no valid value
    validate_required_fields(data, EmailCampaignBase.REQUIRED_FIELDS, error_code=MISSING_FIELD[1])

    # Raise errors if invalid input of string inputs
    if filter(lambda item: not isinstance(item, basestring) or not str(item).strip(), [name, subject, body_html]):
        raise InvalidUsage("Expecting `name`, `subject` and `body_html` as non-empty string",
                           error_code=INVALID_INPUT[1])
    if not frequency_id:
        raise InvalidUsage(INVALID_INPUT[0].format("`frequency_id`"), error_code=INVALID_INPUT[1])

    # Validation for list ids belonging to same domain
    validate_smartlist_ids(list_ids, current_user, error_code=INVALID_INPUT[1],
                           resource_not_found_error_code=SMARTLIST_NOT_FOUND[1],
                           forbidden_error_code=SMARTLIST_FORBIDDEN[1])

    frequency_id, frequency, start_datetime, end_datetime = validate_data_to_schedule_campaign(data)

    if email_client_id:
        # Check if email_client_id is valid
        email_client = EmailClient.query.get(email_client_id)
        if not email_client:
            raise InvalidUsage("`email_client_id` is not valid id.")

    # In case user wants to send email-campaign with its own account
    if email_client_credentials_id:
        email_client_credentials = EmailClientCredentials.get_by_id(email_client_credentials_id)
        if not EmailClientBase.is_outgoing(email_client_credentials.host):
            raise InvalidUsage("Selected email-client must be of type `outgoing`")
    # Validation for base_campaign_id
    if base_campaign_id:
        validate_base_campaign_id(base_campaign_id, current_user.domain_id)

    # strip whitespaces and return data
    return {
        'name': name.strip(),
        'subject': subject.strip(),
        'description': description.strip(),
        'from': get_or_set_valid_value(_from, basestring, '').strip(),
        'reply_to': get_or_set_valid_value(reply_to, basestring, '').strip(),
        'body_html': body_html.strip(),
        'body_text': get_or_set_valid_value(body_text, basestring, '').strip(),
        'list_ids': list_ids,
        'email_client_id': email_client_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'frequency_id': frequency_id,
        'email_client_credentials_id': email_client_credentials_id,
        'base_campaign_id': base_campaign_id
    }


def get_or_set_valid_value(required_value, required_instance, default):
    """
    This checks if `required_value` is an instance of `required_instance`. If it is, it returns the
    `required_value`, otherwise it sets the `default` value and returns it.
    :param required_value: value to be validated
    :param required_instance: expected instance of `required_value`
    :param default: default value to be set
    """
    if not isinstance(required_value, required_instance):
        required_value = default
    return required_value


def validate_domain_id_for_email_templates():
    """
    We want to show email-template feature to only Kaiser for now.
    If any other customer tries to use this API, we will raise Forbidden error saying something like
        "You are not allowed to perform this action"
    """

    def wrapper(func):
        @wraps(func)
        def validate(*args, **kwargs):
            valid_domain_ids = []
            if app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
                valid_domain_ids = Domain.get_by_name('kaiser')
            else:
                # Get valid domain ids from S3 file.
                response = requests.get(app.config[TalentConfigKeys.URL_FOR_DOMAINS_FOR_EMAIL_TEMPLATES])
                response = response.json()
                for key, value in response.iteritems():
                    if value:
                        valid_domain_ids.append(int(key))
            if request.user.domain_id not in valid_domain_ids:
                raise ForbiddenError(TEMPLATES_FEATURE_NOT_ALLOWED[0],
                                     TEMPLATES_FEATURE_NOT_ALLOWED[1])
            return func(*args, **kwargs)

        return validate

    return wrapper
