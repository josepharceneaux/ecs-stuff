"""
This module entails candidate sample data functions for testing
"""
# Standard libraries
import random
from random import randrange

from candidate_service.common.utils.handy_functions import sample_phone_number

# Faker
from faker import Faker
# Instantiate faker
fake = Faker()


def generate_single_candidate_data(talent_pool_ids, areas_of_interest=None, custom_fields=None):
    """
    Function creates a sample data for Candidate and all of candidate's related objects.
    If domain_id is provided, areas_of_interest and custom_fields will also be created. This is
    because areas_of_interest and custom_fields must be created for user's domain first before
    they can be used for candidate's sample data.
    :type talent_pool_ids:      list[int]
    :type areas_of_interest:    list[int]
    :type custom_fields:        list[int]
    :rtype: dict
    """
    aois, cfs = [], []
    if areas_of_interest:
        aois = areas_of_interest
    if custom_fields:
        cfs = custom_fields

    data = {'candidates':
        [
            {
                'first_name': fake.first_name(),
                'middle_name': fake.first_name(),
                'last_name': fake.last_name(),
                'emails': [
                    {'label': 'Primary', 'address': fake.safe_email(), 'is_default': True},
                    {'label': 'work', 'address': fake.company_email(), 'is_default': False}
                ],
                'phones': [
                    {'label': 'mobile', 'value': sample_phone_number(), 'is_default': True},
                    {'label': 'Work', 'value': sample_phone_number(), 'is_default': False}
                ],
                'addresses': [
                    {
                        'address_line_1': fake.street_address(), 'city': fake.city(),
                        'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country(),
                        'is_default': True, 'po_box': None
                    },
                    {
                        'address_line_1': fake.street_address(), 'city': fake.city(),
                        'state': fake.state(), 'zip_code': fake.postcode(), 'country': fake.country(),
                        'is_default': False, 'po_box': ''
                    }
                ],
                'work_preference': {
                    "relocate": False, "authorization": "US Citizen", "telecommute": True,
                    "travel_percentage": randrange(0, 100),
                    "hourly_rate": float('%.2f' % random.uniform(20, 90)),
                    "salary": randrange(50000, 300000),
                    "employment_type": "full-time employment",
                    "security_clearance": None,
                    "third_party": False
                },
                'work_experiences': [
                    {
                        'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                        'state': fake.state(), 'start_month': 11, 'start_year': 2005, 'is_current': True,
                        'end_month': 10, 'end_year': 2007, 'country': fake.country(), 'bullets': [
                        {'description': fake.bs()}, {'description': fake.bs()}
                    ]
                    },
                    {
                        'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                        'state': fake.state(), 'start_month': 1, 'start_year': 2008, 'is_current': None,
                        'end_month': 5, 'end_year': 2012, 'country': fake.country(), 'bullets': [
                        {'description': fake.bs()}, {'description': fake.bs()}
                    ]
                    }
                ],
                'educations': [
                    {
                        'school_name': 'SJSU', 'city': 'San Jose', 'state': 'CA', 'country': 'USA',
                        'school_type': 'university', 'is_current': False, 'degrees': [
                        {
                            'type': 'BS', 'title': 'Bachelors', 'start_year': 2008, 'start_month': 9,
                            'end_year': 2012, 'end_month': 12, 'gpa': 3.5,
                            'bullets': [{'major': fake.job(), 'comments': fake.bs()}]
                        }
                    ]
                    },
                    {
                        'school_name': 'De Anza', 'school_type': 'college', 'city': 'cupertino', 'state': 'california',
                        'country': 'america', 'is_current': True, 'degrees': [
                        {
                            'type': 'AA', 'title': 'Associate', 'start_year': 2006, 'start_month': 9,
                            'end_year': 2008, 'end_month': 9, 'gpa': 3,
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
                        'status': 'active', 'highest_grade': '0-1', 'comments': fake.bs(),
                        'from_date': '2002-5-25', 'to_date': '2012-12-12'
                    }
                ],
                'preferred_locations': [
                    {'city': fake.city(), 'state': fake.state(), 'country': fake.country()},
                    {'city': fake.city(), 'state': fake.state(), 'country': fake.country()}
                ],
                'skills': [
                    {'name': 'payroll', 'months_used': 15, 'last_used_date': fake.date()},
                    {'name': 'sql', 'months_used': 24, 'last_used_date': fake.date()}
                ],
                'social_networks': [
                    {'profile_url': 'http://www.facebook.com/1024359318', 'name': 'facebook'},
                    {'profile_url': 'https://twitter.com/dmcnulla', 'name': 'twitter'}
                ],
                'areas_of_interest': [{'area_of_interest_id': area_of_interest.id}
                                      for area_of_interest in aois],
                'custom_fields': [{'custom_field_id': custom_field.id, 'value': custom_field.name}
                                  for custom_field in cfs],
                'talent_pool_ids': {'add': talent_pool_ids}
            }
        ]
    }
    return data


def candidate_addresses(candidate_id=None, address_id=None):
    """
    Sample data for creating or updating Candidate + CandidateAddress
    :rtype  dict
    """
    # Data for updating a CandidateAddress of an existing Candidate
    if candidate_id and address_id:
        data = {'candidates': [{'id': candidate_id, 'addresses': [
            {'id': address_id, 'address_line_1': fake.street_address(), 'city': fake.city(),
             'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
        ]}]}

    # Data for adding a CandidateAddress to an existing Candidate
    elif candidate_id and not address_id:
        data = {'candidates': [{'id': candidate_id, 'addresses': [
            {'address_line_1': fake.street_address(), 'city': fake.city(), 'is_default': True,
             'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
        ]}]}

    # Data for creating a Candidate + CandidateAddress
    else:
        data = {'candidates': [{'emails': [{'address': fake.email()}], 'addresses': [
            {'address_line_1': fake.street_address(), 'city': fake.city(),
             'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}
        ]}]}

    return data


def candidate_areas_of_interest(domain_aoi, candidate_id=None, aoi_id=None):
    """
    Sample data for creating Candidate + CandidateAreaOfInterest.
    Date for updating will be returned if candidate_id is provided.
    :rtype  dict
    """
    # Data for adding CandidateAreaOfInterest to existing Candidate
    if candidate_id and not aoi_id:
        data = {'candidates': [{'id': candidate_id, 'areas_of_interest': [
            {'area_of_interest_id': area_of_interest.id} for area_of_interest in domain_aoi]}]}
    elif candidate_id and aoi_id:
        data = {'candidates': [{'id': candidate_id, 'areas_of_interest': [
            {'area_of_interest_id': area_of_interest.id} for area_of_interest in domain_aoi]}]}
    # Data for creating Candidate + CandidateAreaOfInterest
    else:
        data = {'candidates': [{'emails': [{'address': fake.email()}], 'areas_of_interest': [
            {'area_of_interest_id': area_of_interest.id} for area_of_interest in domain_aoi]}]}
    return data


def candidate_custom_fields(domain_custom_fields, candidate_id=None):
    """
    Sample data for creating Candidate + CandidateCustomField.
    Data for updating will be returned if candidate_id is provided.
    :rtype  dict
    """
    # Data for adding CandidateCustomField to an existing candidate
    if candidate_id:
        data = {'candidates': [{'id': candidate_id, 'custom_fields': [
            {'custom_field_id': custom_field.id, 'value': fake.word()}
            for custom_field in domain_custom_fields]}]}
    # Data for creating Candidate + CandidateCustomField
    else:
        data = {'candidates': [{'emails': [{'address': fake.email()}], 'custom_fields': [
            {'custom_field_id': custom_field.id, 'value': fake.word()}
            for custom_field in domain_custom_fields]}]}
    return data


def candidate_educations(candidate_id=None, education_id=None):
    """
    Sample data for creating Candidate with CandidateEducation, CandidateEducationDegree,
     and CandidateEducationBullets
    :rtype  dict
    """
    assert candidate_id is not None or education_id is not None
    # Data for adding CandidateEducation to an existing Candidate
    if candidate_id and not education_id:
        data = {'candidates': [{'id': candidate_id, 'educations': [
            {'school_name': 'stanford', 'school_type': 'university', 'city': 'palo alto',
             'state': 'ca', 'country': None, 'is_current': False, 'degrees': [
                {'type': 'bs', 'title': 'engineer', 'start_year': 2002, 'start_month': 11,
                 'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                    {'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'}
                ]}
            ]}
        ]}]}

    # Data for updating an existing CandidateEducation
    elif candidate_id and education_id:
        data = {'candidates': [{'id': candidate_id, 'educations': [
            {'id': education_id, 'school_name': 'westvalley', 'school_type': 'college', 'city': 'saratoga',
             'state': 'ca', 'country': None, 'is_current': True, 'degrees': None}
        ]}]}

    return data


def candidate_experience(candidate_id=None, experience_id=None, experience_bullet_id=None):
    """
    Sample data for creating Candidate + CandidateExperience and CandidateExperienceBullet.
    :rtype  dict
    """
    # Data for adding CandidateExperience to an existing Candidate
    if candidate_id and not experience_id:
        data = {'candidates': [{'id': candidate_id, 'work_experiences': [
            {'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
             'state': fake.state(), 'start_year': 2008, 'end_year': 2012, 'start_month': 10, 'end_month': 2,
             'is_current': True, 'bullets': [{'description': fake.sentence()}]}]}]}

    # Data for updating an existing CandidateExperience
    elif candidate_id and experience_id and not experience_bullet_id:
        data = {'candidates': [{'id': candidate_id, 'work_experiences': [
            {'id': experience_id, 'organization': fake.company(), 'position': fake.job(),
             'city': fake.city(), 'state': fake.state(), 'start_year': 2008, 'end_year': 2012,
             'start_month': 10, 'end_month': 2, 'is_current': True,
             'bullets': [{'description': fake.bs()}]
             }]}]}

    # Data for updating an existing CandidateExperienceBullet
    elif candidate_id and experience_id and experience_bullet_id:
        data = {'candidates': [{'id': candidate_id, 'work_experiences': [
            {'id': experience_id, 'bullets': [
                {'id': experience_bullet_id, 'description': fake.bs()}
            ]}]}]}

    # Data for creating Candidate + CandidateExperience
    else:
        data = reset_all_data_except_param(generate_single_candidate_data(), 'work_experiences')

    return data


def candidate_work_preference(candidate_id=None, work_preference_id=None):
    """
    Sample data for creating Candidate + CandidateWorkPreference
    :rtype  dict
    """
    # Data for adding CandidateWorkPreference to an existing Candidate
    if candidate_id and not work_preference_id:
        data = {'candidates': [{'id': candidate_id, 'work_preference': {
            "relocate": True, "authorization": "us citizen", "telecommute": False,
            "travel_percentage": randrange(0, 100), "hourly_rate": '%.2f' % random.uniform(20, 90),
            "salary": randrange(50000, 300000), "employment_type": "full-time employment", "third_party": False
        }}]}

    # Data for updating an existing CandidateWorkPreference
    elif candidate_id and work_preference_id:
        data = {'candidates': [
            {'id': candidate_id, 'work_preference': {
                'id': work_preference_id,
                "relocate": True, "authorization": "us citizen",
                "telecommute": False,
                "travel_percentage": randrange(0, 100),
                "hourly_rate": '%.2f' % random.uniform(20, 90),
                "salary": randrange(50000, 300000),
                "employment_type": "full-time employment",
                "third_party": False
            }}
        ]}

    # Data for creating Candidate + CandidateWorkPreference
    else:
        data = reset_all_data_except_param(generate_single_candidate_data(), 'work_preference')

    return data


def candidate_emails(candidate_id=None, email_id=None):
    """
    Sample data for creating Candidate + CandidateEmail
    :rtype  dict
    """
    # Data for adding CandidateEmail to an existing Candidate
    if candidate_id and not email_id:
        data = {'candidates': [{'id': candidate_id, 'emails': [{'label': 'work', 'address': fake.email(),
                                                                'is_default': True}]}]}

    # Data for updating an existing CandidateEmail
    elif candidate_id and email_id:
        data = {'candidates': [{'id': candidate_id, 'emails': [{'id': email_id, 'label': 'primary',
                                                                'address': fake.email()}]}]}

    # Data for creating Candidate + CandidateEmail
    else:
        data = {'candidates': [{'emails': [{'label': 'primary', 'address': fake.email()}]}]}

    return data


def candidate_phones(talent_pool, candidate_id=None, phone_id=None):
    """
    Sample data for creating Candidate + CandidatePhones
    :rtype  dict
    """
    # Data for adding CandidatePhone to an existing Candidate
    if candidate_id and not phone_id:
        data = {'candidates': [{'id': candidate_id, 'phones': [
            {'label': 'home', 'value': sample_phone_number(), 'is_default': True}
        ]}]}

    # Data for updating an existing CandidatePhone
    elif candidate_id and phone_id:
        data = {'candidates': [{'id': candidate_id, 'phones': [{'id': phone_id, 'label': 'home',
                                                                'value': sample_phone_number()}]}]}

    # Data for creating Candidate + CandidatePhone
    else:
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]},
             'phones': [{'value': sample_phone_number(), 'label': 'Home'}]}]}

    return data


