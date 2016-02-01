"""
Helper functions for candidate CRUD operations and tracking edits made to the Candidate
"""
# Standard libraries
import datetime
from flask import request
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
from candidate_service.common.models.candidate import EmailLabel, CandidateSubscriptionPreference
from candidate_service.common.models.talent_pools_pipelines import TalentPoolCandidate, TalentPool, TalentPoolGroup
from candidate_service.common.models.candidate_edit import CandidateEdit, CandidateView
from candidate_service.common.models.candidate import PhoneLabel
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.common.models.misc import (Country, AreaOfInterest)
from candidate_service.common.models.user import User

# Error handling
from candidate_service.common.error_handling import (
    InvalidUsage, NotFoundError, UnauthorizedError, ForbiddenError
)
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

# Validations
from candidate_service.common.utils.validators import (sanitize_zip_code, is_number, format_phone_number)

# Common utilities
from candidate_service.common.geo_services.geo_coordinates import get_coordinates

import urlparse

##################################################
# Helper Functions For Retrieving Candidate Info #
##################################################
def fetch_candidate_info(candidate, fields=None):
    """
    Fetch Candidate and candidate related objects via Candidate's id
    :type       candidate: Candidate
    :type       fields: None | str

    :return:    Candidate dict
    :rtype:     dict[str, T]
    """
    assert isinstance(candidate, Candidate)
    candidate_id = candidate.id

    get_all_fields = fields is None  # if fields is None, then get ALL the fields

    full_name = None
    if get_all_fields or 'full_name' in fields:
        full_name = format_candidate_full_name(candidate)

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

    talent_pool_ids = None
    if get_all_fields or 'talent_pool_ids' in fields:
        talent_pool_ids = [talent_pool_candidate.talent_pool_id for talent_pool_candidate in
                           TalentPoolCandidate.query.filter_by(candidate_id=candidate.id).all()]

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
        'dice_profile_id': dice_profile_id,
        'talent_pool_ids': talent_pool_ids
    }

    # Remove keys with None values
    return_dict = dict((k, v) for k, v in return_dict.iteritems() if v is not None)
    return return_dict


def format_candidate_full_name(candidate):
    """
    :type candidate:  Candidate
    :return:
    """
    assert isinstance(candidate, Candidate)
    first_name, middle_name, last_name = candidate.first_name, candidate.middle_name, candidate.last_name
    full_name = ''
    if first_name:
        full_name = '%s ' % first_name
    if middle_name:
        full_name = '%s%s ' % (full_name, middle_name)
    if last_name:
        full_name = '%s%s' % (full_name, last_name)

    return full_name


