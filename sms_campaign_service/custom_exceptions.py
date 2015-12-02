"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

This file contains custom exceptions for SMS campaign service.
"""
import json
import sms_campaign_service.common.error_handling


class SmsCampaignApiException(sms_campaign_service.common.error_handling.InternalServerError):
    status_code = 5000

    def to_dict(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return error_dict

    def __str__(self):
        error_dict = super(SmsCampaignApiException, self).to_dict()
        error_dict['error']['code'] = self.__class__.status_code
        return json.dumps(error_dict)


class EmptySmsBody(SmsCampaignApiException):
    status_code = 5001


class MultipleTwilioNumbers(SmsCampaignApiException):
    status_code = 5002


class TwilioAPIError(SmsCampaignApiException):
    status_code = 5003


class GoogleShortenUrlAPIError(SmsCampaignApiException):
    status_code = 5004


class EmptyDestinationUrl(SmsCampaignApiException):
    status_code = 5005


class MissingRequiredField(SmsCampaignApiException):
    status_code = 5006


class MultipleUsersFound(SmsCampaignApiException):
    status_code = 5007


class MultipleCandidatesFound(SmsCampaignApiException):
    status_code = 5008


class ErrorSavingSMSCampaign(SmsCampaignApiException):
    status_code = 5009


class ErrorDeletingSMSCampaign(SmsCampaignApiException):
    status_code = 5010

