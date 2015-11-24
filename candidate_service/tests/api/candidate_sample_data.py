"""
This module entails sample-data functions for testing
"""
# Standard libraries
import random
from random import randrange

# Faker
from faker import Faker
fake = Faker()


def generate_single_candidate_data(areas_of_interest=list()):
    """
    :rtype: dict
    """
    if not isinstance(areas_of_interest, list):
        areas_of_interest = [areas_of_interest]

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
                                "third_party": "false"},
            'work_experiences': [
                {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                 'state': fake.state(), 'experience_bullets': [
                    {'description': fake.sentence()}
                ]}
            ],
            'educations': [
                {'school_name': 'SJSU', 'city': 'San Jose', 'country': 'USA', 'degrees': [
                    {'type': 'BS', 'title': 'dancing',
                     'degree_bullets': [{'major': fake.job()}]
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
            ],
            'areas_of_interest': [{'id': area_of_interest.id, 'name': area_of_interest.name}
                                  for area_of_interest in areas_of_interest]
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
            {'address_line_1': fake.street_address(), 'city': fake.city(),
             'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
        ]}}
    # Data for creating a Candidate + CandidateAddress
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'addresses': [
        {'address_line_1': fake.street_address(), 'city': fake.city(),
         'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
    ]}}

    return data


def candidate_areas_of_interest(aoi, candidate_id):
    """
    Sample data for creating Candidate with CandidateAreaOfInterest.
    Date for updating will be returned if candidate_id is provided.
    :rtype  dict
    """
    # Data for adding a CandidateAreaOfInterest to an existing Candidate
    data = {'candidate': {'id': candidate_id,
                          'areas_of_interest': [{'id': aoi.id, 'name': aoi.name}]
                          }}

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
                 'end_year': '2006', 'end_month': '12', 'gpa': 1.5, 'degree_bullets': [
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
                 'end_year': '2006', 'end_month': '12', 'gpa': 1.5, 'degree_bullets': [
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
             'is_current': True, 'experience_bullets': [{'description': fake.sentence()}]}]}}
    # Data for updating an existing CandidateExperience
    elif candidate_id and experience_id and not experience_bullet_id:
        data = {'candidate': {'id': candidate_id, 'work_experiences': [
            {'id': experience_id, 'organization': fake.company(), 'position': fake.job(),
             'city': fake.city(), 'state': fake.state(), 'start_year': '2008', 'end_year': 2012,
             'start_month': 10, 'end_month': 2, 'is_current': True,
             'experience_bullets': [{'description': fake.sentence()}]
             }]}}
    # Data for updating an existing CandidateExperienceBullet
    elif candidate_id and experience_id and experience_bullet_id:
        data = {'candidate': {'id': candidate_id, 'work_experiences': [
            {'id': experience_id, 'experience_bullets': [
                {'id': experience_bullet_id, 'description': fake.sentence()}
            ]}]}}
    # Data for creating Candidate + CandidateExperience
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'work_experiences': [
            {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
             'state': fake.state(), 'start_year': '2008', 'end_year': 2012, 'start_month': 10, 'end_month': 2,
             'is_current': True, 'experience_bullets': [{'description': fake.sentence()}]}]}}

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
            "salary": randrange(50000, 300000), "tax_terms": "full-time employment", "third_party": False
        }}}
    elif candidate_id and work_preference_id:
        data = {'candidate': {'id': candidate_id, 'work_preference': {'id': work_preference_id,
            "relocate": True, "authorization": "us citizen", "telecommute": False,
            "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
            "salary": randrange(50000, 300000), "tax_terms": "full-time employment", "third_party": False
        }}}
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'work_preference': {
            "relocate": True, "authorization": "us citizen", "telecommute": False,
            "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
            "salary": randrange(50000, 300000), "tax_terms": "full-time employment", "third_party": False
        }}}

    return data


def candidate_emails(candidate_id=None, email_id=None):
    """
    Sample data for creating Candidate + CandidateEmail
    :rtype  dict
    """
    # Data for adding CandidateEmail to an existing Candidate
    if candidate_id and not email_id:
        data = {'candidate': {'id': candidate_id, 'emails': [{'label': 'work', 'address': fake.email()}]}}
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
        data = {'candidate': {'id': candidate_id, 'phones': [{'label': 'home',
                                                              'value': fake.phone_number()}]}}
    # Data for updating an existing CandidatePhone
    elif candidate_id and phone_id:
        data = {'candidate': {'id': candidate_id, 'phones': [{'id': phone_id, 'label': 'home',
                                                              'value': fake.phone_number()}]}}
    # Data for creating Candidate + CandidatePhone
    else:
        data = {'candidate': {'emails': [{'address': fake.email()}], 'phones': [
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
