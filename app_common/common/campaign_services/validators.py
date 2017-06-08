"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for campaign services.

Functions in this file are
    - validation_of_data_to_schedule_campaign()
    - validate_blast_candidate_url_conversion_in_db()
    - raise_if_dict_values_are_not_int_or_long etc.
"""
# Packages
from contracts import contract

# Database Models
from ..models.user import User
from ..models.candidate import Candidate
from ..models.smartlist import Smartlist
from ..models.base_campaign import BaseCampaign
from ..models.sms_campaign import SmsCampaignBlast
from ..models.misc import (Frequency, UrlConversion)
from ..models.email_campaign import EmailCampaignBlast

# Common utils
from ..utils.datetime_utils import DatetimeUtils
from ..error_handling import (InvalidUsage, ResourceNotFound, ForbiddenError)
from ..utils.handy_functions import (find_missing_items, get_valid_json_data)


def validation_of_data_to_schedule_campaign(request):
    """
    This validates the data provided to schedule a campaign.
    1- Get JSON data from request and raise Invalid Usage exception if no data is found or
            data is not JSON serializable.
    2- Get number of seconds by validating given frequency_id
    3- If end_datetime is not given and frequency is for periodic task, we raise Invalid usage.
    4- Returns data_to_schedule

    This function is used in data_validation_for_campaign_schedule() of CampaignBase class.

    :param flask.request request: request received on API
    :return: data_to_schedule
    :rtype: dict
    """
    data_to_schedule_campaign = get_valid_json_data(request)
    start_datetime = DatetimeUtils.get_datetime_obj_if_format_is_valid(data_to_schedule_campaign.get('start_datetime'))
    if not DatetimeUtils(start_datetime).is_in_future():
        raise InvalidUsage('start_datetime must be in future. Given %s' % start_datetime)

    # get number of seconds from frequency_id
    frequency = Frequency.get_seconds_from_id(data_to_schedule_campaign.get('frequency_id'))
    # check if task to be schedule is periodic
    if frequency and not data_to_schedule_campaign.get('end_datetime'):
        raise InvalidUsage("end_datetime is required to schedule a periodic task")
    else:
        end_datetime = DatetimeUtils.get_datetime_obj_if_format_is_valid(data_to_schedule_campaign.get(
            'end_datetime'))
        if not DatetimeUtils(end_datetime).is_in_future():
            raise InvalidUsage('end_datetime must be in future. Given %s' % end_datetime)

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
    :type campaign_blast_obj: SmsCampaignBlast | EmailCampaignBlast
    :type candidate: Candidate
    :type url_conversion_obj: UrlConversion
    :exception: ResourceNotFound

    **See Also**
    .. see also:: url_redirect() method of CampaignBase class
    """
    # check if candidate exists in database
    if not candidate or candidate.is_archived:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: Candidate not found.',
                               error_code=ResourceNotFound.http_status_code())
    # check if campaign_blasts exists in database
    if not campaign_blast_obj:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: campaign blast'
                               ' not found.', error_code=ResourceNotFound.http_status_code())
    # using relationship
    if not campaign_blast_obj.campaign:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: '
                               'Campaign not found for %s.' % campaign_blast_obj.__tablename__,
                               error_code=ResourceNotFound.http_status_code())
    # check if url_conversion record exists in database
    if not url_conversion_obj:
        raise ResourceNotFound('validate_blast_candidate_url_conversion_in_db: Url Conversion obj not found for '
                               '%s(id:%s).' % (campaign_blast_obj.campaign.__tablename__,
                                               campaign_blast_obj.campaign.id),
                               error_code=ResourceNotFound.http_status_code())
    return campaign_blast_obj.campaign


def validate_smartlist_ids(smartlist_ids, current_user):
    """
    This validates smartlist_ids on following criterion.
    1- If any of the smartlist_ids does not belong to user's domain, it raises ForbiddenError exception.
    2- If any of the smartlist_ids is not found in database, it raises ResourceNotFound exception.
    3- If any of the smartlist_ids is invalid (e.g. not int | long), it raises InvalidUsage exception.
    :param smartlist_ids: List of Ids of smartlists
    :param current_user: logged-in user's object
    :type smartlist_ids: list
    :type current_user: User
    """
    if not isinstance(smartlist_ids, list):
        raise InvalidUsage('Include smartlist id(s) in a list.')
    for smartlist_id in smartlist_ids:
        if not isinstance(smartlist_id, (int, long)) or not smartlist_id > 0:
            raise InvalidUsage('Include smartlist id as int|long')
        smartlist = Smartlist.get_by_id(smartlist_id)
        if not smartlist:
            raise ResourceNotFound('validate_smartlist_ids: Smartlist(id:%s) not found in database.'
                                   % str(smartlist_id))
        if not smartlist.user.domain_id == current_user.domain_id:
            raise ForbiddenError("validate_smartlist_ids: Smartlist(id:%s) do not belong to "
                                 "user's domain'" % str(smartlist_id))
        if smartlist.is_hidden:
            raise InvalidUsage('Associated Smartlist (id: %s) is deleted and can not be accessed'
                               % smartlist.id)


def validate_form_data(form_data, current_user, required_fields=('name', 'body_text', 'smartlist_ids')):
    """
    This does the validation of the data received to create/update a campaign.

        1- If any key from (name, body_text, smartlist_ids) is missing from form data or
            has no value we raise Invalid Usage error..
        2- We validate that all provided smartlist_ids are valid.

    :param form_data: Data from the UI
    :param required_fields: Fields which are required and expected in form_data.
    :type form_data: dict
    :type required_fields: tuple | list
    """
    if not isinstance(form_data, dict):
        raise InvalidUsage('form_data should be a dictionary.')
    if not isinstance(required_fields, (tuple, list)):
        raise InvalidUsage('required_fields should be tuple|list')
    # find if any required key has no valid value
    missing_field_values = find_missing_items(form_data, required_fields)
    if missing_field_values:
        raise InvalidUsage('Required fields not provided to save campaign. Empty fields are %s' % missing_field_values)
    # validate smartlist ids to create campaign
    validate_smartlist_ids(form_data['smartlist_ids'], current_user)

@contract
def raise_if_dict_values_are_not_int_or_long(data):
    """
    This validates if values in given dict are int or long. If not, it raises Invalid usage error.
    :param dict data: data to validate
    """
    for key, value in data.iteritems():
        if not isinstance(value, (int, long)) or not value:
            raise InvalidUsage('Include %s as int|long. It cannot be 0.' % key)


@contract
def validate_base_campaign_id(base_campaign_id, domain_id):
    """
    This raises ResourceNotFound error if given base-campaign-id is not found in database.
    This raises Forbidden error if given base-campaign-id does not belong to user's domain.
    :param positive base_campaign_id: BaseCampaign id
    :param positive domain_id: domain id of user
    """
    if not BaseCampaign.get_by_id(base_campaign_id):
        raise ResourceNotFound('Requested base-campaign not found in database')
    base_campaign = BaseCampaign.search_by_id_in_domain(base_campaign_id, domain_id)
    if not base_campaign:
        raise ForbiddenError('Requested base-campaign does not belong to user`s domain')
