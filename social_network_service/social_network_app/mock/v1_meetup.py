"""
This module contains mocked Api endpoint for Meetup social-network
"""
# Standard Library
import sys
import random

# Third Party
from requests import codes
from flask import Blueprint, jsonify

# Application Specific
from social_network_service.common.models.event import Event
from social_network_service.common.utils.test_utils import fake
from social_network_service.modules.urls import SocialNetworkUrls as urls
from social_network_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

# Create Blueprint
meetup_mock_blueprint = Blueprint('meetup_mock', __name__)


@meetup_mock_blueprint.route(urls.MEETUP[urls.VALIDATE_TOKEN].format(urls.MEETUP_MOCK), methods=['GET'])
def meetup_validate_token():
    """
        This resource validates the access token by simply returning empty string and 200 status code
    """
    return '', codes.OK


@meetup_mock_blueprint.route(urls.MEETUP[urls.GROUPS].format(urls.MEETUP_MOCK), methods=['GET'])
def meetup_groups():
    """
        This resource returns meetup groups for a user.
    """
    fake_member_id = fake.random_number()
    response = {"results": [],
                "meta": {
                    "next": "",
                    "method": fake.word(),
                    "total_count": 3,
                    "link": fake.url(),
                    "count": 3,
                    "description": "None",
                    "lon": fake.longitude(),
                    "title": fake.word(),
                    "url": "%smember_id=%s&offset=0&format=json&page=800&" % (fake.url, fake_member_id),
                    "id": "",
                    "updated": fake.word(),
                    "lat": fake.latitude()
                }
                }
    results_count = random.randint(2, 5)
    for _ in xrange(results_count):
        response['results'].append({"utc_offset": fake.random_number(),
                                    "country": fake.country_code(),
                                    "visibility": fake.word(),
                                    "city": fake.city(),
                                    "timezone": fake.timezone(),
                                    "created": fake.unix_time(),
                                    "topics": [
                                        {
                                            "urlkey": fake.word(),
                                            "name": fake.word(),
                                            "id": fake.random_number()
                                        },
                                        {
                                            "urlkey": fake.word(),
                                            "name": fake.word(),
                                            "id": fake.random_number()
                                        },
                                        {
                                            "urlkey": fake.word(),
                                            "name": fake.word(),
                                            "id": fake.random_number()
                                        },
                                    ],
                                    "link": fake.url(),
                                    "rating": fake.random_number(),
                                    "description": fake.sentence(),
                                    "lon": fake.longitude(),
                                    "join_mode": fake.word(),
                                    "organizer": {
                                        "member_id": fake_member_id,
                                        "name": fake.word()
                                    },
                                    "members": fake.random_number(),
                                    "name": fake.word(),
                                    "id": sys.maxint,
                                    "state": fake.state(),
                                    "urlname": fake.word(),
                                    "category": {
                                        "name": fake.word(),
                                        "id": fake.random_number(),
                                        "shortname": fake.word()
                                    },
                                    "lat": fake.latitude(),
                                    "who": fake.word()
                                    })
    # Making one group owned by different user
    response['results'][results_count - 1]['organizer']['member_id'] = fake.random_number()
    return jsonify(response), codes.OK


@meetup_mock_blueprint.route(urls.MEETUP[urls.VENUES].format(urls.MEETUP_MOCK), methods=['POST'])
def meetup_venues():
    """
    This resource returns meetup venues.
    """
    response = {
        "errors": [
            {
                "code": "venue_error",
                "message": "potential matches",
                "potential_matches": []
            }
        ]
    }
    for _ in xrange(random.randint(1, 5)):
        response['errors'][0]['potential_matches'].append({
            "visibility": fake.word(),
            "zip": fake.zipcode(),
            "state": fake.state(),
            "phone": "",
            "name": fake.address(),
            "lon": fake.longitude(),
            "lat": fake.latitude(),
            "localized_country_name": fake.country(),
            "country": fake.country_code(),
            "city": fake.city(),
            "address_3": "",
            "address_2": "",
            "address_1": fake.address(),
            "id": fake.random_number()
        })
    return jsonify(response), codes.CONFLICT


@meetup_mock_blueprint.route(urls.MEETUP[urls.EVENTS].format(urls.MEETUP_MOCK), methods=['POST'])
def meetup_events():
    """
    This resource returns Meetup event.
    """
    non_existing_id = CampaignsTestsHelpers.get_non_existing_id(Event)
    return jsonify({'id': non_existing_id}), codes.OK


@meetup_mock_blueprint.route(urls.MEETUP[urls.EVENTS].format(urls.MEETUP_MOCK) + "/<string:event_id>",
                             methods=['DELETE'])
def meetup_delete_event(event_id):
    """
    This resource returns OK to show event has been deleted/update from/on Meetup website.
    """
    assert event_id
    return '', codes.OK


@meetup_mock_blueprint.route(urls.MEETUP[urls.EVENTS].format(urls.MEETUP_MOCK) + "/<string:event_id>",
                             methods=['POST'])
def meetup_update_event(event_id):
    """
    This resource returns OK to show event has been deleted/update from/on Meetup website.
    """
    assert event_id
    # event = Event.filter_by_keywords(**{'social_network_event_id': event_id})[0]
    # non_existing_id = CampaignsTestsHelpers.get_non_existing_id(Event)

    return jsonify({'id': event_id}), codes.OK
