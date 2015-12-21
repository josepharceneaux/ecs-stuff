"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains custom exceptions for SMS campaign service.
"""

# Standard Import
import json

# Service Specific
import sms_campaign_service.common.error_handling


class SmsCampaignApiException(sms_campaign_service.common.error_handling.InternalServerError):
    """
    This class contains custom error codes for SMS campaign service.
    """
    error_code = 5000
    EMPTY_SMS_BODY = 5001
    MULTIPLE_TWILIO_NUMBERS = 5002
    TWILIO_API_ERROR = 5003
    GOOGLE_SHORTEN_URL_API_ERROR = 5004
    EMPTY_DESTINATION_URL = 5005
    MISSING_REQUIRED_FIELD = 5006
    MULTIPLE_USERS_FOUND = 5007
    MULTIPLE_CANDIDATES_FOUND = 5008
    ERROR_SAVING_SMS_CAMPAIGN = 5009
    ERROR_DELETING_SMS_CAMPAIGN = 5010
    NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN = 5011
    NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST = 5012
    NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE = 5013
    ERROR_UPDATING_BODY_TEXT = 5014
    NO_CANDIDATE_FOR_PHONE_NUMBER = 5015
    NO_USER_FOR_PHONE_NUMBER = 5016
    INVALID_DATETIME = 5017

    def to_dict(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class EmptySmsBody(SmsCampaignApiException):
    """
    If SMS body text is empty at the time of sending SMS campaign to candidates,
    we raise this exception.

    **Usage**
        .. see also:: process_send() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.EMPTY_SMS_BODY


class MultipleTwilioNumbersFoundForUser(SmsCampaignApiException):
    """
    If user has multiple Twilio numbers associated with it, we raise this exception.

    **Usage**
        .. see also:: get_user_phone() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS


class TwilioAPIError(SmsCampaignApiException):
    """
    This exception is raised if we get any error related to Twilio API like for sending SMS
    or purchasing new number etc.

    **Usage**
        .. see also:: TwilioSMS() class in sms_campaign_service/utilities.py
    """
    error_code = SmsCampaignApiException.TWILIO_API_ERROR


class GoogleShortenUrlAPIError(SmsCampaignApiException):
    """
    This exception is raised if we get any error related to Google's Shorten URL API while
    requesting to shorter version of given URL

    **Usage**
        .. see also:: ConvertUrl() class in sms_campaign_service/v1_url_conversion_api.py
    """
    error_code = SmsCampaignApiException.GOOGLE_SHORTEN_URL_API_ERROR


class EmptyDestinationUrl(SmsCampaignApiException):
    """
    When candidate clicks on a URL present in SMS body text, this exception is raised if
    destination URL is empty in database (This URL was provided by getTalent user at time of
    creating campaign.

    **Usage**
        .. see also:: process_url_redirect() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.EMPTY_DESTINATION_URL


class MissingRequiredField(SmsCampaignApiException):
    """
    If any required field is empty, then we raise this exception.
    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.MISSING_REQUIRED_FIELD


class MultipleUsersFound(SmsCampaignApiException):
    """
    If getTalent user has multiple Twilio numbers associated with it, we raise this error.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.MULTIPLE_USERS_FOUND


class MultipleCandidatesFound(SmsCampaignApiException):
    """
    If multiple candidates are found for a given phone number, we raise this exception.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.MULTIPLE_CANDIDATES_FOUND


class ErrorSavingSMSCampaign(SmsCampaignApiException):
    """
    If we encounter a problem while saving SMS campaign in database table sms_campaign.
    we raise this exception.

    **Usage**
        .. see also:: create_or_update_sms_campaign() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.ERROR_SAVING_SMS_CAMPAIGN


class ErrorDeletingSMSCampaign(SmsCampaignApiException):
    """
    If we encounter a problem while deleting SMS campaign from database table sms_campaign.
    we raise this exception.

    **Usage**
        .. see also:: SMSCampaigns() class's DELETE method inside v1_sms_campaign_api.py
    """
    error_code = SmsCampaignApiException.ERROR_DELETING_SMS_CAMPAIGN


class NoSmartlistAssociatedWithCampaign(SmsCampaignApiException):
    """
    If we are about to send SMS campaign to candidates, and no smartlist is associated with
    SMS campaign, we raise this exception.

    **Usage**
        .. see also:: process_send() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN


class NoCandidateAssociatedWithSmartlist(SmsCampaignApiException):
    """
    If we are sending SMS campaign to candidates, and no candidate is found with
    associated smartlist(s), we raise this exception.

    **Usage**
        .. see also:: process_send() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST


class NoSMSCampaignSentToCandidate(SmsCampaignApiException):
    """
    If we receive an SMS from candidate, and no campaign was sent to this candidate,
    we raise this exception.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE


class ErrorUpdatingBodyText(SmsCampaignApiException):
    """
    If we are sending SMS campaign to candidate(s), we convert actual URL provided by recruiter
    with our App redirect URL (shorter version) and we encounter an issue, we raise this exception.

    **Usage**
        .. see also:: transform_body_text() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.ERROR_UPDATING_BODY_TEXT


class NoCandidateFoundForPhoneNumber(SmsCampaignApiException):
    """
    If we receive an SMS from candidate, and no candidate is found with sender's phone number,
    we raise this exception.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.NO_CANDIDATE_FOR_PHONE_NUMBER


class NoUserFoundForPhoneNumber(SmsCampaignApiException):
    """
    If we receive an SMS from candidate, and no user is found with receiver's phone number
    we raise this exception.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.NO_USER_FOR_PHONE_NUMBER


class InvalidDatetime(SmsCampaignApiException):
    """
    If we are creating new campaign, or updating old one, and start_datetime or end_datetime is
    not in valid UTC format, we raise this exception.
    **Usage**
        .. see also:: validate_form_data() function in utilities.py
    """
    error_code = SmsCampaignApiException.INVALID_DATETIME


