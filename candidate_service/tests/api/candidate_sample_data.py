"""
This module entails sample-data functions for testing
"""
# Standard libraries
import random
from random import randrange

# Conftest
from candidate_service.common.tests.conftest import (
    areas_of_interest_for_domain, custom_field_for_domain
)

# Faker
from faker import Faker
fake = Faker()


def generate_single_candidate_data(domain_id=None):
    """
    Function creates a sample data for Candidate and all of candidate's related objects.
    If domain_id is provided, areas_of_interest and custom_fields will also be created. This is
    because areas_of_interest and custom_fields must be created for user's domain first before
    they can be used for candidate's sample data.
    :rtype: dict
    """
    areas_of_interest, custom_fields = [], []
    if domain_id:
        areas_of_interest = areas_of_interest_for_domain(domain_id=domain_id)
        custom_fields = custom_field_for_domain(domain_id=domain_id)

    data = {'candidate':
        {
            'first_name': fake.first_name(),
            'middle_name': fake.first_name(),
            'last_name': fake.last_name(),
            'emails': [
                {'label': 'Primary', 'address': fake.email(), 'is_default': True},
                {'label': 'work', 'address': fake.company_email(), 'is_default': False}
            ],
            'phones': [
                {'label': 'mobile', 'value': '8009346489', 'is_default': True},
                {'label': 'Work', 'value': '8009346489', 'is_default': False}
            ],
            'addresses': [
                {
                    'address_line_1': fake.street_address(), 'city': fake.city(),
                    'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country(),
                    'is_default': True,
                },
                {
                    'address_line_1': fake.street_address(), 'city': fake.city(),
                    'state': fake.state(), 'zip_code': fake.postcode(), 'country': fake.country(),
                    'is_default': False
                }
            ],
            'work_preference': {
                "relocate": False, "authorization": "US Citizen", "telecommute": True,
                "travel_percentage": randrange(0, 100),
                "hourly_rate": '%.2f' % random.uniform(20, 90),
                "salary": randrange(50000, 300000),
                "employment_type": "full-time employment",
                "security_clearance": None,
                "third_party": False
            },
            'work_experiences': [
                {
                    'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                    'state': fake.state(), 'start_month': 11, 'start_year': 2005, 'is_current': True,
                    'end_month': 10, 'end_year': 2007, 'bullets': [
                        {'description': fake.bs()}, {'description': fake.bs()}
                    ]
                },
                {
                    'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                    'state': fake.state(), 'start_month': '1', 'start_year': '2008',
                    'end_month': '5', 'end_year': '2012', 'bullets': [
                        {'description': fake.bs()}, {'description': fake.bs()}
                    ]
                }
            ],
            'educations': [
                {
                    'school_name': 'SJSU', 'city': 'San Jose', 'country': 'USA', 'degrees': [
                        {
                            'type': 'BS', 'title': 'Bachelors', 'start_year': 2008, 'start_month': 9,
                            'end_year': 2012, 'end_month': 12, 'gpa': 3.5,
                            'bullets': [{'major': fake.job(), 'comments': fake.bs()}]
                        }
                    ]
                },
                {
                    'school_name': 'De Anza', 'city': 'Cupertino', 'country': 'US', 'degrees': [
                        {
                            'type': 'AA', 'title': 'Associate', 'start_date': 2006, 'start_month': 9,
                            'end_year': 2008, 'end_month': 9, 'gpa_num': 3,
                            'bullets': [{'major': fake.job(), 'comments': fake.bs()}]
                        }
                    ]
                }
            ],
            'military_services': [
                {
                    'country': 'us', 'branch': fake.military_ship(), 'highest_rank': 'lieutenant',
                    'status': 'active', 'highest_grade': '0-1', 'comments': fake.bs(),
                    'from_date': '1974-5-25', 'to_date': '1996-12-12'
                },
                {
                    'country': 'us', 'branch': fake.military_ship(), 'highest_rank': 'major',
                    'comments': fake.bs(), 'from_date': '2002-5-25', 'to_date': '2012-12-12'
                }
            ],
            'preferred_locations': [
                {'city': fake.city(), 'state': fake.state()},
                {'city': fake.city(), 'state': fake.state()}
            ],
            'skills': [
                {'name': 'payroll', 'months_used': 15, 'last_used_date': '2015-11-25'},
                {'name': 'sql', 'months_used': '24', 'last_used_date': '1998-10-19'}
            ],
            'social_networks': [
                {'profile_url': 'http://www.facebook.com/1024359318', 'name': 'facebook'},
                {'profile_url': 'https://twitter.com/dmcnulla', 'name': 'twitter'}
            ],
            'areas_of_interest': [{'area_of_interest_id': area_of_interest.id}
                                  for area_of_interest in areas_of_interest],
            'custom_fields': [{'custom_field_id': custom_field.id, 'value': custom_field.name}
                              for custom_field in custom_fields]
        }
    }
    return data


