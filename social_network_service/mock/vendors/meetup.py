"""
Here we have mocked data for Meetup API.
"""
# Standard Library
import sys
import random
from random import randint
from itertools import repeat, chain

# Third Party
from requests import codes

# Application Specific
from social_network_service.common.models.event import Event
from social_network_service.common.utils.test_utils import fake
from social_network_service.modules.urls import SocialNetworkUrls as Urls
from social_network_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

# Prepare data for dictionary below
meetup_fake_member_id = fake.random_number()
valid_access_token = 'abc_access_token'
valid_refresh_token = 'abc_refresh_token'

# JSON dict
meetup_vendor = {
    Urls.MEETUP[Urls.VALIDATE_TOKEN].format(''): {
        'GET': {
            codes.OK: {
                'headers': {
                    'Authorization': 'Bearer {}'.format(valid_access_token)
                },
                'status_code': codes.OK,
                'response': {
                    "country": fake.word(),
                    "city": fake.word(),
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
                        }
                    ],
                    "joined": fake.random_number(),
                    "link": "%s/members/%s" % (fake.url, meetup_fake_member_id),
                    "lon": fake.longitude(),
                    "other_services": {},
                    "name": fake.word(),
                    "visited": fake.random_number(),
                    "self": {
                        "common": {}
                    },
                    "id": meetup_fake_member_id,
                    "state": fake.word(),
                    "lang": fake.word(),
                    "lat": fake.latitude(),
                    "status": fake.word()
                },
            },
            codes.UNAUTHORIZED: {
                'response': {
                    'Unauthorized': 'Unauthorized access'
                }
            }
        }
    },

    Urls.MEETUP[Urls.GROUPS].format(''): {
        'GET': {
            codes.OK: {
                'status_code': codes.OK,
                "results": [{"utc_offset": fake.random_number(),
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
                                 "member_id": fake.random_number() if is_last else meetup_fake_member_id,
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
                             } for is_last in chain(repeat(0, randint(2, 4)), [1])
                            # i.e [0,0 .., 1]
                            ],
                "meta": {
                    "next": "",
                    "method": fake.word(),
                    "total_count": 3,
                    "link": fake.url(),
                    "count": 3,
                    "description": "None",
                    "lon": fake.longitude(),
                    "title": fake.word(),
                    "url": "%smember_id=%s&offset=0&format=json&page=800&" % (
                        fake.url, meetup_fake_member_id),
                    "id": "",
                    "updated": fake.word(),
                    "lat": fake.latitude()
                }
            },
        }
    },

    Urls.MEETUP[Urls.VENUES].format(''): {
        'POST': {
            codes.OK: {
                'status_code': codes.CONFLICT,
                "errors": [
                    {
                        "code": "venue_error",
                        "message": "potential matches",
                        "potential_matches": [
                            {"visibility": fake.word(),
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
                             } for _ in xrange(random.randint(1, 5))]}
                ]
            }
        }
    }
    ,

    Urls.MEETUP[Urls.EVENTS].format(''): {
        'POST': {
            codes.OK: {
                'status_code': codes.CREATED,
                'id': CampaignsTestsHelpers.get_non_existing_id(Event)
            }
        }
    }
}
