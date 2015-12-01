"""
Helper functions related to retrieving, creating, updating, and deleting candidates
"""
# Standard libraries
import datetime
import dateutil.parser
import simplejson as json
from datetime import date

# Database connection and logger
from candidate_service.common.models.db import db
from candidate_service.candidate_app import logger

# Models
from candidate_service.common.models.candidate import (
    Candidate, CandidateEmail, CandidatePhone,
    CandidateWorkPreference, CandidatePreferredLocation, CandidateAddress,
    CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField,
    CandidateSocialNetwork, SocialNetwork, CandidateEducationDegreeBullet,
    CandidateExperienceBullet, ClassificationType
)
from candidate_service.common.models.candidate import EmailLabel
from candidate_service.common.models.candidate import PhoneLabel
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.email_marketing import (EmailCampaign, EmailCampaignSend)
from candidate_service.common.models.misc import (Country, AreaOfInterest, CustomField)
from candidate_service.common.models.user import User

# Error handling
from candidate_service.common.error_handling import InvalidUsage

# Validations
from candidate_service.common.utils.validators import (sanitize_zip_code, is_number)

# Common utilities
from candidate_service.common.utils.common_functions import get_coordinates

##################################################
# Helper Functions For Retrieving Candidate Info #
##################################################
def fetch_candidate_info(candidate_id, fields=None):
    """
    Fetch Candidate and candidate related objects via Candidate's id
    :type       candidate_id: int
    :type       fields: None | str

    :return:    Candidate dict
    :rtype:     dict[str, T]
    """
    assert isinstance(candidate_id, (int, long))
    candidate = db.session.query(Candidate).get(candidate_id)

    if not candidate:
        logger.error('Candidate not found, candidate_id: %s', candidate_id)
        return None

    get_all_fields = fields is None  # if fields is None, then get ALL the fields

    full_name = None
    if get_all_fields or 'full_name' in fields:
        first_name = candidate.first_name or ''
        last_name = candidate.last_name or ''
        full_name = (first_name.capitalize() + ' ' + last_name.capitalize()).strip()

    created_at_datetime = None
    if get_all_fields or 'created_at_datetime' in fields:
        created_at_datetime = str(candidate.added_time)

    emails = None
    if get_all_fields or 'emails' in fields:
        emails = candidate_emails(candidate=candidate)

    phones = None
    if get_all_fields or 'phones' in fields:
        phones = candidate_phones(candidate=candidate)

    addresses = None
    if get_all_fields or 'addresses' in fields:
        addresses = candidate_addresses(candidate_id=candidate_id)

    work_experiences = None
    if get_all_fields or 'work_experiences' in fields:
        work_experiences = candidate_experiences(candidate_id=candidate_id)

    work_preference = None
    if get_all_fields or 'work_preferences' in fields:
        work_preference = candidate_work_preference(candidate=candidate)

    preferred_locations = None
    if get_all_fields or 'preferred_locations' in fields:
        preferred_locations = candidate_preferred_locations(candidate=candidate)

    educations = None
    if get_all_fields or 'educations' in fields:
        educations = candidate_educations(candidate=candidate)

    skills = None
    if get_all_fields or 'skills' in fields:
        skills = candidate_skills(candidate_id=candidate_id)

    areas_of_interest = None
    if get_all_fields or 'areas_of_interest' in fields:
        areas_of_interest = candidate_areas_of_interest(candidate_id=candidate_id)

    military_services = None
    if get_all_fields or 'military_services' in fields:
        military_services = candidate_military_services(candidate_id=candidate_id)

    custom_fields = None
    if get_all_fields or 'custom_fields' in fields:
        custom_fields = candidate_custom_fields(candidate=candidate)

    social_networks = None
    if get_all_fields or 'social_networks' in fields:
        social_networks = candidate_social_networks(candidate=candidate)

    history = None
    if get_all_fields or 'contact_history' in fields:
        history = candidate_contact_history(candidate=candidate)

    openweb_id = None
    if get_all_fields or 'openweb_id' in fields:
        openweb_id = candidate.dice_social_profile_id

    dice_profile_id = None
    if get_all_fields or 'dice_profile_id' in fields:
        dice_profile_id = candidate.dice_profile_id

    return_dict = {
        'id': candidate_id,
        'full_name': full_name,
        'created_at_datetime': created_at_datetime,
        'emails': emails,
        'phones': phones,
        'addresses': addresses,
        'work_experiences': work_experiences,
        'work_preference': work_preference,
        'preferred_locations': preferred_locations,
        'educations': educations,
        'skills': skills,
        'areas_of_interest': areas_of_interest,
        'military_services': military_services,
        'custom_fields': custom_fields,
        'social_networks': social_networks,
        'contact_history': history,
        'openweb_id': openweb_id,
        'dice_profile_id': dice_profile_id
    }

    # Remove keys with None values
    return_dict = dict((k, v) for k, v in return_dict.iteritems() if v is not None)
    return return_dict


