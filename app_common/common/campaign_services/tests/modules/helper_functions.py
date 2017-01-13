"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have helper functions to be used in tests
"""
# Packages
from requests import codes
from datetime import datetime, timedelta

# Application Specific
from ....models.rsvp import RSVP
from ....models.misc import Frequency
from ....tests.sample_data import fake
from ....utils.test_utils import send_request
from ....utils.datetime_utils import DatetimeUtils
from ....routes import (EmailCampaignApiUrl, SocialNetworkApiUrl)

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


def get_email_campaign_data(subject, smartlist_id, campaign_name=fake.name()):
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
    campaign_data = get_email_campaign_data(fake.uuid4(), smartlist_id)
    campaign_data['base_campaign_id'] = base_campaign_id
    response = send_request('post', EmailCampaignApiUrl.CAMPAIGNS, access_token, campaign_data)
    assert response.status_code == codes.CREATED
    resp_object = response.json()
    assert 'campaign' in resp_object
    assert resp_object['campaign']['id']
    return resp_object['campaign']


def assert_email_campaign_overview(response, sent_campaigns_count=0, expected_blasts=0, expected_sends=0,
                                   expected_opens=0, expected_html_clicks=0, expected_text_clicks=0,
                                   expected_bounces=0):
    """
    Here we assert expected fields returned from campaign overview API for email campaigns.
    """
    assert response.status_code == codes.OK, response.text
    assert response.json()
    json_response = response.json()
    assert 'email_campaigns' in json_response
    if sent_campaigns_count:
        assert json_response['email_campaigns']
        email_campaigns = json_response['email_campaigns']
        for expected_campaign_index in xrange(0, sent_campaigns_count):
            assert 'blasts' in email_campaigns[expected_campaign_index]
            if expected_blasts:
                assert email_campaigns[expected_campaign_index]['blasts']
                blasts = email_campaigns[expected_campaign_index]['blasts']
                assert len(blasts) == expected_blasts
                for expected_blast_index in xrange(0, expected_blasts):
                    blast = blasts[expected_blast_index]
                    assert blast['sends'] == expected_sends
                    assert blast['opens'] == expected_opens
                    assert blast['html_clicks'] == expected_html_clicks
                    assert blast['text_clicks'] == expected_text_clicks
                    assert blast['bounces'] == expected_bounces


def assert_event_overview(response, expected_events=0, expected_invites=0):
    """
    Here we assert expected fields returned from campaign overview API for an event.
    """
    assert response.status_code == codes.OK, response.text
    assert response.json()
    json_response = response.json()
    assert 'event' in json_response
    if expected_events:
        assert json_response['event']
        event = json_response['event']
        assert 'rsvps' in event
        if expected_invites:
            rsvps = event['rsvps']
            assert len(rsvps) >= expected_invites  # Due to session based event
            for rsvp in rsvps:
                assert rsvp['event_id'] == event['id']


def create_an_rsvp_in_database(candidate_id, event_id, access_token, expected_status='yes'):
    """
    This saves an RSVP in database
    """
    response = send_request('get', SocialNetworkApiUrl.EVENT % event_id, access_token)
    assert response.ok
    social_network_id = response.json()['event']['social_network_id']
    data = {
        'candidate_id': candidate_id,
        'event_id': event_id,
        'social_network_rsvp_id': fake.random_int(),
        'social_network_id': social_network_id,
        'status': expected_status,
    }
    rsvp = RSVP(**data)
    RSVP.save(rsvp)


def auth_header(token):
    """
    Return dictionary which consist of bearer token only.
    :param token: bearer token
    :return:dictionary containing bearer token
    """
    return dict(Authorization='Bearer %s' % token)
