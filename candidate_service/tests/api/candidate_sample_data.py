"""
This module entails sample-data functions for testing
"""
# Standard libraries
import random
from random import randrange

# Faker
from faker import Faker
fake = Faker()


def generate_single_candidate_data():
    """
    :rtype: dict
    """
    data = {'candidate':
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
                 'state': fake.state(), 'experience_bullets': [
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
        }
    }

    return data


def candidate_data_for_update(candidate_id, email_1_id, email_2_id, phone_1_id,
                              phone_2_id, address_1_id, address_2_id,
                              work_preference_id, work_experience_1_id,
                              education_1_id, degree_1_id, military_1_id,
                              preferred_location_1_id, preferred_location_2_id,
                              skill_1_id, skill_2_id, skill_3_id, social_1_id,
                              social_2_id):
    data = {'candidates': [
        {
            'id': candidate_id,
            'first_name': fake.first_name(),
            'middle_name': fake.first_name(),
            'last_name': fake.last_name(),
            'emails': [
                {'id': email_1_id,'label': 'Primary', 'address': fake.email()},
                {'id': email_2_id, 'label': 'work', 'address': fake.company_email()}
            ],
            'phones': [
                {'id': phone_1_id, 'label': 'mobile', 'value': fake.phone_number()},
                {'id': phone_2_id, 'label': 'Work', 'value': fake.phone_number()}
            ],
            'addresses': [
                {'id': address_1_id, 'address_line_1': fake.street_address(), 'city': fake.city(),
                 'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()},
                {'id': address_2_id, 'address_line_1': fake.street_address(), 'city': fake.city(),
                 'state': fake.state(), 'zip_code': fake.postcode(), 'country': fake.country()}
            ],
            'work_preference': {'id': work_preference_id, "relocate": False, "authorization": "US Citizen",
                                "telecommute": True, "travel_percentage": randrange(0, 100),
                                "hourly_rate": '%.2f' % random.uniform(20, 90),
                                "salary": randrange(50000, 300000),
                                "tax_terms": "full-time employment",
                                "security_clearance": "none",
                                "third_party": "false"},
            'work_experiences': [
                {'id': work_experience_1_id, 'organization': fake.company(),
                 'position': fake.job(), 'city': fake.city(),
                 'state': fake.state(), 'work_experience_bullets': [{'description': None}]
                 }
            ],
            'educations': [
                {'id': education_1_id, 'school_name': 'SJSU', 'city': 'San Jose',
                 'country': 'USA', 'degrees': [
                    {'id': degree_1_id,'type': 'BS', 'title': 'dancing'}
                ]}
            ],
            'military_services': [
                {'id': military_1_id, 'country': 'us', 'branch': fake.military_ship(),
                 'highest_rank': 'lieutenant', 'comments': fake.sentence()}
            ],
            'preferred_locations': [
                {'id': preferred_location_1_id, 'city': fake.city(), 'region': fake.state()},
                {'id': preferred_location_2_id, 'city': fake.city(), 'region': fake.state()}  # TODO state
            ],
            'skills': [
                {'id': skill_1_id, 'name': 'payroll'},
                {'id': skill_2_id, 'name': 'sql'},
                {'id': skill_3_id, 'name': 'excell'}
            ],
            'social_networks': [
                {'id': social_1_id, 'profile_url': 'http://www.facebook.com/', 'name': 'facebook'},
                {'id': social_2_id, 'profile_url': 'https://twitter.com/', 'name': 'twitter'}
            ]
        }
    ]}

    return data


def candidate_educations():
    """
    Sample data for creating Candidate with CandidateEducation, CandidateEducationDegree,
     and CandidateEducationBullets
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': 'some@nice.com'}], 'educations': [
        {'school_name': 'stanford', 'school_type': 'university', 'city': 'palo alto',
         'state': 'ca', 'is_current': False, 'degrees': [
            {'degree_type': 'bs', 'degree_title': 'mr. enginner', 'start_year': '2002', 'start_month': '11',
             'end_year': '2006', 'end_month': '12', 'gpa': 1.5, 'degree_bullets': [
                {'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'}
            ]}
        ]}
    ]}}
    return data


def candidate_work_experience():
    """
    Sample data for creating Candidate with CandidateExperience and CandidateExperienceBullet
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'work_experiences': [
        {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
         'state': fake.state(), 'start_year': '2008', 'end_year': 2012, 'start_month': 10, 'end_month': 2,
         'is_current': True, 'experience_bullets': [{'description': fake.sentence()}]
         }]}}
    return data


def candidate_work_preference():
    """
    Sample data for creating Candidate and CandidateWorkPreference
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'work_preference': {
        "relocate": True, "authorization": "us citizen", "telecommute": False,
        "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
        "salary": randrange(50000, 300000), "tax_terms": "full-time employment", "third_party": False
    }}}
    return data


def candidate_phones():
    """
    Sample data for creating Candidate and CandidatePhones
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'phones': [
        {'label': 'home', 'value': fake.phone_number()},
        {'label': 'work', 'value': fake.phone_number()}
    ]}}
    return data


def candidate_military_service():
    """
    Sample data for Candidate and CandidateMilitaryService
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'military_services': [
        {'country': 'bahrain', 'branch': fake.military_ship(), 'highest_rank': 'lieutenant',
         'comments': fake.sentence()}
    ]}}
    return data

def candidate_preferred_locations():
    """
    Sample data for Candidate and CandidatePreferredLocation
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'preferred_locations': [
        {'address': fake.street_address(), 'country': 'al', 'city': fake.city(),
         'state': fake.state()}
    ]}}
    return data


def candidate_skills():
    """
    Sample data for Candidate and CandidateSkill
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'skills': [
        {'name': 'payroll', 'months_used': 48},
        {'name': 'tinder', 'months_used': 2}
    ]}}
    return data


def candidate_social_network():
    """
    Sample data for Candidate and CandidateSocialNetwork
    :rtype  dict
    """
    data = {'candidate': {'emails': [{'address': fake.email()}], 'social_networks': [
        {'name': 'linkedin', 'profile_url': 'http://www.linkedin.com/in/davemcnulla'},
        {'name': 'google+', 'profile_url': 'https://plus.google.com/+davemcnulla'}
    ]}}
    return data