def candidate_data_for_update(candidate_id, email_1_id, email_2_id, phone_1_id,
                              phone_2_id, address_1_id, address_2_id,
                              work_preference_id, work_experience_1_id,
                              education_1_id, degree_1_id, military_1_id,
                              preferred_location_1_id, preferred_location_2_id,
                              skill_1_id, skill_2_id, social_1_id,
                              social_2_id):
    """
    Function will replace each field with params
    :rtype  dict
    """
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
                {'id': phone_1_id, 'label': 'mobile', 'value': '8009346489'},
                {'id': phone_2_id, 'label': 'Work', 'value': '8009346489'}
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
                                "security_clearance": False,
                                "third_party": False},
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
                {'id': skill_2_id, 'name': 'sql'}
            ],
            'social_networks': [
                {'id': social_1_id, 'profile_url': 'http://www.facebook.com/', 'name': 'facebook'},
                {'id': social_2_id, 'profile_url': 'https://twitter.com/', 'name': 'twitter'}
            ]
        }
    ]}

    return data


def candidate_addresses(candidate_id=None, address_id=None):
    """
    Sample data for creating or updating Candidate + CandidateAddress
    :rtype  dict
    """
    # Data for updating a CandidateAddress of an existing Candidate
    if candidate_id and address_id:
        data = {'candidate': {'id': candidate_id, 'addresses': [
            {'id': address_id, 'address_line_1': fake.street_address(), 'city': fake.city(),
             'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
        ]}}
    # Data for adding a CandidateAddress to an existing Candidate
    elif candidate_id and not address_id:
        data = {'candidate': {'id': candidate_id, 'addresses': [
            {'address_line_1': fake.street_address(), 'city': fake.city(), 'is_default': True,
             'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
        ]}}
    # Data for creating a Candidate + CandidateAddress
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'addresses': [
        {'address_line_1': fake.street_address(), 'city': fake.city(),
         'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
    ]}}

    return data


def candidate_areas_of_interest(domain_id, candidate_id=None, aoi_id=None):
    """
    Sample data for creating Candidate + CandidateAreaOfInterest.
    Date for updating will be returned if candidate_id is provided.
    :rtype  dict
    """
    # Create sample AreaOfInterest in domain
    areas_of_interest = areas_of_interest_for_domain(domain_id=domain_id)

    # Data for adding CandidateAreaOfInterest to existing Candidate
    if candidate_id and not aoi_id:
        data = {'candidate': {'id': candidate_id, 'areas_of_interest': [
            {'area_of_interest_id': area_of_interest.id} for area_of_interest in areas_of_interest
        ]}}
    elif candidate_id and aoi_id:
        data = {'candidate': {'id': candidate_id, 'areas_of_interest': [
            {'area_of_interest_id': area_of_interest.id} for area_of_interest in areas_of_interest
        ]}}
    # Data for creating Candidate + CandidateAreaOfInterest
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'areas_of_interest': [
            {'area_of_interest_id': area_of_interest.id} for area_of_interest in areas_of_interest
        ]}}
    return data


def candidate_custom_fields(domain_id, candidate_id=None):
    """
    Sample data for creating Candidate + CandidateCustomField.
    Data for updating will be returned if candidate_id is provided.
    :rtype  dict
    """
    custom_fields = custom_field_for_domain(domain_id=domain_id)

    # Data for adding CandidateCustomField to an existing candidate
    if candidate_id:
        data = {'candidate': {'id': candidate_id, 'custom_fields': [
            {'custom_field_id': custom_field.id, 'value': fake.word()} for custom_field in custom_fields
        ]}}
    # Data for creating Candidate + CandidateCustomField
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'custom_fields': [
            {'custom_field_id': custom_field.id, 'value': fake.word()} for custom_field in custom_fields
        ]}}
    return data


def candidate_educations(candidate_id=None, education_id=None):
    """
    Sample data for creating Candidate with CandidateEducation, CandidateEducationDegree,
     and CandidateEducationBullets
    :rtype  dict
    """
    # Data for adding CandidateEducation to an existing Candidate
    if candidate_id and not education_id:
        data = {'candidate': {'id': candidate_id, 'educations': [
            {'school_name': 'stanford', 'school_type': 'university', 'city': 'palo alto',
             'state': 'ca', 'is_current': False, 'degrees': [
                {'type': 'bs', 'title': 'engineer', 'start_year': '2002', 'start_month': '11',
                 'end_year': '2006', 'end_month': '12', 'gpa': 1.5, 'bullets': [
                    {'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'}
                ]}
            ]}
        ]}}
    # Data for updating an existing CandidateEducation
    elif candidate_id and education_id:
        data = {'candidate': {'id': candidate_id, 'educations': [
            {'id': education_id, 'school_name': 'westvalley', 'school_type': 'college', 'city': 'saratoga',
             'state': 'ca', 'is_current': True}
        ]}}
    # Data for adding Candidate + CandidateEducation
    else:
        data = {'candidate': {'emails': [{'address': 'some@nice.com'}], 'educations': [
            {'school_name': 'stanford', 'school_type': 'university', 'city': 'palo alto',
             'state': 'ca', 'is_current': False, 'degrees': [
                {'degree_type': 'bs', 'degree_title': 'engineer', 'start_year': '2002', 'start_month': '11',
                 'end_year': '2006', 'end_month': '12', 'gpa': 1.5, 'bullets': [
                    {'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'}
                ]}
            ]}
        ]}}

    return data