def candidate_emails(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    emails = candidate.candidate_emails
    return [{'id': email.id,
             'label': email.email_label.description,
             'address': email.address,
             'is_default': email.is_default
             } for email in emails]


def candidate_phones(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    phones = candidate.candidate_phones
    return [{'id': phone.id,
             'label': phone.phone_label.description,
             'value': phone.value,
             'extension': phone.extension,
             'is_default': phone.is_default
             } for phone in phones]


def candidate_addresses(candidate_id):
    """
    :type candidate_id:     int
    :rtype                  [dict]
    """
    # Default CandidateAddress must be returned first
    addresses = db.session.query(CandidateAddress).filter_by(candidate_id=candidate_id).\
        order_by(CandidateAddress.is_default.desc())
    return [{'id': address.id,
             'address_line_1': address.address_line_1,
             'address_line_2': address.address_line_2,
             'city': address.city,
             'state': address.state,
             'zip_code': address.zip_code,
             'po_box': address.po_box,
             'country': Country.country_name_from_country_id(country_id=address.country_id),
             'latitude': address.coordinates and address.coordinates.split(',')[0],
             'longitude': address.coordinates and address.coordinates.split(',')[1],
             'is_default': address.is_default
             } for address in addresses]


def candidate_experiences(candidate_id):
    """
    :type candidate_id:     int
    :rtype                  [dict]
    """
    # Query CandidateExperience from db in descending order based on start_date & is_current
    experiences = db.session.query(CandidateExperience).filter_by(candidate_id=candidate_id).\
        order_by(CandidateExperience.is_current.desc(),
                 CandidateExperience.start_year.desc(),
                 CandidateExperience.start_month.desc())
    return [{'id': experience.id,
             'company': experience.organization,
             'position': experience.position,
             'start_date': date_of_employment(year=experience.start_year, month=experience.start_month or 1),
             'end_date': date_of_employment(year=experience.end_year, month=experience.end_month or 1),
             'city': experience.city,
             'state': experience.state,
             'country': Country.country_name_from_country_id(country_id=experience.country_id),
             'is_current': experience.is_current,
             'experience_bullets': _candidate_experience_bullets(experience=experience),
             } for experience in experiences]


def _candidate_experience_bullets(experience):
    """
    :type experience:   CandidateExperience
    :rtype              [dict]
    """
    experience_bullets = experience.candidate_experience_bullets
    return [{'id': experience_bullet.id,
             'description': experience_bullet.description,
             'added_time': str(experience_bullet.added_time)
             } for experience_bullet in experience_bullets]


def candidate_work_preference(candidate):
    """
    :type candidate:    Candidate
    :rtype              dict
    """
    assert isinstance(candidate, Candidate)
    work_preference = candidate.candidate_work_preferences
    return {'id': work_preference[0].id,
            'authorization': work_preference[0].authorization,
            'employment_type': work_preference[0].tax_terms,
            'security_clearance': work_preference[0].bool_security_clearance,
            'relocate': work_preference[0].bool_relocate,
            'telecommute': work_preference[0].bool_telecommute,
            'hourly_rate': work_preference[0].hourly_rate,
            'salary': work_preference[0].salary,
            'tax_terms': work_preference[0].tax_terms,
            'travel_percentage': work_preference[0].travel_percentage,
            'third_party': work_preference[0].bool_third_party
            } if work_preference else dict()


def candidate_preferred_locations(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    preferred_locations = candidate.candidate_preferred_locations
    return [{'id': preferred_location.id,
             'address': preferred_location.address,
             'city': preferred_location.city,
             'state': preferred_location.region,
             'country': Country.country_name_from_country_id(country_id=preferred_location.country_id)
             } for preferred_location in preferred_locations]


def candidate_educations(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    educations = candidate.candidate_educations
    return [{'id': education.id,
             'school_name': education.school_name,
             'school_type': education.school_type,
             'is_current': education.is_current,
             'degrees': _candidate_degrees(education=education),
             'city': education.city,
             'state': education.state,
             'country': Country.country_name_from_country_id(country_id=education.country_id),
             'added_time': str(education.added_time)
             } for education in educations]


def _candidate_degrees(education):
    """
    :type education:    CandidateEducation
    :rtype              [dict]
    """
    degrees = education.candidate_education_degrees
    return [{'id': degree.id,
             'type': degree.degree_type,
             'title': degree.degree_title,
             'start_year': str(degree.start_year) if degree.start_year else None,
             'start_month': str(degree.start_month) if degree.start_month else None,
             'end_year': str(degree.end_year) if degree.start_year else None,
             'end_month': str(degree.end_month) if degree.start_month else None,
             'gpa': json.dumps(degree.gpa_num, use_decimal=True),
             'start_date': degree.start_time.date().isoformat() if degree.start_time else None,
             'end_date': degree.end_time.date().isoformat() if degree.end_time else None,
             'degree_bullets': _candidate_degree_bullets(degree=degree),
             } for degree in degrees]


def _candidate_degree_bullets(degree):
    """
    :type degree:  CandidateEducationDegree
    :rtype          [dict]
    """
    degree_bullets = degree.candidate_education_degree_bullets
    return [{'id': degree_bullet.id,
             'major': degree_bullet.concentration_type,
             'comments': degree_bullet.comments,
             'added_time': str(degree_bullet.added_time)
             } for degree_bullet in degree_bullets]


def candidate_skills(candidate_id):
    """
    :type candidate_id: int
    :rtype              [dict]
    """
    # Query CandidateSkill in descending order based on last_used
    skills = db.session.query(CandidateSkill).filter_by(candidate_id=candidate_id).\
        order_by(CandidateSkill.last_used.desc())
    return [{'id': skill.id,
             'name': skill.description,
             'months_used': skill.total_months,
             'last_used_date': skill.last_used.isoformat() if skill.last_used else None,
             'added_time': str(skill.added_time)
             } for skill in skills]


def candidate_areas_of_interest(candidate_id):
    """
    :type candidate_id: int
    :rtype              [dict]
    """
    areas_of_interest = db.session.query(CandidateAreaOfInterest).filter_by(candidate_id=candidate_id)
    return [{'id': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).id,
             'name': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).name
             } for interest in areas_of_interest]


def candidate_military_services(candidate_id):
    """
    :type candidate_id:  int
    :rtype              [dict]
    """
    military_experiences = db.session.query(CandidateMilitaryService).\
        filter_by(candidate_id=candidate_id).order_by(CandidateMilitaryService.to_date.desc())
    # military_experiences = candidate.candidate_military_services
    return [{'id': military_info.id,
             'branch': military_info.branch,
             'service_status': military_info.service_status,
             'highest_grade': military_info.highest_grade,
             'highest_rank': military_info.highest_rank,
             'start_date': str(military_info.from_date),
             'end_date': str(military_info.to_date),
             'country': Country.country_name_from_country_id(country_id=military_info.country_id),
             'comments': military_info.comments
             } for military_info in military_experiences]


def candidate_custom_fields(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    can_custom_fields = []
    custom_fields = candidate.candidate_custom_fields
    return [{'id': custom_field.custom_field_id,
             'value': custom_field.value,
             'created_at_datetime': custom_field.added_time.isoformat()
             } for custom_field in custom_fields]


def candidate_social_networks(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    social_networks = candidate.candidate_social_networks
    return [{'id': soc_net.id,
             'name': soc_net.social_network.name,
             'profile_url': soc_net.social_profile_url
             } for soc_net in social_networks]


class ContactHistoryEvent:
    def __init__(self):
        pass

    CREATED_AT = 'created_at'
    EMAIL_SEND = 'email_send'
    EMAIL_OPEN = 'email_open'  # Todo: Implement opens and clicks into timeline
    EMAIL_CLICK = 'email_click'


def candidate_contact_history(candidate):
    """
    :type candidate:    Candidate
    :rtype              dict
    """
    timeline = []

    # Campaign sends & campaigns
    email_campaign_sends = candidate.email_campaign_sends
    for email_campaign_send in email_campaign_sends:
        if not email_campaign_sends.email_campaign_id:
            logger.error("contact_history: email_campaign_send has no email_campaign_id: %s", email_campaign_send.id)
            continue
        email_campaign = db.session.query(EmailCampaign).get(email_campaign_send.email_campaign_id)
        timeline.insert(0, dict(event_datetime=email_campaign_send.sentTime,
                                event_type=ContactHistoryEvent.EMAIL_SEND,
                                campaign_name=email_campaign.name))

    # Sort events by datetime and convert all datetimes to isoformat
    timeline = sorted(timeline, key=lambda entry: entry['event_datetime'], reverse=True)
    for event in timeline:
        event['event_datetime'] = event['event_datetime'].isoformat()

    return dict(timeline=timeline)


def date_of_employment(year, month, day=1):
    # Stringify datetime object to ensure it will be JSON serializable
    return str(date(year, month, day)) if year else None


def get_candidate_id_from_candidate_email(candidate_email):
    """
    :type candidate_email:  CandidateEmail
    :rtype                  int
    """
    candidate_email_row = db.session.query(CandidateEmail).filter_by(address=candidate_email).first()
    if not candidate_email_row:
        logger.info('get_candidate_id_from_candidate_email: candidate email not recognized: %s',
                    candidate_email)
        return None

    return candidate_email_row.candidate_id


# TODO: move function to Email Marketing Service
def retrieve_email_campaign_send(email_campaign, candidate_id):
    """
    :type email_campaign:   EmailCampaign
    :type candidate_id:     int
    :rtype:                 list
    """
    email_campaign_send_rows = db.session.query(EmailCampaignSend). \
        filter_by(EmailCampaignSend.email_campaign_id == email_campaign.id,
                  EmailCampaignSend.candidate_id == candidate_id)

    return [{'candidate_id': email_campaign_send_row.candidate_id,
             'sent_time': email_campaign_send_row.sent_time
             } for email_campaign_send_row in email_campaign_send_rows]


###########################################
# Helper Functions For Creating Candidate #
###########################################
def create_or_update_candidate_from_params(
        user_id,
        is_creating=False,
        is_updating=False,
        candidate_id=None,
        first_name=None,
        last_name=None,
        middle_name=None,
        formatted_name=None,
        status_id=None,
        emails=None,
        phones=None,
        addresses=None,
        educations=None,
        military_services=None,
        areas_of_interest=None,
        custom_fields=None,
        social_networks=None,
        work_experiences=None,
        work_preference=None,
        preferred_locations=None,
        skills=None,
        dice_social_profile_id=None,
        dice_profile_id=None,
        added_time=None,
        source_id=None,
        objective=None,
        summary=None
):
    """
    Function will parse each parameter and:
        I. Creates a Candidate if posting is True
           A 400 will be returned if candidate_id is found
        Or
        II. Updates a Candidate if patching is True and candidate_id is provided/found
            Note: All Candidate fields (see objects mentioned below) require an ID
            for updating, otherwise a new field will be created to the pre-existing
            candidate.

    If all parameters are provided, function will also create or update:
        CandidateAddress, CandidateAreaOfInterest, CandidateCustomField,
        CandidateEducation, CandidateEducationDegree, CandidateEducationDegreeBullet,
        CandidateWorkPreference, CandidateEmail, CandidatePhone,
        CandidateMilitaryService, CandidatePreferredLocation,
        CandidateSkill, CandidateSocialNetwork

    :type user_id:                  int
    :type is_creating:              bool
    :type is_updating:              bool
    :type candidate_id:             int
    :type first_name:               str
    :type last_name:                str
    :type middle_name:              str
    :type formatted_name:           str
    :type status_id:                int
    :type emails:                   list
    :type phones:                   list
    :type addresses:                list
    :type educations:               list
    :type military_services:        list
    :type areas_of_interest:        list
    :type custom_fields:            list
    :type social_networks:          list
    :type work_experiences:         list
    :type work_preference:          dict
    :type preferred_locations:      list
    :type skills:                   list
    :type dice_social_profile_id:   int
    :type dice_profile_id:          int
    :type added_time:               date
    :type domain_can_read:          bool
    :type domain_can_write:         bool
    :type source_id:                int
    :type objective:                str
    :type summary:                  str
    :return:                        dict(candidate_id=candidate_id)
    """
    # Format inputs
    added_time = added_time or datetime.datetime.now()
    status_id = status_id or 1
    is_update = False

    # Figure out first_name, last_name, middle_name, and formatted_name from inputs
    if first_name or last_name or middle_name or formatted_name:
        if (first_name or last_name) and not formatted_name:
            # If first_name and last_name given but not formatted_name, guess it
            formatted_name = get_fullname_from_name_fields(first_name, middle_name, last_name)
        elif formatted_name and (not first_name or not last_name):
            # Otherwise, guess formatted_name from the other fields
            first_name, middle_name, last_name = get_name_fields_from_name(formatted_name)

    # Get domain ID
    domain_id = domain_id_from_user_id(user_id=user_id)


    # If candidate_id is not provided, Check if candidate exists
    if not candidate_id:
        candidate_id = does_candidate_id_exist(dice_social_profile_id, dice_profile_id, domain_id, emails)

    # Raise an error if creation is requested and candidate_id is provided/found
    if candidate_id and is_creating:
        raise InvalidUsage(error_message="Candidate already exists, creation failed.")

    # Update if an update is requested and candidate_id is provided/found
    elif candidate_id and is_updating:
        is_update = True

    # Update is not possible without candidate ID
    elif not candidate_id and is_updating:
        raise InvalidUsage(error_message="Candidate ID is required for updating.")

    if is_update:  # Update Candidate
        candidate_id = _update_candidate(first_name, middle_name, last_name,
                                         formatted_name, objective, summary,
                                         candidate_id)
    else:  # Add Candidate
        candidate_id = _add_candidate(first_name, middle_name, last_name,
                                      formatted_name, added_time, status_id,
                                      user_id, dice_profile_id, dice_social_profile_id,
                                      source_id, objective, summary)

    # Add or update Candidate's address(es)
    if addresses:
        _add_or_update_candidate_addresses(candidate_id, addresses)

    # Add or update Candidate's areas_of_interest
    if areas_of_interest:
        _add_or_update_candidate_areas_of_interest(candidate_id, areas_of_interest)

    # Add or update Candidate's custom_field(s)
    if custom_fields:
        _add_or_update_candidate_custom_field_ids(candidate_id, custom_fields, added_time)

    # Add or update Candidate's education(s)
    if educations:
        _add_or_update_educations(candidate_id, educations, added_time)

    # Add or update Candidate's work experience(s)
    if work_experiences:
        _add_or_update_work_experiences(candidate_id, work_experiences, added_time)

    # Add or update Candidate's work preference(s)
    if work_preference:
        _add_or_update_work_preference(candidate_id, work_preference)

    # Add or update Candidate's email(s)
    if emails:
        _add_or_update_emails(candidate_id, emails)

    # Add or update Candidate's phone(s)
    if phones:
        _add_or_update_phones(candidate_id, phones)

    # Add or update Candidate's military service(s)
    if military_services:
        _add_or_update_military_services(candidate_id, military_services)

    # Add or update Candidate's preferred location(s)
    if preferred_locations:
        _add_or_update_preferred_locations(candidate_id, preferred_locations)

    # Add or update Candidate's skill(s)
    if skills:
        _add_or_update_skills(candidate_id, skills, added_time)

    # Add or update Candidate's social_network(s)
    if social_networks:
        _add_or_update_social_networks(candidate_id, social_networks)

    # Commit to database after all insertions/updates are executed successfully
    db.session.commit()
    return dict(candidate_id=candidate_id)


def get_fullname_from_name_fields(first_name, middle_name, last_name):
    """
    Function will concatenate names if any, otherwise will return empty string
    :rtype: str
    """
    full_name = ''
    if first_name:
        full_name = '%s ' % first_name
    if middle_name:
        full_name = '%s%s ' % (full_name, middle_name)
    if last_name:
        full_name = '%s%s' % (full_name, last_name)

    return full_name


def get_name_fields_from_name(formatted_name):
    names = formatted_name.split(' ') if formatted_name else []
    first_name, middle_name, last_name = '', '', ''
    if len(names) == 1:
        last_name = names[0]
    elif len(names) > 1:
        first_name, last_name = names[0], names[-1]
        # middle_name is everything between first_name and last_name
        # middle_name = '' if only first_name and last_name are provided
        middle_name = ' '.join(names[1:-1])

    return first_name, middle_name, last_name


# Todo: move function to user_service/module
def domain_id_from_user_id(user_id):
    """
    Function will return the domain ID of the user if found, else None
    :type   user_id:  int
    :return domain ID
    """
    assert is_number(user_id)
    user = db.session.query(User).get(user_id)
    if not user:
        logger.error('domain_id_from_user_id: Tried to find the domain ID of the user: %s',
                     user_id)
        return None
    if not user.domain_id:
        logger.error('domain_id_from_user_id: user.domain_id was None!', user_id)
        return None

    return user.domain_id


def does_candidate_id_exist(dice_social_profile_id, dice_profile_id, domain_id, emails):
    """
    Function will search the db for a candidate with the same parameter(s) as provided
    :return candidate_id if found, otherwise None
    """
    candidate = None
    # Check for existing dice_social_profile_id and dice_profile_id
    if dice_social_profile_id:
        candidate = db.session.query(Candidate).join(User).filter(
            Candidate.dice_social_profile_id == dice_social_profile_id,
            User.domain_id == domain_id
        ).first()

    elif dice_profile_id:
        candidate = db.session.query(Candidate).join(User).filter(
            Candidate.dice_profile_id == dice_profile_id,
            User.domain_id == domain_id
        ).first()

    # If candidate is found, return its ID
    if candidate:
        return candidate.id

    # If candidate still not found, check for existing email address, if specified
    if emails:
        for email in emails:
            email_address = email.get('address')
            candidate_email = db.session.query(CandidateEmail).join(Candidate).join(User).filter(
                CandidateEmail.address == email_address, User.domain_id == domain_id
            ).first()
            if candidate_email:
                return candidate_email.candidate_id

    return None


# TODO: convert to classmethod in models
def classification_type_id_from_degree_type(degree_type):
    """
    Function will return classification_type ID of the classification_type that matches
    with degree_type. E.g. degree_type = 'Masters' => classification_type_id: 5
    :return:    classification_type_id or None
    """
    matching_classification_type_id = None
    if degree_type:
        all_classification_types = db.session.query(ClassificationType).all()
        matching_classification_type_id = next((row.id for row in all_classification_types
                                                if row.code.lower() == degree_type.lower()), None)
    return matching_classification_type_id


# TODO: convert to classmethod in models
def social_network_id_from_name(name):
    """
    Function gets social_network ID from social network's name
    e.g. 'Facebook' => 1
    :return: SocialNetwork.id
    """
    matching_social_network = None
    if name:
        all_social_networks = db.session.query(SocialNetwork).all()
        matching_social_network = next((row for row in all_social_networks
                                        if row.name.lower() == name.lower()), None)
    return matching_social_network.id if matching_social_network else None


def _update_candidate(first_name, middle_name, last_name, formatted_name,
                      objective, summary, candidate_id):
    """
    Function will update Candidate
    :return:    Candidate ID
    """
    update_dict = {'first_name': first_name, 'middle_name': middle_name,
                   'last_name': last_name, 'formatted_name': formatted_name,
                   'objective': objective,
                   'summary': summary}

    # Remove None values from update_dict
    update_dict = dict((k, v) for k, v in update_dict.iteritems() if v is not None)

    # Candidate will not be updated if update_dict is empty
    if not any(update_dict):
        return candidate_id

    # Candidate ID must be recognized
    candidate_query = db.session.query(Candidate).filter_by(id=candidate_id)
    if not candidate_query.first():
        error_message = "The Candidate you have requested to update does not exist."
        raise InvalidUsage(error_message=error_message)

    candidate_query.update(update_dict)

    return candidate_id


def _add_candidate(first_name, middle_name, last_name, formatted_name,
                   added_time, candidate_status_id, user_id,
                   dice_profile_id, dice_social_profile_id, source_id,
                   objective, summary):
    """
    Function will create Candidate
    :return:    Candidate ID
    """
    candidate = Candidate(
        first_name=first_name, middle_name=middle_name, last_name=last_name,
        formatted_name=formatted_name, added_time=added_time,
        candidate_status_id=candidate_status_id, user_id=user_id,
        dice_profile_id=dice_profile_id,
        dice_social_profile_id=dice_social_profile_id,
        source_id=source_id, objective=objective, summary=summary,
        is_dirty=0  # TODO: is_dirty cannot be null. This should be removed once the field is successfully removed.
    )
    db.session.add(candidate)
    db.session.flush()

    return candidate.id


def _add_or_update_candidate_addresses(candidate_id, addresses):
    """
    Function will update CandidateAddress or create a new one.

    :type addresses: list[dict[str, T]]
    """
    address_has_default = any([address.get('is_default') for address in addresses])
    for i, address in enumerate(addresses):
        address_dict = address.copy()  # TODO: assert 'address' has no fields that shouldn't be there!
        zip_code = sanitize_zip_code(address.get('zip_code'))
        address_dict.update({
            'country_id': Country.country_id_from_name_or_code(address.get('country')),
            'zip_code': zip_code,
            'coordinates': get_coordinates(zip_code, address.get('city'), address.get('state')),
            'is_default': i == 0 if address_has_default else address.get('is_default'),
            'country': None,
            'candidate_id': candidate_id,
            'resume_id': candidate_id  # TODO: this is to be removed once all tables have been added & migrated
        })

        # No fields in particular are required for address, i.e. dict is empty; just continue
        if not address_dict:
            continue

        # Remove keys that have None values
        address_dict = dict((k, v) for k, v in address_dict.iteritems() if v is not None)

        address_id = address.get('id')
        if address_id:  # Update

            # CandidateAddress must be recognized before updating
            candidate_address_query = db.session.query(CandidateAddress).filter_by(id=address_id)
            if not candidate_address_query.first():
                error_message = "Candidate address you are requesting to update does not exist."
                raise InvalidUsage(error_message=error_message)

            candidate_address_query.update(address_dict)

        else:  # Create if not an update
            db.session.add(CandidateAddress(**address_dict))


def _add_or_update_candidate_areas_of_interest(candidate_id, areas_of_interest):
    """
    Function will update CandidateAreaOfInterest or create a new one.
    """
    for area_of_interest in areas_of_interest:

        aoi_id = area_of_interest['area_of_interest_id']
        # candidate_aoi = CandidateAreaOfInterest.get_areas_of_interest(candidate_id=candidate_id,
        #                                                               area_of_interest_id=aoi_id)

        # if candidate_aoi:  # Update
        #     can_aoi_query = db.session.query(CandidateAreaOfInterest).filter_by(candidate_id=candidate_id)
        #     can_aoi_query.update({'area_of_interest_id': aoi_id})

        # else:  # Add
        db.session.add(CandidateAreaOfInterest(candidate_id=candidate_id, area_of_interest_id=aoi_id))


def _add_or_update_candidate_custom_field_ids(candidate_id, custom_fields, added_time):
    """
    Function will update CandidateCustomField or create a new one.
    """
    for custom_field in custom_fields:
        custom_field_dict = dict(
            value=custom_field.get('value'),
            custom_field_id=custom_field.get('custom_field_id')
        )

        candidate_custom_field_id = custom_field.get('id')
        if candidate_custom_field_id:   # Update

            # Remove keys with None values
            custom_field_dict = dict((k, v) for k, v in custom_field_dict.iteritems() if v is not None)

            # Update CandidateCustomField
            db.session.query(CandidateCustomField).filter_by(candidate_id=candidate_id).update(custom_field_dict)

        else:  # Add
            custom_field_dict.update(dict(added_time=added_time, candidate_id=candidate_id))
            db.session.add(CandidateCustomField(**custom_field_dict))


def _add_or_update_educations(candidate_id, educations, added_time):
    """
    Function will update CandidateEducation, CandidateEducationDegree, and
    CandidateEducationDegreeBullet or create new ones.
    """
    for education in educations:
        # CandidateEducation
        education_dict = dict(
            # candidate_id=candidate_id,
            list_order=education.get('list_order', 1),
            school_name=education.get('school_name'),
            school_type=education.get('school_type'),
            city=education.get('city'),
            state=education.get('state'),
            country_id=Country.country_id_from_name_or_code(education.get('country')),
            is_current=education.get('is_current'),
            added_time=added_time
        )

        education_id = education.get('id')
        if education_id:  # Update

            # Remove keys with None values
            education_dict = dict((k, v) for k, v in education_dict.iteritems() if v is not None)

            # Update CandidateEducation
            db.session.query(CandidateEducation).filter_by(id=education_id).update(education_dict)

            # CandidateEducationDegree
            education_degrees = education.get('degrees', [])
            for education_degree in education_degrees:
                education_degree_dict = dict(
                    list_order=education_degree.get('list_order'),
                    degree_type=education_degree.get('type'),
                    degree_title=education_degree.get('title'),
                    start_year=education_degree.get('start_year'),
                    start_month=education_degree.get('start_month'),
                    end_year=education_degree.get('end_year'),
                    end_month=education_degree.get('end_month'),
                    gpa_num=education_degree.get('gpa'),
                    added_time=added_time,
                    classification_type_id=classification_type_id_from_degree_type(education_degree.get('type')),
                    start_time=education_degree.get('start_time'),
                    end_time=education_degree.get('end_time')
                )

                # Remove keys with None values
                education_degree_dict = dict((k, v) for k, v in education_degree_dict.iteritems() if v is not None)

                education_degree_id = education_degree.get('id')
                if education_degree_id:  # Update CandidateEducationDegree
                    db.session.query(CandidateEducationDegree). \
                        filter_by(candidate_education_id=education_id).update(education_degree_dict)

                    # CandidateEducationDegreeBullet
                    education_degree_bullets = education_degree.get('degree_bullets', [])
                    for education_degree_bullet in education_degree_bullets:
                        education_degree_bullet_dict = dict(
                            concentration_type=education_degree_bullet.get('major'),
                            comments=education_degree_bullet.get('comments')
                        )

                        # Remove keys with None values
                        education_degree_bullet_dict = dict((k, v) for k, v in
                                                            education_degree_bullet_dict.iteritems() if v is not None)

                        education_degree_bullet_id = education_degree_bullet.get('id')
                        if education_degree_bullet_id:  # Update CandidateEducationDegreeBullet
                            db.session.query(CandidateEducationDegreeBullet).\
                                filter_by(candidate_education_degree_id=education_degree_id).\
                                update(education_degree_bullet_dict)
                        else:   # Add CandidateEducationDegreeBullet
                            education_degree_bullet_dict.update(dict(added_time=added_time))
                            db.session.add(CandidateEducationDegreeBullet(**education_degree_bullet_dict))

                else:   # Add CandidateEducationDegree
                    education_degree_dict.update(dict(candidate_education_id=education_id))
                    candidate_education_degree = CandidateEducationDegree(**education_degree_dict)
                    db.session.add(candidate_education_degree)
                    db.session.flush()

                    can_edu_degree_id = candidate_education_degree.id

                    # Add CandidateEducationDegreeBullets
                    education_degree_bullets = education_degree.get('degree_bullets', [])
                    for education_degree_bullet in education_degree_bullets:
                        db.session.add(CandidateEducationDegreeBullet(
                            candidate_education_degree_id=can_edu_degree_id,
                            concentration_type=education_degree_bullet.get('major'),
                            comments=education_degree_bullet.get('comments'),
                            added_time=added_time
                        ))

        else:  # Add
            # CandidateEducation
            education_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id))  # TODO: this is to be removed once all tables have been added & migrated
            candidate_education = CandidateEducation(**education_dict)
            db.session.add(candidate_education)
            db.session.flush()

            education_id = candidate_education.id

            # CandidateEducationDegree
            education_degrees = education.get('degrees')
            for education_degree in education_degrees:

                # Add CandidateEducationDegree
                candidate_education_degree = CandidateEducationDegree(
                    candidate_education_id=education_id,
                    list_order=education_degree.get('list_order'),
                    degree_type=education_degree.get('type'),
                    degree_title=education_degree.get('title'),
                    start_year=education_degree.get('start_year'),
                    start_month=education_degree.get('start_month'),
                    end_year=education_degree.get('end_year'),
                    end_month=education_degree.get('end_month'),
                    gpa_num=education_degree.get('gpa'),
                    added_time=added_time,
                    classification_type_id=classification_type_id_from_degree_type(education_degree.get('type')),
                    start_time=education_degree.get('start_time'),
                    end_time=education_degree.get('end_time')
                )
                db.session.add(candidate_education_degree)
                db.session.flush()

                education_degree_id = candidate_education_degree.id

                # CandidateEducationDegreeBullet
                degree_bullets = education_degree.get('degree_bullets', [])
                for degree_bullet in degree_bullets:

                    # Add CandidateEducationDegreeBullet
                    db.session.add(CandidateEducationDegreeBullet(
                        candidate_education_degree_id=education_degree_id,
                        list_order=degree_bullet.get('list_order'),
                        concentration_type=degree_bullet.get('major'),
                        comments=degree_bullet.get('comments'),
                        added_time=added_time
                    ))


def _add_or_update_work_experiences(candidate_id, work_experiences, added_time):
    """
    Function will update CandidateExperience and CandidateExperienceBullet
    or create new ones.
    """
    for work_experience in work_experiences:
        # CandidateExperience
        experience_dict = dict(
            list_order=work_experience.get('list_order', 1),
            organization=work_experience.get('organization'),
            position=work_experience.get('position'),
            city=work_experience.get('city'),
            state=work_experience.get('state'),
            end_month=work_experience.get('end_month'),
            start_year=work_experience.get('start_year'),
            country_id=Country.country_id_from_name_or_code(work_experience.get('country')),
            start_month=work_experience.get('start_month'),
            end_year=work_experience.get('end_year'),
            is_current=work_experience.get('is_current', 0)
        )

        experience_id = work_experience.get('id')
        if experience_id:  # Update

            # Remove keys with None values
            experience_dict = dict((k, v) for k, v in experience_dict.iteritems() if v is not None)

            # Update CandidateExperience
            db.session.query(CandidateExperience).filter_by(candidate_id=candidate_id).update(experience_dict)

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('experience_bullets', [])
            for experience_bullet in experience_bullets:
                experience_bullet_dict = dict(
                    list_order=experience_bullet.get('list_order'),
                    description=experience_bullet.get('description'),
                    added_time=added_time
                )

                # Remove keys with None values
                experience_bullet_dict = dict((k, v) for k, v in experience_bullet_dict.iteritems() if v is not None)

                experience_bullet_id = experience_bullet.get('id')
                if experience_bullet_id:  # Update
                    db.session.query(CandidateExperienceBullet).\
                        filter_by(candidate_experience_id=experience_id).update(experience_bullet_dict)
                else:  # Add
                    experience_bullet_dict.update(dict(candidate_experience_id=experience_id))
                    db.session.add(CandidateExperienceBullet(**experience_bullet_dict))

        else:  # Add
            experience_dict.update(dict(candidate_id=candidate_id, added_time=added_time, resume_id=candidate_id))
            experience = CandidateExperience(**experience_dict)
            db.session.add(experience)
            db.session.flush()

            experience_id = experience.id

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('experience_bullets', [])
            for experience_bullet in experience_bullets:
                db.session.add(CandidateExperienceBullet(
                    candidate_experience_id=experience_id,
                    list_order=experience_bullet.get('list_order'),
                    description=experience_bullet.get('description'),
                    added_time=added_time
                ))


def _add_or_update_work_preference(candidate_id, work_preference):
    """
    Function will update CandidateWorkPreference or create a new one.
    """
    work_preference_dict = dict(
        relocate=work_preference.get('relocate'),
        authorization=work_preference.get('authorization'),
        telecommute=work_preference.get('telecommute'),
        travel_percentage=work_preference.get('travel_percentage'),
        hourly_rate=work_preference.get('hourly_rate'),
        salary=work_preference.get('salary'),
        tax_terms=work_preference.get('tax_terms')
    )

    # Remove None values from update_dict
    work_preference_dict = dict((k, v) for k, v in work_preference_dict.iteritems() if v is not None)

    work_preference_id = work_preference.get('id')
    if work_preference_id:  # Update
        db.session.query(CandidateWorkPreference).filter_by(candidate_id=candidate_id)\
            .update(work_preference_dict)

    else:  # Add
        # Only 1 CandidateWorkPreference is permitted for each Candidate
        if db.session.query(CandidateWorkPreference).filter_by(candidate_id=candidate_id).first():
            raise InvalidUsage(error_message="Candidate work preference already exists.")

        work_preference_dict.update(dict(candidate_id=candidate_id))
        db.session.add(CandidateWorkPreference(**work_preference_dict))


def _add_or_update_emails(candidate_id, emails):
    """
    Function will update CandidateEmail or create new one(s).
    """
    emails_has_default = any([email.get('is_default') for email in emails])
    for i, email in enumerate(emails):

        # If there's no is_default, the first email should be default
        is_default = email.get('is_default')
        is_default = i == 0 if not emails_has_default else is_default
        email_address = email.get('address')

        email_dict = dict(
            address=email_address,
            email_label_id=EmailLabel.email_label_id_from_email_label(email_label=email.get('label')),
            is_default=is_default
        )

        email_id = email.get('id')
        if email_id:  # Update
            if not email_address:
                raise InvalidUsage(error_message="Email address is required for update.")

            # Remove keys with None values
            email_dict = dict((k, v) for k, v in email_dict.iteritems() if v is not None)

            # Update CandidateEamil
            db.session.query(CandidateEmail).filter_by(id=email_id).update(email_dict)

        else:  # Add
            email_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidateEmail(**email_dict))


def _add_or_update_phones(candidate_id, phones):
    """
    Function will update CandidatePhone or create new one(s).
    """
    # TODO: parse out phone extension. Currently the value + extension are being added to the phone's value in the db
    phone_has_default = any([phone.get('is_default') for phone in phones])
    for i, phone in enumerate(phones):

        # If there's no is_default, the first phone should be default
        is_default = phone.get('is_default')
        is_default = i == 0 if not phone_has_default else is_default

        phone_dict = dict(
            value=phone.get('value'),
            phone_label_id = PhoneLabel.phone_label_id_from_phone_label(phone_label=phone['label']),
            is_default=is_default
        )

        candidate_phone_id = phone.get('id')
        if candidate_phone_id:  # Update

            # Remove keys with None values
            phone_dict = dict((k, v) for k, v in phone_dict.iteritems() if v is not None)

            # Update CandidatePhone
            db.session.query(CandidatePhone).filter_by(candidate_id=candidate_id).update(phone_dict)

        else:  # Add
            phone_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidatePhone(**phone_dict))