def candidate_military_service(talent_pool):
    """
    Sample data for Candidate and CandidateMilitaryService
    :rtype  dict
    """
    data = {'candidates': [
        {'military_services': [
            {'country': 'us', 'branch': fake.military_ship(), 'highest_rank': 'lieutenant',
             'status': 'active', 'highest_grade': '0-1', 'comments': fake.bs(),
             'from_date': '1974-5-25', 'to_date': '1996-12-12'}
        ], 'talent_pool_ids': {'add': [talent_pool.id]}}
    ]}
    return data


def candidate_preferred_locations(talent_pool):
    """
    Sample data for Candidate and CandidatePreferredLocation
    :rtype  dict
    """
    data = {'candidates': [
        {'preferred_locations': [
            {'city': fake.city(), 'state': fake.state(), 'country': fake.country()}
        ], 'talent_pool_ids': {'add': [talent_pool.id]}}
    ]}
    return data


def candidate_skills(talent_pool):
    """
    Sample data for Candidate and CandidateSkill
    :rtype  dict
    """
    data = {'candidates': [
        {'skills': [{'name': 'payroll', 'months_used': 120}],
         'talent_pool_ids': {'add': [talent_pool.id]}}
    ]}
    return data


def candidate_social_network(talent_pool):
    """
    Sample data for Candidate and CandidateSocialNetwork
    :rtype  dict
    """
    data = {'candidates': [
        {'social_networks': [{'profile_url': 'http://www.facebook.com/', 'name': 'facebook'}],
         'talent_pool_ids': {'add': [talent_pool.id]}}
    ]}
    return data


