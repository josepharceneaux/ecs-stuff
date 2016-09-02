"""
Here we have mocked data for Meetup API.
"""
# Standard Library
import json
import sys
import random
from random import randint
from itertools import repeat, chain

# Third Party
from requests import codes

# Application Specific
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.event import Event
from social_network_service.common.redis_cache import redis_store2
from social_network_service.common.utils.test_utils import fake
from social_network_service.modules.constants import MEETUP
from social_network_service.modules.urls import SocialNetworkUrls as Urls
from social_network_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

# Prepare data for dictionary below
meetup_fake_member_id = fake.random_number()
meetup_kv = json.loads(redis_store2.get(MEETUP.title()))
valid_access_token = meetup_kv['access_token']
valid_refresh_token = meetup_kv['refresh_token']
non_existent_event_id = CampaignsTestsHelpers.get_non_existing_id(Event)
events_id = []


def get_random_event_id():
    event_id = fake.random_number()
    events_id.append(event_id)
    return event_id


def delete_event_id(event_id):
    i = events_id.index(event_id)
    try:
        del events_id[i]
    except IndexError:
        pass


def get_meetup_client():
    """
    Return meetup client from db
    """
    social_network = SocialNetwork.get_by_name(MEETUP.title())
    return {
        'grant_type': 'refresh_token',
        'refresh_token': valid_refresh_token,
        'client_id': social_network.client_key,
        'client_secret': social_network.secret_key
    }


def meetup_vendor_api(event_id=None):
    """
    Returns Meetup API URLs
    """
    return {
        Urls.MEETUP[Urls.VALIDATE_TOKEN].format(''): {
            'GET': {
                'expected_headers':
                    {
                        'headers': {
                            'Authorization': 'Bearer {}'.format(valid_access_token)
                        },
                        'on_fail': {
                            codes.UNAUTHORIZED
                        }
                    },
                codes.OK: {
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
                        "link": "{}/members/{}".format(fake.url(), meetup_fake_member_id),
                        "lon": float(fake.longitude()),
                        "other_services": {},
                        "name": fake.word(),
                        "visited": fake.random_number(),
                        "self": {
                            "common": {}
                        },
                        "id": meetup_fake_member_id,
                        "state": fake.word(),
                        "lang": fake.word(),
                        "lat": float(fake.latitude()),
                        "status": fake.word()
                    },
                },
                codes.UNAUTHORIZED: {
                    'response': {
                        'Unauthorized': 'Unauthorized access'
                    }
                }
            },
            'POST': {
                'expected_headers':
                    {
                        'headers': {
                            'Authorization': 'Bearer {}'.format(valid_access_token)
                        },
                        'on_fail': {
                            codes.UNAUTHORIZED
                        }
                    },
                codes.OK: {
                    'status_code': codes.OK,
                    'response': {
                        'id': meetup_fake_member_id
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
                'expected_headers':
                    {
                        'headers': {
                            'Authorization': 'Bearer {}'.format(valid_access_token)
                        },
                        'on_fail': {
                            codes.UNAUTHORIZED
                        }
                    },
                codes.OK: {
                    'status_code': codes.OK,
                    'response': {
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
                                     "lon": float(fake.longitude()),
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
                                     "lat": float(fake.latitude()),
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
                            "lon": float(fake.longitude()),
                            "title": fake.word(),
                            "url": "%smember_id=%s&offset=0&format=json&page=800&" % (
                                fake.url(), meetup_fake_member_id),
                            "id": "",
                            "updated": fake.word(),
                            "lat": float(fake.latitude())
                        }
                    },
                },
                codes.UNAUTHORIZED: {
                    'response': {
                        'Unauthorized': 'Unauthorized access'
                    }
                }
            }
        },

        Urls.MEETUP[Urls.VENUES].format(''): {
            'POST': {
                codes.OK: {
                    'status_code': codes.CONFLICT,
                    'response': {
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
                                     "lon": float(fake.longitude()),
                                     "lat": float(fake.latitude()),
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
        }
        ,
        Urls.MEETUP[Urls.EVENTS].format(''): {
            'POST': {
                codes.OK: {
                    'status_code': codes.CREATED,
                    'response': {
                        # Need to generate random number so that event won't found in database
                        'id': fake.random_number(),
                    }
                }
            },
            'DELETE': {
                codes.OK: {
                    'status_code': codes.OK
                }
            },

            'PUT': {
                codes.OK: {
                    'status_code': codes.CREATED,
                    'response': {
                        'id': event_id
                    }
                }
            },
            'GET': {
                codes.OK: {
                    'status_code': codes.OK,
                    'response': {
                        'ids': ['']
                    }
                }
            }
        },
        Urls.MEETUP[Urls.EVENT].format('', event_id): {
            'DELETE': {
                codes.OK: {
                    'status_code': codes.OK
                }
            },

            'PUT': {
                codes.OK: {
                    'status_code': codes.CREATED,
                    'response': {
                        'id': event_id
                    }
                }
            }
        }
    }


def meetup_vendor_auth():
    """
    Returns JSON dict for mocked data of Meetup
    :return:
    :rtype:
    """
    return {
        Urls.MEETUP[Urls.REFRESH_TOKEN].format(''): {
            'POST': {
                'expected_payload': {
                    'payload': get_meetup_client(),
                    'on_fail': codes.UNAUTHORIZED,
                    'ignore': ['refresh_token']
                },
                codes.OK: {
                    'status_code': codes.ok,
                    'response': {
                        "expires_in": 3600,
                        "access_token": valid_access_token,
                        "refresh_token": valid_refresh_token,
                        "token_type": "bearer"
                    },
                },
                codes.UNAUTHORIZED: {
                    'response': {
                        'Unauthorized': 'Unauthorized access'
                    }
                }
            }
        }
    }


def meetup_vendor(url_type, event_id=None):
    """
    Returns JSON dict for mocked data of Meetup
    :param url_type: Check if request URL is of auth type
    :type url_type: str
    :rtype: dict
    """
    if url_type.lower() == 'auth':
        return meetup_vendor_auth()

    elif url_type.lower() == 'api':
        return meetup_vendor_api(event_id=event_id)

    else:
        return []