def _add_or_update_military_services(candidate_id, military_services):
    """
    Function will update CandidateMilitaryService or create new one(s).
    """
    for military_service in military_services:

        # Convert ISO 8061 date object to datetime object
        from_date, to_date = military_service.get('from_date'), military_service.get('to_date')
        if from_date:
            from_date = dateutil.parser.parse(from_date)
        if to_date:
            to_date = dateutil.parser.parse(to_date)

        military_service_dict = dict(
            country_id=Country.country_id_from_name_or_code(military_service.get('country')),
            service_status=military_service.get('service_status'),
            highest_rank=military_service.get('highest_rank'),
            highest_grade=military_service.get('highest_grade'),
            branch=military_service.get('branch'),
            comments=military_service.get('comments'),
            from_date=from_date,
            to_date=to_date
        )

        military_service_id = military_service.get('id')
        if military_service_id:  # Update

            # Remove keys with None values
            military_service_dict = dict((k, v) for k, v in military_service_dict.iteritems() if v is not None)

            # Update CandidateMilitaryService
            db.session.query(CandidateMilitaryService).filter_by(candidate_id=candidate_id).\
                update(military_service_dict)

        else:  # Add
            military_service_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id))
            db.session.add(CandidateMilitaryService(**military_service_dict))


def _add_or_update_preferred_locations(candidate_id, preferred_locations):
    """
    Function will update CandidatePreferredLocation or create a new one.
    """
    for preferred_location in preferred_locations:

        preferred_location_dict = dict(
            address=preferred_location.get('address'),
            country_id=Country.country_id_from_name_or_code(preferred_location.get('country')),
            city=preferred_location.get('city'),
            region=preferred_location.get('state'),
            zip_code=sanitize_zip_code(preferred_location.get('zip_code'))
        )

        preferred_location_id = preferred_location.get('id')
        if preferred_location_id:  # Update

            # Remove keys with None values
            preferred_location_dict = dict((k, v) for k, v in preferred_location_dict.iteritems() if v is not None)

            # Update CandidatePreferredLocation
            db.session.query(CandidatePreferredLocation).\
                filter_by(candidate_id=candidate_id).update(preferred_location_dict)

        else:  # Add
            preferred_location_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidatePreferredLocation(**preferred_location_dict))