def reset_all_data_except_param(data, field):
    """All required properties of the candidate data will be set to None or []
    except the specified field.
    Please see json_schema.py/candidates_resource_schema_post
    :param data:  comprehensive candidate data
    :param field: name of field that must not be resetted
    :return:      candidate data
    """
    for _field in data['candidates'][0]:
        if _field == field:
            continue

        if _field in ['first_name', 'middle_name', 'last_name', 'work_preference']:
            data['candidates'][0][_field] = None

        if _field in ['addresses', 'phones', 'areas_of_interest', 'custom_fields',
                      'work_experiences', 'preferred_locations', 'military_services', 'skills',
                      'social_networks', 'educations']:
            data['candidates'][0][_field] = []

    return data


def complete_candidate_data_for_posting(data):
    """Helps complete required fields for candidate's data to comply with
    json_schema/candidates_resource_schema_post
    :param data: incomplete candidate data, e.g. {'candidates': [{'first_name': 'joe'}]}
    :return: comprehensive candidate data structure
    """
    template = {'candidates': [
        {
            'emails': [{'label': None, 'address': fake.safe_email(), 'is_default': None}],
            'first_name': None, 'middle_name': None, 'last_name': None, 'addresses': [],
            'social_networks': [], 'skills': [], 'work_experiences': [], 'work_preference': None,
            'educations': [], 'custom_fields': [], 'preferred_locations': [], 'military_services': [],
            'areas_of_interest': [], 'phones': []
        }
    ]}

    data_field = data['candidates'][0].keys()[0]
    for _field in template['candidates'][0]:
        if _field == data_field:
            template['candidates'][0][_field] = data['candidates'][0][data_field]

    return template
