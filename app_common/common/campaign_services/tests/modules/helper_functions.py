"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have helper functions to be used in tests
"""
# Packages
from requests import codes
from datetime import datetime, timedelta

# Application Specific
from ....models.misc import Frequency
from ....tests.sample_data import fake
from ....routes import EmailCampaignApiUrl
from ....utils.test_utils import send_request
from ....utils.datetime_utils import DatetimeUtils

__author__ = 'basit'


# This is common data for creating test events
EVENT_DATA = {
    "organizer_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "venue_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "title": "Test Event",
    "description": "Test Event Description",
    "registration_instruction": "Just Come",
    "start_datetime": (datetime.utcnow() + timedelta(days=2)).strftime(DatetimeUtils.ISO8601_FORMAT),
    "end_datetime": (datetime.utcnow() + timedelta(days=3)).strftime(DatetimeUtils.ISO8601_FORMAT),
    "group_url_name": "QC-Python-Learning",
    "social_network_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "timezone": "Asia/Karachi",
    "cost": 0,
    "currency": "USD",
    "social_network_group_id": 18837246,
    "max_attendees": 10
}


def create_data_for_campaign_creation(subject, smartlist_id, campaign_name=fake.name()):
    """
    This function returns the required data to create an email campaign.
    """
    body_text = fake.sentence()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    return {'name': campaign_name,
            'subject': subject,
            'body_html': body_html,
            'frequency_id': Frequency.ONCE,
            'list_ids': [smartlist_id] if smartlist_id else []
            }


def create_email_campaign_with_base_id(smartlist_id, base_campaign_id, access_token):
    """
    This creates an email-campaign with base_campaign_id
    """
    campaign_data = create_data_for_campaign_creation(fake.uuid4(), smartlist_id)
    campaign_data['base_campaign_id'] = base_campaign_id
    response = send_request('post', EmailCampaignApiUrl.CAMPAIGNS, access_token, campaign_data)
    assert response.status_code == codes.CREATED
    resp_object = response.json()
    assert 'campaign' in resp_object
    assert resp_object['campaign']['id']
    return resp_object['campaign']


def assert_email_campaign_overview(response, sent_campaigns_count=1, expected_blasts=0, expected_sends=0,
                                   expected_opens=0, expected_html_clicks=0, expected_text_clicks=0,
                                   expected_bounces=0):
    """
    Here we assert expected fields returned from campaign overview API
    """
    assert response.status_code == codes.OK, response.text
    assert response.json()
    json_response = response.json()
    assert json_response['email_campaigns']
    email_campaigns = json_response['email_campaigns']
    for expected_campaign_index in xrange(0, sent_campaigns_count):
        assert email_campaigns[expected_campaign_index]['blasts']
        blasts = email_campaigns[expected_campaign_index]['blasts']
        assert len(blasts) == expected_blasts
        for expected_blast_index in xrange(0, expected_blasts):
            assert blasts[expected_blast_index]['sends'] == expected_sends
            assert blasts[expected_blast_index]['opens'] == expected_opens
            assert blasts[expected_blast_index]['html_clicks'] == expected_html_clicks
            assert blasts[expected_blast_index]['text_clicks'] == expected_text_clicks
            assert blasts[expected_blast_index]['bounces'] == expected_bounces
