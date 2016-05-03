"""
This module entails candidate sample data functions for testing
"""
# Standard libraries
import random
from random import randrange

# Third party libraries
import phonenumbers
from boltons.iterutils import remap

from candidate_service.common.utils.handy_functions import sample_phone_number

# Faker
from faker import Faker

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
                        'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country_code(),
                        'is_default': True, 'po_box': None, 'subdivision_code': 'US-CA'
                    },
                    {
                        'address_line_1': fake.street_address(), 'city': fake.city(),
                        'state': fake.state(), 'zip_code': fake.postcode(), 'country': fake.country_code(),
                        'is_default': False, 'po_box': '', 'subdivision_code': 'US-CA'
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
                        'subdivision_code': 'US-CA',
                        'state': fake.state(), 'start_month': 11, 'start_year': 2005, 'is_current': True,
                        'end_month': 10, 'end_year': 2007, 'country': fake.country_code(), 'bullets': [
                        {'description': fake.bs()}, {'description': fake.bs()}
                    ]
                    },
                    {
                        'organization': fake.company(), 'position': fake.job(), 'city': fake.city(),
                        'subdivision_code': 'US-CA',
                        'state': fake.state(), 'start_month': 1, 'start_year': 2008, 'is_current': None,
                        'end_month': 5, 'end_year': 2012, 'country': fake.country_code(), 'bullets': [
                        {'description': fake.bs()}, {'description': fake.bs()}
                    ]
                    }
                ],
                'educations': [
                    {
                        'school_name': 'SJSU', 'city': 'San Jose', 'state': 'CA', 'country': 'USA',
                        'subdivision_code': 'US-CA',
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
                        'subdivision_code': 'US-CA',
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
                    {
                        'city': fake.city(), 'state': fake.state(), 'country': fake.country_code(),
                        'subdivision_code': 'US-CA'
                    },
                    {
                        'city': fake.city(), 'state': fake.state(), 'country': fake.country_code(),
                        'subdivision_code': 'US-CA'
                    }
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
                'talent_pool_ids': {'add': talent_pool_ids},
                'resume_url': fake.url()
            }
        ]
    }
    return data


