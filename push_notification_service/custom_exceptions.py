"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

This file contains custom exceptions for SMS campaign service.
"""
import json
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
    NO_SMARTLIST_ASSOCIATED = 5011
    NO_CANDIDATE_ASSOCIATED = 5012
    NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE = 5013
    ERROR_UPDATING_BODY_TEXT = 5014

    def to_dict(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class EmptySmsBody(SmsCampaignApiException):
    error_code = SmsCampaignApiException.EMPTY_SMS_BODY


class MultipleTwilioNumbers(SmsCampaignApiException):
    error_code = SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS


class TwilioAPIError(SmsCampaignApiException):
    error_code = SmsCampaignApiException.TWILIO_API_ERROR


class GoogleShortenUrlAPIError(SmsCampaignApiException):
    error_code = SmsCampaignApiException.GOOGLE_SHORTEN_URL_API_ERROR


class EmptyDestinationUrl(SmsCampaignApiException):
    error_code = SmsCampaignApiException.EMPTY_DESTINATION_URL


class MissingRequiredField(SmsCampaignApiException):
    error_code = SmsCampaignApiException.MISSING_REQUIRED_FIELD


class MultipleUsersFound(SmsCampaignApiException):
    error_code = SmsCampaignApiException.MULTIPLE_USERS_FOUND


class MultipleCandidatesFound(SmsCampaignApiException):
    error_code = SmsCampaignApiException.MULTIPLE_CANDIDATES_FOUND


class ErrorSavingSMSCampaign(SmsCampaignApiException):
    error_code = SmsCampaignApiException.ERROR_SAVING_SMS_CAMPAIGN


class ErrorDeletingSMSCampaign(SmsCampaignApiException):
    error_code = SmsCampaignApiException.ERROR_DELETING_SMS_CAMPAIGN


class NoSmartlistAssociated(SmsCampaignApiException):
    error_code = SmsCampaignApiException.NO_SMARTLIST_ASSOCIATED


class NoCandidateAssociated(SmsCampaignApiException):
    error_code = SmsCampaignApiException.NO_CANDIDATE_ASSOCIATED


class NoSMSCampaignSentToCandidate(SmsCampaignApiException):
    error_code = SmsCampaignApiException.NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE


class ErrorUpdatingBodyText(SmsCampaignApiException):
    error_code = SmsCampaignApiException.ERROR_UPDATING_BODY_TEXT