def candidate_experience(candidate_id=None, experience_id=None, experience_bullet_id=None):
    """
    Sample data for creating Candidate + CandidateExperience and CandidateExperienceBullet.
    :rtype  dict
    """
    # Data for adding CandidateExperience to an existing Candidate
    if candidate_id and not experience_id:
        data = {'candidate': {'id': candidate_id, 'work_experiences': [
            {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
             'state': fake.state(), 'start_year': '2008', 'end_year': 2012, 'start_month': 10, 'end_month': 2,
             'is_current': True, 'bullets': [{'description': fake.sentence()}]}]}}
    # Data for updating an existing CandidateExperience
    elif candidate_id and experience_id and not experience_bullet_id:
        data = {'candidate': {'id': candidate_id, 'work_experiences': [
            {'id': experience_id, 'organization': fake.company(), 'position': fake.job(),
             'city': fake.city(), 'state': fake.state(), 'start_year': '2008', 'end_year': 2012,
             'start_month': 10, 'end_month': 2, 'is_current': True,
             'bullets': [{'description': fake.bs()}]
             }]}}
    # Data for updating an existing CandidateExperienceBullet
    elif candidate_id and experience_id and experience_bullet_id:
        data = {'candidate': {'id': candidate_id, 'work_experiences': [
            {'id': experience_id, 'bullets': [
                {'id': experience_bullet_id, 'description': fake.bs()}
            ]}]}}
    # Data for creating Candidate + CandidateExperience
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'work_experiences': [
            {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
             'state': fake.state(), 'start_year': '2008', 'end_year': 2012, 'start_month': 10, 'end_month': 2,
             'is_current': True, 'bullets': [{'description': fake.bs()}]}]}}

    return data


def candidate_work_preference(candidate_id=None, work_preference_id=None):
    """
    Sample data for creating Candidate + CandidateWorkPreference
    :rtype  dict
    """
    # Data for adding CandidateWorkPreference to an existing Candidate
    if candidate_id and not work_preference_id:
        data = {'candidate': {'id': candidate_id, 'work_preference': {
            "relocate": True, "authorization": "us citizen", "telecommute": False,
            "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
            "salary": randrange(50000, 300000), "employment_type": "full-time employment", "third_party": False
        }}}
    elif candidate_id and work_preference_id:
        data = {'candidate': {'id': candidate_id, 'work_preference': {'id': work_preference_id,
            "relocate": True, "authorization": "us citizen", "telecommute": False,
            "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
            "salary": randrange(50000, 300000), "employment_type": "full-time employment", "third_party": False
        }}}
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'work_preference': {
            "relocate": True, "authorization": "us citizen", "telecommute": False,
            "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
            "salary": randrange(50000, 300000), "employment_type": "full-time employment", "third_party": False
        }}}

    return data


def candidate_emails(candidate_id=None, email_id=None):
    """
    Sample data for creating Candidate + CandidateEmail
    :rtype  dict
    """
    # Data for adding CandidateEmail to an existing Candidate
    if candidate_id and not email_id:
        data = {'candidate': {'id': candidate_id, 'emails': [{'label': 'work', 'address': fake.email(),
                                                              'is_default': True}]}}
    # Data for updating an existing CandidateEmail
    elif candidate_id and email_id:
        data = {'candidate': {'id': candidate_id, 'emails': [{'id': email_id, 'label': 'primary',
                                                              'address': fake.email()}]}}
    # Data for creating Candidate + CandidateEmail
    else:
        data = {'candidate': {'emails': [{'label': 'primary', 'address': fake.email()}]}}

    return data


def candidate_phones(candidate_id=None, phone_id=None):
    """
    Sample data for creating Candidate + CandidatePhones
    :rtype  dict
    """
    # Data for adding CandidatePhone to an existing Candidate
    if candidate_id and not phone_id:
        data = {'candidate': {'id': candidate_id, 'phones': [
            {'label': 'home', 'value': '8009346489', 'is_default': True}
        ]}}
    # Data for updating an existing CandidatePhone
    elif candidate_id and phone_id:
        data = {'candidate': {'id': candidate_id, 'phones': [{'id': phone_id, 'label': 'home',
                                                              'value': '8009346489'}]}}
    # Data for creating Candidate + CandidatePhone
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'phones': [
            {'label': 'work', 'value': '8009346489'}
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
