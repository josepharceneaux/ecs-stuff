"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains custom exceptions for campaign services like SMS campaign service, Push campaign
    etc.    
"""

# Standard Imports
import json

# Service Specific
from ..error_handling import InternalServerError


class CampaignException(InternalServerError):
    """
    This class contains custom error codes for campaigns services.
    """
    error_code = 5100

    # only used as error codes
    EMPTY_BODY_TEXT = 5101
    NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN = 5102
    NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST = 5103
    MISSING_REQUIRED_FIELD = 5104
    ERROR_DELETING_CAMPAIGN = 5015

    # used as custom exceptions
    MULTIPLE_CANDIDATES_FOUND = 5016
    EMPTY_DESTINATION_URL = 5017

    def to_dict(self):
        error_dict = super(CampaignException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return error_dict

    def __str__(self):
        error_dict = super(CampaignException, self).to_dict()
        error_dict['error']['code'] = self.__class__.error_code
        return json.dumps(error_dict)


class MultipleCandidatesFound(CampaignException):
    """
    If multiple candidates are found for a given
    1) phone number for sms_campaign or
    2) device id for push_campaign
    3) email address for email_campaign, we raise this exception.

    **Usage**
        .. see also:: process_candidate_reply() method of SmsCampaignBase class.
    """
    error_code = CampaignException.MULTIPLE_CANDIDATES_FOUND


class EmptyDestinationUrl(CampaignException):
    """
    When candidate clicks on a URL present in SMS body text, this exception is raised if
    destination URL is empty in database (This URL was provided by getTalent user at time of
    creating campaign.

    **Usage**
        .. see also:: process_url_redirect() method of SmsCampaignBase class.
    """
    error_code = CampaignException.EMPTY_DESTINATION_URL