def candidate_emails(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    emails = candidate.emails
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
    phones = candidate.phones
    return [{'id': phone.id,
             'label': phone.phone_label.description,
             'value': phone.value,
             'extension': phone.extension,
             'is_default': phone.is_default
             } for phone in phones]


def candidate_addresses(candidate_id):
    """
    :type candidate_id:     int|long
    :rtype                  [dict]
    """
    assert isinstance(candidate_id, (int, long))
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
    :type candidate_id:     int|long
    :rtype                  [dict]
    """
    assert isinstance(candidate_id, (int, long))
    # Query CandidateExperience from db in descending order based on start_date & is_current
    experiences = db.session.query(CandidateExperience).filter_by(candidate_id=candidate_id).\
        order_by(CandidateExperience.is_current.desc(),
                 CandidateExperience.start_year.desc(),
                 CandidateExperience.start_month.desc())
    return [{'id': experience.id,
             'organization': experience.organization,
             'position': experience.position,
             'start_date': date_of_employment(year=experience.start_year, month=experience.start_month or 1),
             'end_date': date_of_employment(year=experience.end_year, month=experience.end_month or 1),
             'city': experience.city,
             'state': experience.state,
             'country': Country.country_name_from_country_id(country_id=experience.country_id),
             'is_current': experience.is_current,
             'bullets': _candidate_experience_bullets(experience=experience),
             } for experience in experiences]


def _candidate_experience_bullets(experience):
    """
    :type experience:   CandidateExperience
    :rtype              [dict]
    """
    assert isinstance(experience, CandidateExperience)
    experience_bullets = experience.bullets
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
    work_preference = candidate.work_preferences
    return {'id': work_preference[0].id,
            'authorization': work_preference[0].authorization,
            'employment_type': work_preference[0].tax_terms,
            'security_clearance': work_preference[0].bool_security_clearance,
            'relocate': work_preference[0].bool_relocate,
            'telecommute': work_preference[0].bool_telecommute,
            'hourly_rate': work_preference[0].hourly_rate,
            'salary': work_preference[0].salary,
            'travel_percentage': work_preference[0].travel_percentage,
            'third_party': work_preference[0].bool_third_party
            } if work_preference else dict()


def candidate_preferred_locations(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    preferred_locations = candidate.preferred_locations
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
    educations = candidate.educations
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
    assert isinstance(education, CandidateEducation)
    degrees = education.degrees
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
             'bullets': _candidate_degree_bullets(degree=degree),
             } for degree in degrees]


def _candidate_degree_bullets(degree):
    """
    :type degree:  CandidateEducationDegree
    :rtype          [dict]
    """
    assert isinstance(degree, CandidateEducationDegree)
    degree_bullets = degree.bullets
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
    assert isinstance(candidate_id, (int, long))
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
    assert isinstance(candidate_id, (int, long))
    areas_of_interest = db.session.query(CandidateAreaOfInterest).filter_by(candidate_id=candidate_id)
    return [{'id': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).id,
             'name': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).name
             } for interest in areas_of_interest]


def candidate_military_services(candidate_id):
    """
    :type candidate_id:  int
    :rtype              [dict]
    """
    assert isinstance(candidate_id, (int, long))
    military_experiences = db.session.query(CandidateMilitaryService).\
        filter_by(candidate_id=candidate_id).order_by(CandidateMilitaryService.to_date.desc())
    return [{'id': military_info.id,
             'branch': military_info.branch,
             'status': military_info.service_status,
             'highest_grade': military_info.highest_grade,
             'highest_rank': military_info.highest_rank,
             'from_date': military_info.from_date.strftime('%Y-%m-%d') if military_info.from_date else None,
             'to_date': military_info.to_date.strftime('%Y-%m-%d') if military_info.from_date else None,
             'country': Country.country_name_from_country_id(country_id=military_info.country_id),
             'comments': military_info.comments
             } for military_info in military_experiences]


def candidate_custom_fields(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    custom_fields = db.session.query(CandidateCustomField).filter_by(candidate_id=candidate.id).all()
    return [{'id': custom_field.id,
             'value': custom_field.value,
             'created_at_datetime': custom_field.added_time.isoformat()
             } for custom_field in custom_fields]


def candidate_social_networks(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    social_networks = candidate.social_networks
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
    assert isinstance(candidate, Candidate)
    timeline = []

    # Campaign sends & campaigns
    for email_campaign_send in candidate.email_campaign_sends:
        if not email_campaign_send.email_campaign_id:
            logger.error("contact_history: email_campaign_send has no email_campaign_id: %s", email_campaign_send.id)
            continue
        email_campaign = db.session.query(EmailCampaign).get(email_campaign_send.email_campaign_id)
        timeline.insert(0, dict(event_datetime=email_campaign_send.sent_time,
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


def get_candidate_id_from_email_if_exists_in_domain(user, email):
    """
    Function will get the domain-candidate associated with email and return its ID.
    :type user: User
    :type email: str
    :return Candidate.id or None (if not found)
    """
    email_obj = CandidateEmail.query.join(Candidate).join(User).filter(
            User.domain_id == user.domain_id).filter(CandidateEmail.address == email).first()
    if not email_obj:
        raise NotFoundError(error_message='Candidate email not recognized: {}'.format(email),
                            error_code=custom_error.EMAIL_NOT_FOUND)
    return email_obj.candidate_id


######################################
# Helper Functions For Candidate Edits
######################################
def fetch_candidate_edits(candidate_id):
    """
    :type candidate_id:  int|long
    :rtype:  list[dict]
    """
    all_edits = []
    for can_edit in CandidateEdit.get_by_candidate_id(candidate_id=candidate_id):
        table_and_field_names_tuple = CandidateEdit.get_table_and_field_names_from_id(can_edit.field_id)
        all_edits.append({
            'user_id': can_edit.user_id,
            'table_name': table_and_field_names_tuple[0],
            'field_name': table_and_field_names_tuple[1],
            'old_value': can_edit.old_value,
            'new_value': can_edit.new_value,
            'is_custom_field': can_edit.is_custom_field,
            'edit_type': can_edit.edit_type,
            'edit_datetime': str(can_edit.edit_datetime)
        })
    return all_edits


######################################
# Helper Functions For Candidate Views
######################################
def fetch_candidate_views(candidate_id):
    """
    :return: list of candidate view information
    :rtype:  list[dict]
    """
    assert isinstance(candidate_id, (int, long))
    candidate_views = CandidateView.get_all(candidate_id=candidate_id)
    return [{'id': view.id,
             'candidate_id': view.candidate_id,
             'user_id': view.user_id,
             'view_type': view.view_type,
             'view_datetime': str(view.view_datetime)
             } for view in candidate_views]


def add_candidate_view(user_id, candidate_id, view_datetime=datetime.datetime.now(), view_type=3):
    """
    Once a Candidate has been viewed, this function should be invoked
    and add a record to CandidateView
    :type user_id: int|long
    :type candidate_id: int|long
    """
    db.session.add(CandidateView(
        user_id=user_id,
        candidate_id=candidate_id,
        view_type=view_type,
        view_datetime=view_datetime
    ))
    db.session.commit()


########################################################
# Helper Functions For Candidate Subscription Preference
########################################################
def fetch_candidate_subscription_preference(candidate_id):
    """
    :type candidate_id: int|long
    :rtype:  dict
    """
    assert isinstance(candidate_id, (int, long))
    candidate_subs_pref = CandidateSubscriptionPreference.get_by_candidate_id(candidate_id)
    if not candidate_subs_pref:
        return {}
    return {'id': candidate_subs_pref.id, 'frequency_id': candidate_subs_pref.frequency_id}


def add_or_update_candidate_subs_preference(candidate_id, frequency_id, is_update=False):
    """
    Function adds or updates candidate's subs preference
    :type candidate_id: int|long
    :type frequency_id: int|long
    :type is_update: bool
    """
    assert isinstance(candidate_id, (int, long)) and isinstance(frequency_id, (int, long))
    can_subs_pref_query = CandidateSubscriptionPreference.query.filter_by(candidate_id=candidate_id)
    if is_update:  # Update
        can_subs_pref_query.update(dict(frequency_id=frequency_id))
    else:  # Add
        db.session.add(CandidateSubscriptionPreference(
            candidate_id=candidate_id, frequency_id=frequency_id
        ))
    db.session.commit()


######################################################
# Helper Functions For Creating and Updating Candidate
######################################################
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
        summary=None,
        talent_pool_ids=None
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

    :type user_id:                  int|long
    :type is_creating:              bool
    :type is_updating:              bool
    :type candidate_id:             int
    :type first_name:               basestring
    :type last_name:                basestring
    :type middle_name:              basestring
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
    :type source_id:                int
    :type objective:                basestring
    :type summary:                  basestring
    :type talent_pool_ids:          dict
    :type delete_talent_pools:      bool
    :rtype                          dict
    """
    # Format inputs
    added_time = added_time or datetime.datetime.now()
    status_id = status_id or 1
    edit_time = datetime.datetime.now()  # Timestamp for tracking edits

    # Figure out first_name, last_name, middle_name, and formatted_name from inputs
    if first_name or last_name or middle_name or formatted_name:
        if (first_name or last_name) and not formatted_name:
            # If first_name and last_name given but not formatted_name, guess it
            formatted_name = get_fullname_from_name_fields(first_name, middle_name, last_name)
        elif formatted_name and (not first_name or not last_name):
            # Otherwise, guess formatted_name from the other fields
            first_name, middle_name, last_name = get_name_fields_from_name(formatted_name)

    # Get user's domain ID
    domain_id = domain_id_from_user_id(user_id=user_id)

    # If candidate_id is not provided, Check if candidate exists
    if is_creating:
        candidate_id = get_candidate_id_if_found(dice_social_profile_id, dice_profile_id,
                                                 domain_id, emails)

    # Raise an error if creation is requested and candidate_id is provided/found
    if candidate_id and is_creating:
        raise InvalidUsage(error_message='Candidate already exists, creation failed.',
                           error_code=custom_error.CANDIDATE_ALREADY_EXISTS)

    # Update is not possible without candidate ID
    elif not candidate_id and is_updating:
        raise InvalidUsage(error_message='Candidate ID is required for updating',
                           error_code=custom_error.MISSING_INPUT)

    if is_updating:  # Update Candidate
        candidate_id = _update_candidate(first_name, middle_name, last_name,
                                         formatted_name, objective, summary,
                                         candidate_id, user_id, edit_time)
    else:  # Add Candidate
        candidate_id = _add_candidate(first_name, middle_name, last_name,
                                      formatted_name, added_time, status_id,
                                      user_id, dice_profile_id, dice_social_profile_id,
                                      source_id, objective, summary)

    # Add or update Candidate's talent-pools
    if talent_pool_ids:
        _add_or_update_candidate_talent_pools(candidate_id, talent_pool_ids, is_creating,
                                              is_updating)

    # Add or update Candidate's address(es)
    if addresses:
        _add_or_update_candidate_addresses(candidate_id, addresses, user_id, edit_time)

    # Add or update Candidate's areas_of_interest
    if areas_of_interest:
        _add_or_update_candidate_areas_of_interest(candidate_id, areas_of_interest)

    # Add or update Candidate's custom_field(s)
    if custom_fields:
        _add_or_update_candidate_custom_field_ids(candidate_id, custom_fields, added_time, user_id, edit_time)

    # Add or update Candidate's education(s)
    if educations:
        _add_or_update_educations(candidate_id, educations, added_time, user_id, edit_time)

    # Add or update Candidate's work experience(s)
    if work_experiences:
        _add_or_update_work_experiences(candidate_id, work_experiences, added_time, user_id, edit_time)

    # Add or update Candidate's work preference(s)
    if work_preference:
        _add_or_update_work_preference(candidate_id, work_preference, user_id, edit_time)

    # Add or update Candidate's email(s)
    if emails:
        _add_or_update_emails(candidate_id, emails, user_id, edit_time)

    # Add or update Candidate's phone(s)
    if phones:
        _add_or_update_phones(candidate_id, phones, user_id, edit_time)

    # Add or update Candidate's military service(s)
    if military_services:
        _add_or_update_military_services(candidate_id, military_services, user_id, edit_time)

    # Add or update Candidate's preferred location(s)
    if preferred_locations:
        _add_or_update_preferred_locations(candidate_id, preferred_locations, user_id, edit_time)

    # Add or update Candidate's skill(s)
    if skills:
        _add_or_update_skills(candidate_id, skills, added_time, user_id, edit_time)

    # Add or update Candidate's social_network(s)
    if social_networks:
        _add_or_update_social_networks(candidate_id, social_networks, user_id, edit_time)

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


def get_candidate_id_if_found(dice_social_profile_id, dice_profile_id, domain_id, emails):
    """
    Function will search the db for a candidate with the same parameter(s) as provided
    :type dice_social_profile_id: int|long
    :type dice_profile_id: int|long
    :type domain_id: int|long
    :type emails: list
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


def social_network_name_from_url(url):

    if url:
        parsed_url = urlparse.urlparse(url)
        url = "%s://%s" % (parsed_url.scheme, parsed_url.netloc)
        result = db.session.query(SocialNetwork.name).filter(SocialNetwork.url == url).first()
        if result:
            return result[0]
        else:
            return "Unknown"



def _update_candidate(first_name, middle_name, last_name, formatted_name,
                      objective, summary, candidate_id, user_id, edited_time):
    """
    Function will update Candidate
    :return:    Candidate ID
    """
    update_dict = {'first_name': first_name, 'middle_name': middle_name,
                   'last_name': last_name, 'formatted_name': formatted_name,
                   'objective': objective,
                   'summary': summary}

    # Remove keys with None values
    update_dict = dict((k, v) for k, v in update_dict.iteritems() if v is not None)

    # Candidate will not be updated if update_dict is empty
    if not any(update_dict):
        return candidate_id

    # Candidate ID must be recognized
    candidate_query = db.session.query(Candidate).filter_by(id=candidate_id)
    if not candidate_query.first():
        raise NotFoundError('Candidate not found', custom_error.CANDIDATE_NOT_FOUND)

    # Track all edits
    _track_candidate_edits(update_dict, candidate_query.first(), user_id, edited_time)

    # Update
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


def _add_or_update_candidate_addresses(candidate_id, addresses, user_id, edited_time):
    """
    Function will update CandidateAddress or create a new one.
    :type addresses: list[dict[str, T]]
    """
    # If any of addresses is_default, set candidate's addresses' is_default to False
    address_has_default = any([address.get('is_default') for address in addresses])
    if address_has_default:
        CandidateAddress.set_is_default_to_false(candidate_id=candidate_id)

    for i, address in enumerate(addresses):
        address_dict = address.copy()
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
                raise InvalidUsage(error_message='Candidate address not found',
                                   error_code=custom_error.ADDRESS_NOT_FOUND)

            # CandidateAddress must belong to Candidate
            if candidate_address_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message="Unauthorized candidate address",
                                     error_code=custom_error.ADDRESS_FORBIDDEN)

            # Track all edits
            _track_candidate_address_edits(address_dict, candidate_id, candidate_address_query.first(),
                                           user_id, edited_time)

            # Update
            candidate_address_query.update(address_dict)

        else:  # Create if not an update
            db.session.add(CandidateAddress(**address_dict))


def _add_or_update_candidate_areas_of_interest(candidate_id, areas_of_interest):
    """
    Function will add CandidateAreaOfInterest
    """
    for area_of_interest in areas_of_interest:
        aoi_id = area_of_interest['area_of_interest_id']
        db.session.add(CandidateAreaOfInterest(candidate_id=candidate_id,
                                               area_of_interest_id=aoi_id))


def _add_or_update_candidate_custom_field_ids(candidate_id, custom_fields, added_time, user_id, edit_time):
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
            custom_field_dict = dict((k, v) for k, v in custom_field_dict.iteritems()
                                     if v is not None)

            # CandidateCustomField must be recognized
            can_custom_field_query = db.session.query(CandidateCustomField).\
                filter_by(id=candidate_custom_field_id)
            if not can_custom_field_query.first():
                error_message = 'Candidate custom field you are requesting to update does not exist'
                raise InvalidUsage(error_message=error_message,
                                   error_code=custom_error.CUSTOM_FIELD_NOT_FOUND)

            # CandidateCustomField must belong to Candidate
            if can_custom_field_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message="Unauthorized candidate custom field",
                                     error_code=custom_error.CUSTOM_FIELD_FORBIDDEN)

            # Track all edits
            _track_candidate_custom_field_edits(custom_field_dict, can_custom_field_query.first(),
                                                candidate_id, user_id, edit_time)

            # Update CandidateCustomField
            can_custom_field_query.update(custom_field_dict)

        else:  # Add
            custom_field_dict.update(dict(added_time=added_time, candidate_id=candidate_id))
            db.session.add(CandidateCustomField(**custom_field_dict))


def _add_or_update_educations(candidate_id, educations, added_time, user_id, edit_time):
    """
    Function will update CandidateEducation, CandidateEducationDegree, and
    CandidateEducationDegreeBullet or create new ones.
    """
    # If any of educations is_current, set all of Candidate's educations' is_current to False
    if any([education.get('is_current') for education in educations]):
        CandidateEducation.set_is_current_to_false(candidate_id=candidate_id)

    for education in educations:
        # CandidateEducation
        education_dict = dict(
            list_order=education.get('list_order', 1) or 1,
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

            # CandidateEducation must be recognized
            can_education_query = db.session.query(CandidateEducation).filter_by(id=education_id)
            if not can_education_query.first():
                raise NotFoundError('Candidate education you are requesting does not exist',
                                    error_code=custom_error.EDUCATION_NOT_FOUND)

            # CandidateEducation must belong to Candidate
            if can_education_query.first().candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate education',
                                     error_code=custom_error.EDUCATION_FORBIDDEN)

            # Track all changes made to CandidateEducation
            _track_candidate_education_edits(education_dict, can_education_query.first(),
                                             candidate_id, user_id, edit_time)

            # Update CandidateEducation
            db.session.query(CandidateEducation).filter_by(id=education_id).update(education_dict)

            # CandidateEducationDegree
            education_degrees = education.get('degrees') or []
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
                    classification_type_id=classification_type_id_from_degree_type(
                            education_degree.get('type')),
                    start_time=education_degree.get('start_time'),
                    end_time=education_degree.get('end_time')
                )

                # Remove keys with None values
                education_degree_dict = dict((k, v) for k, v in education_degree_dict.iteritems()
                                             if v is not None)

                education_degree_id = education_degree.get('id')
                if education_degree_id:  # Update CandidateEducationDegree

                    # CandidateEducationDegree must be recognized
                    can_edu_degree_query = db.session.query(CandidateEducationDegree).\
                        filter_by(id=education_degree_id)
                    if not can_edu_degree_query.first():
                        raise NotFoundError('Candidate education degree not found',
                                            error_code=custom_error.DEGREE_NOT_FOUND)

                    # CandidateEducationDegree must belong to Candidate
                    if can_edu_degree_query.first().candidate_education.candidate_id != candidate_id:
                        raise ForbiddenError(error_message='Unauthorized candidate degree',
                                             error_code=custom_error.DEGREE_FORBIDDEN)

                    # Track all changes made to CandidateEducationDegree
                    _track_candidate_education_degree_edits(education_degree_dict,
                                                            can_edu_degree_query.first(),
                                                            candidate_id, user_id, edit_time)

                    can_edu_degree_query.update(education_degree_dict)

                    # CandidateEducationDegreeBullet
                    education_degree_bullets = education_degree.get('bullets') or []
                    for education_degree_bullet in education_degree_bullets:
                        education_degree_bullet_dict = dict(
                            concentration_type=education_degree_bullet.get('major'),
                            comments=education_degree_bullet.get('comments')
                        )

                        # Remove keys with None values
                        education_degree_bullet_dict = dict(
                                (k, v) for k, v in education_degree_bullet_dict.iteritems() if v is not None)

                        education_degree_bullet_id = education_degree_bullet.get('id')
                        if education_degree_bullet_id:  # Update CandidateEducationDegreeBullet

                            # CandidateEducationDegreeBullet must be recognized
                            can_edu_degree_bullet_query = db.session.query(CandidateEducationDegreeBullet).\
                                filter_by(id=education_degree_bullet_id)
                            if not can_edu_degree_bullet_query.first():
                                raise NotFoundError('Candidate education degree bullet not found',
                                                    error_code=custom_error.DEGREE_BULLET_NOT_FOUND)

                            # CandidateEducationDegreeBullet must belong to Candidate
                            if can_edu_degree_bullet_query.first().candidate_education_degree.\
                                    candidate_education.candidate_id != candidate_id:
                                raise ForbiddenError('Unauthorized candidate degree bullet',
                                                     error_code=custom_error.DEGREE_BULLET_FORBIDDEN)

                            # Track all changes made to CandidateEducationDegreeBullet
                            _track_candidate_education_degree_bullet_edits(education_degree_bullet_dict,
                                                                           can_edu_degree_bullet_query.first(),
                                                                           candidate_id, user_id, edit_time)

                            can_edu_degree_bullet_query.update(education_degree_bullet_dict) # Update
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
                    education_degree_bullets = education_degree.get('bullets') or []
                    for education_degree_bullet in education_degree_bullets:
                        db.session.add(CandidateEducationDegreeBullet(
                            candidate_education_degree_id=can_edu_degree_id,
                            concentration_type=education_degree_bullet.get('major'),
                            comments=education_degree_bullet.get('comments'),
                            added_time=added_time
                        ))

        else:  # Add
            # CandidateEducation
            education_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id))  # TODO: resume_id to be removed once all tables have been added & migrated
            candidate_education = CandidateEducation(**education_dict)
            db.session.add(candidate_education)
            db.session.flush()

            education_id = candidate_education.id

            # CandidateEducationDegree
            education_degrees = education.get('degrees') or []
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
                    classification_type_id=classification_type_id_from_degree_type(
                            education_degree.get('type')),
                    start_time=education_degree.get('start_time'),
                    end_time=education_degree.get('end_time')
                )
                db.session.add(candidate_education_degree)
                db.session.flush()

                education_degree_id = candidate_education_degree.id

                # CandidateEducationDegreeBullet
                degree_bullets = education_degree.get('bullets') or []
                for degree_bullet in degree_bullets:

                    # Add CandidateEducationDegreeBullet
                    db.session.add(CandidateEducationDegreeBullet(
                        candidate_education_degree_id=education_degree_id,
                        list_order=degree_bullet.get('list_order'),
                        concentration_type=degree_bullet.get('major'),
                        comments=degree_bullet.get('comments'),
                        added_time=added_time
                    ))


def _add_or_update_work_experiences(candidate_id, work_experiences, added_time, user_id, edit_time):
    """
    Function will update CandidateExperience and CandidateExperienceBullet
    or create new ones.
    """
    # If any of work_experiences' is_current is True, set all of candidate's experiences' is_current to False
    if any([experience.get('is_current') for experience in work_experiences]):
        CandidateExperience.set_is_current_to_false(candidate_id=candidate_id)

    for work_experience in work_experiences:
        # CandidateExperience
        experience_dict = dict(
            list_order=work_experience.get('list_order') or 1,
            organization=work_experience.get('organization'),
            position=work_experience.get('position'),
            city=work_experience.get('city'),
            state=work_experience.get('state'),
            end_month=work_experience.get('end_month'),
            start_year=work_experience.get('start_year'),
            country_id=Country.country_id_from_name_or_code(work_experience.get('country')),
            start_month=work_experience.get('start_month'),
            end_year=work_experience.get('end_year'),
            is_current=work_experience.get('is_current')
        )

        experience_id = work_experience.get('id')
        if experience_id:  # Update

            # Remove keys with None values
            experience_dict = dict((k, v) for k, v in experience_dict.iteritems() if v is not None)

            # CandidateExperience must be recognized
            can_exp_query = db.session.query(CandidateExperience).filter_by(id=experience_id)
            if not can_exp_query.first():
                raise InvalidUsage('Candidate experience not found',
                                   error_code=custom_error.EXPERIENCE_NOT_FOUND)

            # CandidateExperience must belong to Candidate
            if can_exp_query.first().candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate experience',
                                     error_code=custom_error.EXPERIENCE_FORBIDDEN)

            # Track all changes made to CandidateExperience
            _track_candidate_experience_edits(experience_dict, can_exp_query.first(),
                                              candidate_id, user_id, edit_time)

            # Update CandidateExperience
            can_exp_query.update(experience_dict)

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('bullets') or []
            for experience_bullet in experience_bullets:
                experience_bullet_dict = dict(
                    list_order=experience_bullet.get('list_order'),
                    description=experience_bullet.get('description'),
                    added_time=added_time
                )

                # Remove keys with None values
                experience_bullet_dict = dict((k, v) for k, v in experience_bullet_dict.iteritems()
                                              if v is not None)

                experience_bullet_id = experience_bullet.get('id')
                if experience_bullet_id:  # Update

                    # CandidateExperienceBullet must be recognized
                    can_exp_bullet_query = db.session.query(CandidateExperienceBullet).\
                        filter_by(id=experience_bullet_id)
                    if not can_exp_bullet_query.first():
                        raise InvalidUsage('Candidate experience bullet not found',
                                           error_code=custom_error.EXPERIENCE_BULLET_NOT_FOUND)

                    # CandidateExperienceBullet must belong to Candidate
                    if can_exp_bullet_query.first().candidate_experience.candidate_id != candidate_id:
                        raise ForbiddenError('Unauthorized candidate experience bullet',
                                             error_code=custom_error.EXPERIENCE_BULLET_FORBIDDEN)

                    # Track all changes made to CandidateExperienceBullet
                    _track_candidate_experience_bullet_edits(experience_bullet_dict,
                                                             can_exp_bullet_query.first(),
                                                             candidate_id, user_id, edit_time)

                    can_exp_bullet_query.update(experience_bullet_dict)
                else:  # Add
                    experience_bullet_dict.update(dict(candidate_experience_id=experience_id))
                    db.session.add(CandidateExperienceBullet(**experience_bullet_dict))

        else:  # Add
            experience_dict.update(dict(candidate_id=candidate_id, added_time=added_time,
                                        resume_id=candidate_id))
            experience = CandidateExperience(**experience_dict)
            db.session.add(experience)
            db.session.flush()

            experience_id = experience.id

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('bullets') or []
            for experience_bullet in experience_bullets:
                db.session.add(CandidateExperienceBullet(
                    candidate_experience_id=experience_id,
                    list_order=experience_bullet.get('list_order'),
                    description=experience_bullet.get('description'),
                    added_time=added_time
                ))


def _add_or_update_work_preference(candidate_id, work_preference, user_id, edit_time):
    """
    Function will update CandidateWorkPreference or create a new one.
    """
    work_preference_dict = dict(
        relocate=work_preference.get('relocate', False),
        authorization=work_preference.get('authorization'),
        telecommute=work_preference.get('telecommute', False),
        travel_percentage=work_preference.get('travel_percentage'),
        hourly_rate=work_preference.get('hourly_rate'),
        salary=work_preference.get('salary'),
        tax_terms=work_preference.get('employment_type'),
        security_clearance=work_preference.get('security_clearance', False),
        third_party=work_preference.get('third_party', False)
    )

    # Remove None values from update_dict
    work_preference_dict = dict((k, v) for k, v in work_preference_dict.iteritems() if v is not None)

    work_preference_id = work_preference.get('id')
    if work_preference_id:  # Update

        # CandidateWorkPreference must be recognized
        can_work_pref_query = db.session.query(CandidateWorkPreference).\
            filter_by(id=work_preference_id)
        if not can_work_pref_query.first():
            raise NotFoundError(error_message='Candidate work preference not found',
                                error_code=custom_error.WORK_PREF_NOT_FOUND)

        # CandidateWorkPreference must belong to Candidate
        if can_work_pref_query.first().candidate_id != candidate_id:
            raise ForbiddenError('Unauthorized candidate work preference',
                                 error_code=custom_error.WORK_PREF_FORBIDDEN)

        # Track all changes
        _track_candidate_work_preference_edits(work_preference_dict, can_work_pref_query.first(),
                                               candidate_id, user_id, edit_time)

        # Update
        can_work_pref_query.update(work_preference_dict)

    else:  # Add
        # Only 1 CandidateWorkPreference is permitted for each Candidate
        if db.session.query(CandidateWorkPreference).filter_by(candidate_id=candidate_id).first():
            raise InvalidUsage(error_message="Candidate work preference already exists",
                               error_code=custom_error.WORK_PREF_EXISTS)

        work_preference_dict.update(dict(candidate_id=candidate_id))
        db.session.add(CandidateWorkPreference(**work_preference_dict))


def _add_or_update_emails(candidate_id, emails, user_id, edit_time):
    """
    Function will update CandidateEmail or create new one(s).
    """
    # If any of emails' is_default is True, set all of candidate's emails' is_default to False
    if any([email.get('is_default') for email in emails]):
        CandidateEmail.set_is_default_to_false(candidate_id=candidate_id)

    emails_has_label = any([email.get('label') for email in emails])
    emails_has_default = any([email.get('is_default') for email in emails])
    for i, email in enumerate(emails):

        # If there's no is_default, the first email should be default
        is_default = i == 0 if not emails_has_default else email.get('is_default')
        # If there's no label, the first email's label will be 'Primary', rest will be 'Other'
        email_label = 'Primary' if (not emails_has_label and i == 0) else email.get('label')
        email_address = email.get('address')

        email_dict = dict(
            address=email_address,
            email_label_id=EmailLabel.email_label_id_from_email_label(email_label=email_label),
            is_default=is_default
        )

        email_id = email.get('id')
        if email_id:  # Update
            email_dict = dict((k, v) for k, v in email_dict.iteritems() if v is not None)

            # CandidateEmail must be recognized
            candidate_email_query = db.session.query(CandidateEmail).filter_by(id=email_id)
            if not candidate_email_query.first():
                raise NotFoundError(error_message='Candidate email not found',
                                    error_code=custom_error.EMAIL_NOT_FOUND)

            # CandidateEmail must belong to Candidate
            if candidate_email_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate email',
                                     error_code=custom_error.EMAIL_FORBIDDEN)

            # Track all changes
            _track_candidate_email_edits(email_dict, candidate_email_query.first(),
                                         candidate_id, user_id, edit_time)

            # Update CandidateEmail
            candidate_email_query.update(email_dict)

        else:  # Add
            email = get_candidate_email_from_domain_if_exists(candidate_id, user_id,
                                                              email_dict['address'])
            # Prevent duplicate email address for the same candidate in the same domain
            if email is None:
                email_dict.update(dict(candidate_id=candidate_id))
                db.session.add(CandidateEmail(**email_dict))


def _add_or_update_phones(candidate_id, phones, user_id, edit_time):
    """
    Function will update CandidatePhone or create new one(s).
    """
    # If any of phones' is_default is True, set all of candidate's phones' is_default to False
    if any([phone.get('is_default') for phone in phones]):
        CandidatePhone.set_is_default_to_false(candidate_id=candidate_id)

    phones_has_label = any([phone.get('label') for phone in phones])
    phones_has_default = any([phone.get('is_default') for phone in phones])
    for i, phone in enumerate(phones):

        # If there's no is_default, the first phone should be default
        is_default = i == 0 if not phones_has_default else phone.get('is_default')
        # If there's no label, the first phone's label will be 'Home', rest will be 'Other'
        phone_label = 'Home' if (not phones_has_label and i == 0) else phone.get('label')
        # Format phone number
        value = phone.get('value')
        phone_number_dict = format_phone_number(value) if value else None

        phone_dict = dict(
            value=phone_number_dict.get('formatted_number') if phone_number_dict else None,
            extension=phone_number_dict.get('extension') if phone_number_dict else None,
            phone_label_id = PhoneLabel.phone_label_id_from_phone_label(phone_label=phone_label),
            is_default=is_default
        )

        candidate_phone_id = phone.get('id')
        if candidate_phone_id:  # Update

            # Remove keys with None values
            phone_dict = dict((k, v) for k, v in phone_dict.iteritems() if v is not None)

            # CandidatePhone must be recognized
            can_phone_query = db.session.query(CandidatePhone).filter_by(id=candidate_phone_id)
            if not can_phone_query.first():
                raise NotFoundError(error_message='Candidate phone not found',
                                    error_code=custom_error.PHONE_NOT_FOUND)

            # CandidatePhone must belong to Candidate
            if can_phone_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate phone',
                                     error_code=custom_error.PHONE_FORBIDDEN)

            # Track all changes
            _track_candidate_phone_edits(phone_dict, can_phone_query.first(),
                                         candidate_id, user_id, edit_time)

            # Update CandidatePhone
            can_phone_query.update(phone_dict)

        else:  # Add
            phone_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidatePhone(**phone_dict))


def _add_or_update_military_services(candidate_id, military_services, user_id, edit_time):
    """
    Function will update CandidateMilitaryService or create new one(s).
    """
    for military_service in military_services:

        # Convert ISO 8061 date object to datetime object
        from_date, to_date = military_service.get('from_date'), military_service.get('to_date')
        if from_date:
            if isinstance(from_date, basestring):
                from_date = dateutil.parser.parse(from_date)
        if to_date:
            if isinstance(to_date, basestring):
                to_date = dateutil.parser.parse(to_date)

        military_service_dict = dict(
            country_id=Country.country_id_from_name_or_code(military_service.get('country')),
            service_status=military_service.get('status'),
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
            military_service_dict = dict((k, v) for k, v in military_service_dict.iteritems()
                                         if v is not None)

            # CandidateMilitaryService must be recognized
            can_military_service_query = db.session.query(CandidateMilitaryService).\
                filter_by(id=military_service_id)
            if not can_military_service_query.first():
                raise NotFoundError(error_message='Candidate military service not found',
                                    error_code=custom_error.MILITARY_NOT_FOUND)

            # CandidateMilitaryService must belong to Candidate
            if can_military_service_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate military service',
                                     error_code=custom_error.MILITARY_FORBIDDEN)

            # Track all changes
            _track_candidate_military_service_edits(military_service_dict,
                                                    can_military_service_query.first(),
                                                    candidate_id, user_id, edit_time)

            # Update CandidateMilitaryService
            can_military_service_query.update(military_service_dict)

        else:  # Add
            military_service_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id))
            db.session.add(CandidateMilitaryService(**military_service_dict))


def _add_or_update_preferred_locations(candidate_id, preferred_locations, user_id, edit_time):
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
            preferred_location_dict = dict((k, v) for k, v in preferred_location_dict.iteritems()
                                           if v is not None)

            # CandidatePreferredLocation must be recognized
            can_preferred_location_query = db.session.query(CandidatePreferredLocation).\
                filter_by(id=preferred_location_id)
            if not can_preferred_location_query.first():
                raise NotFoundError(error_message='Candidate preferred location not found',
                                    error_code=custom_error.PREFERRED_LOCATION_NOT_FOUND)

            # CandidatePreferredLocation must belong to Candidate
            if can_preferred_location_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate preferred location',
                                     error_code=custom_error.PREFERRED_LOCATION_FORBIDDEN)

            # Track all changes
            _track_candidate_preferred_location_edits(preferred_location_dict,
                                                      can_preferred_location_query.first(),
                                                      candidate_id, user_id, edit_time)

            # Update CandidatePreferredLocation
            can_preferred_location_query.update(preferred_location_dict)

        else:  # Add
            preferred_location_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidatePreferredLocation(**preferred_location_dict))


def _add_or_update_skills(candidate_id, skills, added_time, user_id, edit_time):
    """
    Function will update CandidateSkill or create new one(s).
    """
    for skill in skills:

        # Convert ISO 8601 date format to datetime object
        last_used_date = skill.get('last_used_date')
        if last_used_date:
            last_used_date = dateutil.parser.parse(skill.get('last_used_date'))

        skills_dict = dict(
            list_order=skill.get('list_order'),
            description=skill.get('name'),
            total_months=skill.get('months_used'),
            last_used=last_used_date
        )

        skill_id = skill.get('id')
        if skill_id:  # Update

            # Remove keys with None values
            skills_dict = dict((k, v) for k, v in skills_dict.iteritems() if v is not None)

            # CandidateSkill must be recognized
            can_skill_query = db.session.query(CandidateSkill).filter_by(id=skill_id)
            if not can_skill_query.first():
                raise NotFoundError(error_message='Candidate skill not found',
                                    error_code=custom_error.SKILL_NOT_FOUND)

            # CandidateSkill must belong to Candidate
            if can_skill_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate skill',
                                     error_code=custom_error.SKILL_FORBIDDEN)

            # Track all changes
            _track_candidate_skill_edits(skills_dict, can_skill_query.first(),
                                         candidate_id, user_id, edit_time)

            # Update CandidateSkill
            can_skill_query.update(skills_dict)

        else:  # Add
            skills_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id,
                                    added_time=added_time))
            db.session.add(CandidateSkill(**skills_dict))


def _add_or_update_social_networks(candidate_id, social_networks, user_id, edit_time):
    """
    Function will update CandidateSocialNetwork or create new one(s).
    """
    for social_network in social_networks:

        if not social_network.get('name'):
            social_network['name'] = social_network_name_from_url(social_network.get('profile_url'))

        social_network_dict = dict(
            social_network_id=social_network_id_from_name(name=social_network.get('name')),
            social_profile_url=social_network.get('profile_url')
        )

        # Todo: what if url and/or name is not provided?
        social_network_id = social_network.get('id')
        if social_network_id:  # Update

            # CandidateSocialNetwork must be recognized
            can_sn_query = db.session.query(CandidateSocialNetwork).filter_by(id=social_network_id)
            if not can_sn_query.first():
                raise NotFoundError(error_message='Candidate social network not found',
                                    error_code=custom_error.SOCIAL_NETWORK_NOT_FOUND)

            # CandidateSocialNetwork must belong to Candidate
            if can_sn_query.first().candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate social network',
                                     error_code=custom_error.SOCIAL_NETWORK_FORBIDDEN)

            # Track all changes
            _track_candidate_social_network_edits(social_network_dict, can_sn_query.first(),
                                                  candidate_id, user_id, edit_time)

            can_sn_query.update(social_network_dict)

        else:  # Add
            social_network_dict.update(dict(candidate_id=candidate_id))
            db.session.add(CandidateSocialNetwork(**social_network_dict))


def _add_or_update_candidate_talent_pools(candidate_id, talent_pool_ids, is_creating, is_updating):

    talent_pools_to_be_added = talent_pool_ids.get('add')
    talent_pools_to_be_deleted = talent_pool_ids.get('delete')

    if is_creating or is_updating and talent_pools_to_be_added:
        for talent_pool_id in talent_pools_to_be_added:
            talent_pool = TalentPool.query.get(int(talent_pool_id))
            if not talent_pool:
                raise NotFoundError("TalentPool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise UnauthorizedError("TalentPool and logged in user belong to different domains")

            if not TalentPoolGroup.get(talent_pool_id, request.user.user_group_id):
                raise UnauthorizedError("TalentPool %s doesn't belong to UserGroup %s of logged-in "
                                        "user" % (talent_pool_id, request.user.user_group_id))

            # In case candidate was web-hidden, the recreated with the same talent-pool-id
            talent_pool_candidate = TalentPoolCandidate.get(candidate_id, talent_pool_id)
            if talent_pool_candidate and is_updating:
                pass
            else:
                db.session.add(TalentPoolCandidate(candidate_id=candidate_id,
                                                   talent_pool_id=talent_pool_id))

    if is_updating and talent_pools_to_be_deleted:
        for talent_pool_id in talent_pools_to_be_deleted:
            talent_pool = TalentPool.query.get(int(talent_pool_id))
            if not talent_pool:
                raise NotFoundError("TalentPool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise UnauthorizedError("TalentPool and logged in user belong to different domains")

            if not TalentPoolGroup.get(talent_pool_id, request.user.user_group_id):
                raise UnauthorizedError("TalentPool %s doesn't belong to UserGroup %s of logged-in "
                                        "user" % (talent_pool_id, request.user.user_group_id))

            talent_pool_candidate = TalentPoolCandidate.get(candidate_id, talent_pool_id)
            if not talent_pool_candidate:
                raise InvalidUsage("Candidate %s doesn't belong to TalentPool %s" %
                                   (candidate_id, talent_pool_id))
            else:
                db.session.delete(talent_pool_candidate)


###############################################################
# Helper Functions For Tracking updates made to the Candidate #
###############################################################
def _track_candidate_edits(update_dict, candidate, user_id, edit_time):
    for field in update_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id(table_name='candidate', field_name=field)
        if not field_id:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,  # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate.id,
            field_id=field_id,
            old_value=getattr(candidate, field),
            new_value=update_dict.get(field),
            edit_datetime=edit_time
        ))


def _track_candidate_address_edits(address_dict, candidate_id, candidate_address, user_id, edit_time):
    for field in address_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_address', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_address, field), address_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_custom_field_edits(custom_field_dict, candidate_custom_field,
                                        candidate_id, user_id, edit_time):
    for field in custom_field_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_custom_field', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_custom_field, field), custom_field_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            is_custom_field=True,
            edit_datetime=edit_time
        ))


def _track_candidate_education_edits(education_dict, candidate_education,
                                     candidate_id, user_id, edit_time):
    for field in education_dict:

        # If field_id is not found, do not add to record
        field_id = CandidateEdit.get_field_id('candidate_education', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_education, field), education_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_education_degree_edits(degree_dict, candidate_education_degree,
                                            candidate_id, user_id, edit_time):
    for field in degree_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_education_degree', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_education_degree, field), degree_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_education_degree_bullet_edits(degree_bullet_dict, candidate_education_degree_bullet,
                                                   candidate_id, user_id, edit_time):
    for field in degree_bullet_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_education_degree_bullet', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_education_degree_bullet, field), degree_bullet_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_experience_edits(experience_dict, candidate_experience, candidate_id,
                                      user_id, edit_time):
    for field in experience_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_experience', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_experience, field), experience_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_experience_bullet_edits(bullet_dict, candidate_experience_bullet, candidate_id,
                                             user_id, edit_time):
    for field in bullet_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_experience_bullet', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_experience_bullet, field), bullet_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_work_preference_edits(work_preference_dict, candidate_work_preference,
                                           candidate_id, user_id, edit_time):
    for field in work_preference_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_work_preference', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_work_preference, field), work_preference_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_email_edits(email_dict, candidate_email, candidate_id, user_id, edit_time):
    for field in email_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_email', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_email, field), email_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_phone_edits(phone_dict, candidate_phone, candidate_id, user_id, edit_time):
    for field in phone_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_phone', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_phone, field), phone_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_military_service_edits(military_service_dict, candidate_military_service,
                                            candidate_id, user_id, edit_time):
    for field in military_service_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_military_service', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_military_service, field), military_service_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_preferred_location_edits(preferred_location_dict, candidate_preferred_location,
                                              candidate_id, user_id, edit_time):
    for field in preferred_location_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_preferred_location', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_preferred_location, field), preferred_location_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_skill_edits(skill_dict, candidate_skill, candidate_id, user_id, edit_time):
    for field in skill_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_skill', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_skill, field), skill_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_social_network_edits(sn_dict, candidate_social_network, candidate_id, user_id, edit_time):
    for field in sn_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_social_network', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_social_network, field), sn_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def get_candidate_email_from_domain_if_exists(candidate_id, user_id, email_address):
    """
    Function will retrieve CandidateEmail belonging to the requested candidate
    in the same domain if found.
    :type candidate_id:  int|long
    :type user_id:       int|long
    :type email_address: basestring
    :rtype: CandidateEmail|None
    """
    user_domain_id = User.get_domain_id(_id=user_id)
    candidate_email = CandidateEmail.query.join(Candidate).join(User).filter(
            CandidateEmail.address == email_address, User.domain_id == user_domain_id).first()
    return candidate_email if candidate_email else None
