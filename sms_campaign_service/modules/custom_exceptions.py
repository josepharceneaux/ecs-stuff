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
    # only used as error codes
    INVALID_URL_FORMAT = 5001

    # used as custom exceptions
    MULTIPLE_TWILIO_NUMBERS = 5002
    TWILIO_API_ERROR = 5003
    GOOGLE_SHORTEN_URL_API_ERROR = 5004
    MULTIPLE_USERS_FOUND = 5005
    NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE = 5006
    ERROR_UPDATING_BODY_TEXT = 5007
    NO_CANDIDATE_FOR_PHONE_NUMBER = 5008
    NO_USER_FOR_PHONE_NUMBER = 5009

    def to_dict(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class MultipleTwilioNumbersFoundForUser(SmsCampaignApiException):
    """
    If user has multiple Twilio numbers associated with it, we raise this exception.

    **Usage**
        .. see also:: get_user_phone() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS


class TwilioApiError(SmsCampaignApiException):
    """
    This exception is raised if we get any error related to Twilio API like for sending SMS
    or purchasing new number etc.

    **Usage**
        .. see also:: TwilioSMS() class in sms_campaign_service/modules/handy_functions.py
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


class MultipleUsersFound(SmsCampaignApiException):
    """
    If getTalent user has multiple Twilio numbers associated with it, we raise this error.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = SmsCampaignApiException.MULTIPLE_USERS_FOUND


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