def _add_or_update_skills(candidate_id, skills, added_time):
    """
    Function will update CandidateSkill or create new one(s).
    """
    for skill in skills:

        # Convert ISO 8601 date format to datetime object
        last_used = skill.get('last_used')
        if last_used:
            last_used = dateutil.parser.parse(skill.get('last_used'))

        skills_dict = dict(
            list_order=skill.get('list_order'),
            description=skill.get('name'),
            total_months=skill.get('months_used'),
            last_used=last_used
        )

        skill_id = skill.get('id')
        if skill_id:  # Update

            # Remove keys with None values
            skills_dict = dict((k, v) for k, v in skills_dict.iteritems() if v is not None)

            # Update CandidateSkill
            db.session.query(CandidateSkill).filter_by(candidate_id=candidate_id).update(skills_dict)

        else:  # Add
            skills_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id, added_time=added_time))
            db.session.add(CandidateSkill(**skills_dict))


def _add_or_update_social_networks(candidate_id, social_networks):
    """
    Function will update CandidateSocialNetwork or create new one(s).
    """
    for social_network in social_networks:

        social_network_dict = dict(
            social_network_id=social_network_id_from_name(name=social_network.get('name')),
            social_profile_url=social_network.get('profile_url')
        )

        # Todo: what if url and/or name is not provided?
        social_network_id = social_network.get('id')
        if social_network_id:  # Update
            db.session.query(CandidateSocialNetwork).filter_by(candidate_id=candidate_id).\
                update(social_network_dict)

        else:  # Add
            social_network_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidateSocialNetwork(**social_network_dict))


