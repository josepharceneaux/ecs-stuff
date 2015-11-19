import random
from random import randrange
from faker import Faker
fake = Faker()


def generate_single_candidate_data():
    data = {'candidates': [
        {
            'first_name': fake.first_name(),
            'middle_name': fake.first_name(),
            'last_name': fake.last_name(),
            'emails': [
                {'label': 'Primary', 'address': fake.email()},
                {'label': 'work', 'address': fake.company_email()}
            ],
            'phones': [
                {'label': 'mobile', 'value': fake.phone_number()},
                {'label': 'Work', 'value': fake.phone_number()}
            ],
            'addresses': [
                {'address_line_1': fake.street_address(), 'city': fake.city(),
                 'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()},
                {'address_line_1': fake.street_address(), 'city': fake.city(),
                 'state': fake.state(), 'zip_code': fake.postcode(), 'country': fake.country()}
            ],
            'work_preference': {"relocate": False, "authorization": "US Citizen", "telecommute": True,
                                "travel_percentage": randrange(0, 100),
                                "hourly_rate": '%.2f' % random.uniform(20, 90),
                                "salary": randrange(50000, 300000),
                                "tax_terms": "full-time employment",
                                "security_clearance": "none",
                                "third_party": "false"},  # TODO boolean
            'work_experiences': [
                {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                 'state': fake.state(), 'work_experience_bullets': [
                    {'description': fake.sentence()}
                ]}
            ],
            'educations': [
                {'school_name': 'SJSU', 'city': 'San Jose', 'country': 'USA', 'degrees': [
                    {'type': 'BS', 'title': 'dancing',
                     'degree_bullets': [{'major': fake.job()}]   # TODO major
                     }
                ]}
            ],
            'military_services': [
                {'country': 'us', 'branch': fake.military_ship(), 'highest_rank': 'lieutenant',
                 'comments': fake.sentence()}
            ],
            'preferred_locations': [
                {'city': fake.city(), 'region': fake.state()},
                {'city': fake.city(), 'region': fake.state()}  # TODO state
            ],
            'skills': [
                {'name': 'payroll'}, {'name': 'sql'}, {'name': 'excell'} # TODO name
            ],
            'social_networks': [
                {'profile_url': 'http://www.facebook.com/1024359318', 'name': 'facebook'},
                {'profile_url': 'https://twitter.com/dmcnulla', 'name': 'twitter'}
            ]
            # 'areas_of_interest': [{'id': 7}, {'id': 8}],
            # 'custom_fields': [{'id': 7}, {'id': 8}]
        }
    ]}
    return data


def generate_multiple_candidates_data():
    data = {'candidates': [
        {'first_name': fake.first_name(), 'last_name': fake.last_name(),
         'emails': [{'label': 'Primary', 'address': fake.email()}]},
        {'first_name': fake.first_name(), 'last_name': fake.last_name(),
         'emails': [{'label': 'Primary', 'address': fake.email()}]},
        {'first_name': fake.first_name(), 'last_name': fake.last_name(),
         'emails': [{'label': 'Primary', 'address': fake.email()}]}
    ]}
    return data