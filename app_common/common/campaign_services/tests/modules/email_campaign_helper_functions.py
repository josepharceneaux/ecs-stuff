"""
This code contains helper common functions for email campaign service
"""
# Standard Imports
import json
from datetime import (datetime, timedelta)

# Third Party
import requests

# Application Specific
from ....models.misc import (Frequency)
from ....utils.datetime_utils import DatetimeUtils
from ....utils.test_utils import (fake)
from ....routes import (EmailCampaignApiUrl)
from ...tests_helpers import CampaignsTestsHelpers


def create_email_campaign_via_api(access_token, data, is_json=True):
    """
    This function makes HTTP POST call on /v1/email-campaigns to create
    an email-campaign. It then returns the response from email-campaigns API.
    :param access_token: access token of user
    :param data: data required for creation of campaign
    :param is_json: If True, it will take dumps of data to be sent in POST call. Otherwise it
                    will send data as it is.
    :return: response of API call
    """
    if is_json:
        data = json.dumps(data)
    response = requests.post(
        url=EmailCampaignApiUrl.CAMPAIGNS,
        data=data,
        headers={'Authorization': 'Bearer %s' % access_token,
                 'content-type': 'application/json'}
    )
    return response


def create_scheduled_email_campaign_data(access_token, talent_pipeline, **kwargs):
    """
    This returns data to create an scheduled email-campaign.
    :param access_token: User access token
    :param talent_pipeline: Talent pipeline object
    """
    campaign_data = create_data_for_campaign_creation(access_token, talent_pipeline, **kwargs)
    campaign_data['frequency_id'] = Frequency.ONCE
    campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(weeks=1))
    campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow()
                                                             + timedelta(weeks=2))
    return campaign_data


def create_data_for_campaign_creation(access_token, talent_pipeline, subject=fake.name(),
                                      campaign_name=fake.name(), assert_candidates=True, create_smartlist=True,
                                      smartlist_id=None):
    """
    This function returns the required data to create an email campaign
    """
    body_text = fake.sentence()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    if create_smartlist:
        smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token,
                                                                                talent_pipeline,
                                                                                emails_list=True,
                                                                                assert_candidates=assert_candidates)
    return {'name': campaign_name,
            'subject': subject,
            'body_html': body_html,
            'frequency_id': Frequency.ONCE,
            'list_ids': [smartlist_id] if smartlist_id else []
            }