################################################
# Helper Functions For Deleting Candidate Info #
################################################
def _delete_candidates(candidate_ids, user_id, source_product_id):
    """
    Mark as web_hidden in db, then delete from search & db, then delete all candidate data from S3

    :type candidate_ids: list[int]
    :type user_id: int
    :type source_product_id: int
    :return: Number of deleted candidates
    """
    # Delete candidates from CloudSearch, 100 at a time
    list_offset = 0
    list_segment = candidate_ids[0:100]
    candidates = db.session.query(Candidate).filter(Candidate.id.in_(candidate_ids))

    from activity_service.activities_app.views.api import (TalentActivityManager, create_activity)

    activity_api = TalentActivityManager()

    while list_segment:
        # Add activity for every candidate deleted
        for candidate_id in list_segment:
            candidate = candidates.filter(Candidate.id == candidate_id).first()
            if candidate:
                create_activity(user_id=user_id, type_=activity_api.CANDIDATE_DELETE,
                                source_table='candidate', source_id=candidate_id,
                                params=dict(source_product_id=source_product_id,
                                            formatted_name=candidate.formatted_name))

        # Delete all candidates in segment
        db.session.query(Candidate).filter(Candidate.id.in_(list_segment)).delete(synchronize_session=False)

        # Get next segment
        list_offset += 100
        list_segment = candidate_ids[list_offset:(list_offset + 100)]

    # TODO: Delete files from S3
    # TODO: Delete files from CloudSearch

    db.session.commit()
    return len(candidate_ids)