class GenerateCandidateData(object):
    @staticmethod
    def addresses(talent_pool_ids=None, candidate_id=None, address_id=None, is_default=False):
        """
        :type talent_pool_ids:  list[int]
        :param talent_pool_ids is required for creating candidate, but not for updating
        :type candidate_id: int | long
        :rtype:  dict[list]
        """
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids}, 'addresses':
                [
                    {
                        'id': address_id, 'address_line_1': fake.street_address(), 'city': fake.city(),
                        'subdivision_code': 'US-CA', 'zip_code': fake.zipcode(),
                        'country_code': fake.country_code(), 'is_default': is_default
                    }
                ]
            }
        ]}
        # Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def areas_of_interest(domain_aoi, talent_pool_ids=None, candidate_id=None):
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids},
                'areas_of_interest': [{'area_of_interest_id': area_of_interest.id} for area_of_interest in domain_aoi]
            }
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def emails(talent_pool_ids=None, candidate_id=None, email_id=None):
        """
        :type talent_pool_ids:  list[int]
        :rtype:  dict[list]
        """
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids},
                'emails': [
                    {
                        'id': email_id, 'label': 'primary', 'address': fake.safe_email()
                    }
                ]
            }
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def phones(talent_pool_ids=None, candidate_id=None, phone_id=None, internationalize=False):
        """
        :type talent_pool_ids:  list[int]
        :param internationalize:  If True, the phone number value will be internationalized, e.g. +14085067789
        :rtype:  dict[list]
        """
        # Generate phone number
        value = generate_international_phone_number(fake.boolean()) if internationalize else sample_phone_number()
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids},
                'phones': [
                    {
                        'id': phone_id, 'label': 'Work', 'value': value, 'is_default': False
                    }
                ]
            }
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def educations(talent_pool_ids=None, candidate_id=None, education_id=None, degree_id=None, bullet_id=None):
        """
        :type talent_pool_ids:  list[int]
        :rtype:  dict[list]
        """
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids}, 'educations': [
                {
                    'id': education_id,
                    'school_name': 'westvalley', 'school_type': 'college', 'city': fake.city(),
                    'subdivision_code': 'US-CA', 'state': fake.state(),
                    'country_code': fake.country_code(), 'is_current': fake.boolean(),
                    'degrees': [
                        {
                            'id': degree_id, 'type': 'bs', 'title': 'engineer', 'start_year': 2002, 'start_month': 11,
                            'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                            {
                                'id': bullet_id,
                                'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                            }]
                        }
                    ]
                }
            ]}
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def military_services(talent_pool_ids=None, candidate_id=None, military_experience_id=None):
        """
        :type talent_pool_ids:  list[int]
        :rtype:  dict[list]
        """
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids}, 'military_services': [
                {
                    'id': military_experience_id, 'country_code': fake.country_code(),
                    'branch': fake.military_ship(), 'highest_rank': 'lieutenant', 'status': 'active',
                    'highest_grade': '0-1', 'comments': fake.bs(), 'from_date': '1974-5-25', 'to_date': '1996-12-12'
                }
            ]}
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def work_experiences(talent_pool_ids=None, candidate_id=None, experience_id=None, bullet_id=None):
        """
        :type talent_pool_ids:  list[int]
        :rtype:  dict[list]
        """
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids}, 'work_experiences': [
                {
                    'id': experience_id, 'organization': fake.company(), 'position': fake.job(),
                    'city': fake.city(), 'state': fake.state(), 'country_code': fake.country_code(),
                    'start_year': 2008, 'end_year': 2012, 'start_month': 10, 'end_month': 2,
                    'is_current': True, 'subdivision_code': 'US-CA', 'bullets':
                    [
                        {'id': bullet_id, 'description': fake.bs()}
                    ]
                }
            ]}
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def preferred_locations(talent_pool_ids=None, candidate_id=None, preferred_location_id=None):
        """
        :type talent_pool_ids:  list[int]
        :rtype:  dict[list]
        """
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids}, 'preferred_locations': [
                {
                    'id': preferred_location_id, 'city': fake.city(), 'state': fake.state(),
                    'country_code': fake.country_code(), 'subdivision_code': 'US-CA'
                }
            ]}
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
        return data

    @staticmethod
    def work_preference(talent_pool_ids=None, candidate_id=None, preference_id=None):
        data = {'candidates': [
            {
                'id': candidate_id, 'talent_pool_ids': {'add': talent_pool_ids}, 'work_preference':
                {
                    'id': preference_id, "relocate": False, "authorization": "US Citizen", "telecommute": True,
                    "travel_percentage": randrange(0, 100), "hourly_rate": float('%.2f' % random.uniform(20, 90)),
                    "salary": randrange(50000, 300000), "employment_type": "full-time employment",
                    "security_clearance": None, "third_party": False
                }
            }
        ]}
        # Recursively Remove keys with None values
        data = remap(data, lambda p, k, v: v is not None)
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


def candidate_phones(talent_pool, candidate_id=None, phone_id=None, internationalize=False):
    """
    Sample data for creating Candidate + CandidatePhones
    :param internationalize:  If True, the phone number value will be internationalized, e.g. +14085067789
    :rtype  dict
    """
    # Generate phone number
    value = generate_international_phone_number(fake.boolean()) if internationalize else sample_phone_number()

    # Data for adding CandidatePhone to an existing Candidate
    if candidate_id and not phone_id:
        data = {'candidates': [{'id': candidate_id, 'phones': [{'label': 'home', 'value': value, 'is_default': True}]}]}

    # Data for updating an existing CandidatePhone
    elif candidate_id and phone_id:
        data = {'candidates': [{'id': candidate_id, 'phones': [{'id': phone_id, 'label': 'home', 'value': value}]}]}

    # Data for creating Candidate + CandidatePhone
    else:
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'phones': [{'value': value, 'label': 'Home'}]}]}

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
            {'city': fake.city(), 'state': fake.state(), 'country': fake.country_code()}
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


def generate_international_phone_number(extension=False):
    """
    Function will generate a valid international phone number
    :param extension:  If True, phone number will have an extension
    :rtype:  str
    """
    phone_number = '{}'.format(random.randint(1, 9))  # phone number must start with a non-zero value
    while len(phone_number) < 10:  # phone number must have 10 digits
        phone_number += str(random.randint(0, 9))

    # Add country code to the beginning of the phone number
    phone_number = '+' + str(phonenumbers.country_code_for_valid_region(region_code=fake.country_code())) + phone_number

    # Generate and append random extension to phone number
    if extension:
        ext = ''.join(map(str, (random.randrange(9) for _ in range(random.randint(2, 3)))))
        phone_number += ('x' + ext)
    return phone_number
