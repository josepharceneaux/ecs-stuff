"""
Helper functions for candidate CRUD operations and tracking edits made to the Candidate
"""
# Standard libraries
import re
import datetime
import urlparse
import dateutil.parser
import simplejson as json
import pycountry
import phonenumbers
from flask import request
from datetime import date
from nameparser import HumanName

# Database connection and logger
from candidate_service.common.models.db import db
from candidate_service.common.models.smartlist import Smartlist
from candidate_service.candidate_app import logger

# Models
from candidate_service.common.models.candidate import (
    Candidate, CandidateEmail, CandidatePhone, CandidateWorkPreference, CandidatePreferredLocation,
    CandidateAddress, CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField, CandidateSocialNetwork,
    SocialNetwork, CandidateEducationDegreeBullet, CandidateExperienceBullet, ClassificationType,
    CandidatePhoto, CandidateTextComment, PhoneLabel, EmailLabel, CandidateSubscriptionPreference
)
from candidate_service.common.models.talent_pools_pipelines import TalentPoolCandidate, TalentPool, TalentPoolGroup
from candidate_service.common.models.candidate_edit import CandidateEdit, CandidateView
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.email_campaign import EmailCampaign
from candidate_service.common.models.misc import AreaOfInterest
from candidate_service.common.models.language import CandidateLanguage
from candidate_service.common.models.user import User

# Modules
from track_changes import track_edits, track_areas_of_interest_edits

# Error handling
from candidate_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

# Validations
from candidate_service.common.utils.validators import sanitize_zip_code, is_number, format_phone_number, parse_phone_number
from candidate_service.modules.validators import (
    does_address_exist, does_candidate_cf_exist, does_education_degree_bullet_exist,
    get_education_if_exists, get_work_experience_if_exists, does_experience_bullet_exist,
    does_phone_exist, does_preferred_location_exist, does_skill_exist, does_social_network_exist,
    get_education_degree_if_exists, does_military_service_exist
)

# Common utilities
from candidate_service.common.utils.talent_s3 import get_s3_url
from candidate_service.common.utils.iso_standards import get_country_name, get_subdivision_name
from candidate_service.common.utils.datetime_utils import DatetimeUtils
from candidate_service.common.geo_services.geo_coordinates import get_coordinates

# Handy functions
from candidate_service.common.utils.handy_functions import purge_dict

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
        created_at_datetime = DatetimeUtils.utc_isoformat(candidate.added_time)

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

    resume_url = None
    if (get_all_fields or 'resume_url' in fields) and candidate.filename:
        resume_url = get_s3_url(folder_path="OriginalFiles", name=candidate.filename)

    return_dict = {
        'id': candidate_id,
        'owner': candidate.user_id,
        'first_name': candidate.first_name,
        'middle_name': candidate.middle_name,
        'last_name': candidate.last_name,
        'full_name': full_name,
        'created_at_datetime': created_at_datetime,
        'updated_at_datetime': created_at_datetime,
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
        'talent_pool_ids': talent_pool_ids,
        'resume_url': resume_url
    }

    # Remove keys with None values
    return_dict = dict((k, v) for k, v in return_dict.iteritems() if v is not None)
    return return_dict


def format_candidate_full_name(candidate):
    """
    :type candidate:  Candidate
    :rtype:  basestring
    """
    assert isinstance(candidate, Candidate)
    first_name, middle_name, last_name = candidate.first_name, candidate.middle_name, candidate.last_name
    return get_fullname_from_name_fields(first_name or '', middle_name or '', last_name or '')


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
    addresses = CandidateAddress.query.filter_by(candidate_id=candidate_id).order_by(CandidateAddress.is_default.desc())
    return [{'id': address.id,
             'address_line_1': address.address_line_1,
             'address_line_2': address.address_line_2,
             'city': address.city,
             'state': address.state,
             'subdivision': get_subdivision_name(address.iso3166_subdivision) if address.iso3166_subdivision else None,
             'zip_code': address.zip_code,
             'po_box': address.po_box,
             'country': get_country_name(address.iso3166_country),
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
             'subdivision': get_subdivision_name(experience.iso3166_subdivision) if experience.iso3166_subdivision else None,
             'country': get_country_name(experience.iso3166_country),
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
             'added_time': DatetimeUtils.to_utc_str(experience_bullet.added_time) if experience_bullet.added_time else None
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
            } if work_preference else {}


def candidate_preferred_locations(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    return [{'id': preferred_location.id,
             'address': preferred_location.address,
             'city': preferred_location.city,
             'state': preferred_location.region,
             'subdivision': get_subdivision_name(preferred_location.iso3166_subdivision)
             if preferred_location.iso3166_subdivision else None,
             'country': get_country_name(preferred_location.iso3166_country)
             } for preferred_location in candidate.preferred_locations]


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
             'subdivision': get_subdivision_name(education.iso3166_subdivision) if education.iso3166_subdivision else None,
             'country': get_country_name(education.iso3166_country),
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
             'from_date': str(military_info.from_date.date()) if military_info.from_date else None,
             'to_date': str(military_info.to_date.date()) if military_info.from_date else None,
             'country': get_country_name(military_info.iso3166_country),
             'comments': military_info.comments
             } for military_info in military_experiences]


def candidate_custom_fields(candidate):
    """
    :type candidate:    Candidate
    :rtype              [dict]
    """
    assert isinstance(candidate, Candidate)
    return [{'id': custom_field.id,
             'value': custom_field.value,
             'created_at_datetime': custom_field.added_time.isoformat()
             } for custom_field in db.session.query(CandidateCustomField).filter_by(candidate_id=candidate.id).all()]


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


class ContactHistoryEvent(object):
    CREATED_AT = 'created_at'
    EMAIL_SEND = 'email_send'
    EMAIL_OPEN = 'email_open'  # Todo: Implement opens and clicks into timeline
    EMAIL_CLICK = 'email_click'


def candidate_contact_history(candidate):
    """
    :type candidate:    Candidate
    :rtype              dict
    """
    # Campaign sends & campaigns
    timeline = []
    for email_campaign_send in candidate.email_campaign_sends:
        if not email_campaign_send.campaign_id:
            logger.error("contact_history: email_campaign_send has no campaign_id: %s", email_campaign_send.id)
            continue
        email_campaign = db.session.query(EmailCampaign).get(email_campaign_send.campaign_id)
        timeline.insert(0, dict(id=email_campaign.id,
                                event_datetime=email_campaign_send.sent_datetime,
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
             'view_datetime': DatetimeUtils.to_utc_str(view.view_datetime)
             } for view in candidate_views]


def fetch_aggregated_candidate_views(domain_id, candidate_id):
    """
    Function will return a list of view objects displaying all the domain users
     that viewed the candidate, last datetime of view, and the number of times each
     user viewed the same candidate
    :type domain_id:  int|long
    :type candidate_id:  int|long
    :rtype:  list[dict[str]]
    """
    team_members = User.all_users_of_domain(domain_id)
    """
    :type team_members:  list[User]
    """
    return_obj = []
    for user in team_members:
        views = CandidateView.get_by_user_and_candidate(user_id=user.id, candidate_id=candidate_id)
        if views:
            return_obj.append(
                {
                    'user_id': user.id,
                    'last_view_datetime': DatetimeUtils.to_utc_str(views[-1].view_datetime),
                    'view_count': len(views)
                }
            )

    return return_obj


def add_candidate_view(user_id, candidate_id):
    """
    Once a Candidate has been viewed, this function should be invoked
    and add a record to CandidateView
    :type user_id: int|long
    :type candidate_id: int|long
    """
    db.session.add(CandidateView(
        user_id=user_id,
        candidate_id=candidate_id,
        view_type=3,
        view_datetime=datetime.datetime.utcnow()
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
        db.session.add(CandidateSubscriptionPreference(candidate_id=candidate_id, frequency_id=frequency_id))
    db.session.commit()


#######################################
# Helper Functions For Candidate Photos
#######################################
def add_photos(candidate_id, photos):
    """
    Function will add a new entry into CandidatePhoto
    :type candidate_id: int|long
    :type user_id: int|long
    :type photos:  list[dict[str, T]]
    """
    # Check if any of the photo objects have is_default value
    photo_has_default = any(photo.get('is_default') for photo in photos)
    if photo_has_default:
        CandidatePhoto.set_is_default_to_false(candidate_id=candidate_id)

    for i, photo in enumerate(photos):
        # Format inputs
        is_default = i == 0 if not photo_has_default else photo['is_default']
        added_time = photo['added_datetime'] if photo.get('added_datetime') else datetime.datetime.utcnow()
        image_url = photo['image_url']

        # Prevent duplicate insertions
        if CandidatePhoto.exists(candidate_id=candidate_id, image_url=image_url):
            continue

        db.session.add(CandidatePhoto(candidate_id=candidate_id, image_url=image_url,
                                      is_default=is_default, added_datetime=added_time))
    db.session.commit()


def update_photo(candidate_id, user_id, update_dict):
    """
    Function will update CandidatePhoto data
    :type candidate_id:  int|long
    :type user_id:   int|long
    """
    photo_id = update_dict['id']
    photo_query = CandidatePhoto.query.filter_by(id=photo_id)
    photo_object = photo_query.first()

    # Photo must be recognized
    if not photo_object:
        raise NotFoundError('Candidate photo not found; photo-id: {}'.format(photo_id),
                            error_code=custom_error.PHOTO_NOT_FOUND)

    # Photo must belong to candidate
    if photo_object.candidate_id != candidate_id:
        raise ForbiddenError('Unauthorized candidate photo', error_code=custom_error.PHOTO_FORBIDDEN)

    # Format inputs
    photo_update_dict = dict(candidate_id=candidate_id,
                             image_url=update_dict.get('image_url'),
                             is_default=update_dict.get('is_default'),
                             updated_datetime=datetime.datetime.utcnow())
    photo_update_dict = dict((k, v) for k, v in photo_update_dict.iteritems() if v is not None)

    # Track all changes
    track_edits(update_dict=photo_update_dict, query_obj=photo_object, table_name='candidate_photo',
                candidate_id=candidate_id, user_id=user_id)

    # Update candidate's photo
    photo_query.update(photo_update_dict)
    return


######################################
# Helper Functions For Candidate Notes
######################################
def add_notes(candidate_id, data):
    """
    Function will insert candidate notes into the db
    :type candidate_id:  int|long
    :type data:  list[dict]
    """
    # Format inputs
    for note in data:
        notes_dict = dict(
            candidate_id=candidate_id,
            comment=note.get('comment'),
            added_time=datetime.datetime.utcnow()
        )
        notes_dict = dict((k, v) for k, v in notes_dict.iteritems() if v is not None)
        db.session.add(CandidateTextComment(**notes_dict))


##########################################
# Helper Functions For Candidate Languages
##########################################
def add_languages(candidate_id, data):
    """
    Function will insert candidate languages into the db
    :type candidate_id:  int|long
    :type data:  list
    :rtype:  list[dict]
    """
    for language in data:
        language_dict = dict(
            candidate_id=candidate_id,
            resume_id=candidate_id,
            iso639_language=language['language_code'].lower() if language.get('language_code') else None,
            read=language.get('read'),
            write=language.get('write'),
            speak=language.get('speak')
        )
        language_dict = dict((k, v) for k, v in language_dict.iteritems() if v is not None)
        db.session.add(CandidateLanguage(**language_dict))


def fetch_candidate_languages(candidate_id, language=None):
    """
    :type candidate_id:  int|long
    :type language:  CandidateLanguage | None
    """
    if language:
        return [{'language_code': language.iso639_language,
                 'language_name': pycountry.languages.get(iso639_1_code=language.iso639_language).name,
                 'read': language.read, 'write': language.write, 'speak': language.speak}]
    else:
        return [
            {'id': language.id, 'candidate_id': candidate_id,
             'language_code': language.iso639_language, 'read': language.read,
             'write': language.write, 'speak': language.speak,
             'language_name': pycountry.languages.get(iso639_1_code=language.iso639_language).name
             if language.iso639_language else None}
            for language in CandidateLanguage.get_by_candidate_id(candidate_id)]


def update_candidate_languages(candidate_id, update_data, user_id):
    """
    :type candidate_id:  int|long
    :type update_data:  list[dict]
    :type user_id:  int|long
    """
    current_time = datetime.datetime.utcnow()
    for update_dict in update_data:

        language_id = update_dict.get('id')
        language_query = CandidateLanguage.query.filter_by(id=language_id)
        language_obj = language_query.first()

        # CandidateLanguage must be recognized
        if not language_obj:
            raise NotFoundError('Candidate language not recognized: {}'.format(language_id),
                                error_code=custom_error.PHOTO_NOT_FOUND)

        # Photo must belong to candidate
        if language_obj.candidate_id != candidate_id:
            raise ForbiddenError('Unauthorized candidate language', custom_error.PHOTO_FORBIDDEN)

        # Format inputs
        language_update_dict = dict(
            candidate_id=candidate_id,
            read=update_dict.get('read'),
            write=update_dict.get('write'),
            speak=update_dict.get('speak'),
            iso639_language=update_dict.get('language_code'),
            updated_time=current_time
        )
        language_update_dict = dict((k, v) for k, v in language_update_dict.iteritems() if v is not None)

        # Track all changes
        track_edits(update_dict=language_update_dict, table_name='candidate_language',
                    candidate_id=candidate_id, user_id=user_id, query_obj=language_obj)

        # Update candidate's photo
        language_query.update(language_update_dict)
        return


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
        added_datetime=None,
        source_id=None,
        objective=None,
        summary=None,
        talent_pool_ids=None,
        resume_url=None
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
    :type added_datetime:           str
    :type source_id:                int
    :type objective:                basestring
    :type summary:                  basestring
    :type talent_pool_ids:          dict
    :type delete_talent_pools:      bool
    :type resume_url                basestring
    :rtype                          dict
    """
    # Format inputs
    added_datetime = added_datetime or datetime.datetime.utcnow()
    status_id = status_id or 1
    edit_datetime = datetime.datetime.utcnow()  # Timestamp for tracking edits

    # Get user's domain ID
    domain_id = domain_id_from_user_id(user_id)

    # Prevent creating a candidate if candidate ID is provided or found; Parse our candidate's names
    if is_creating:

        # Cannot request candidate creation when supplying candidate's ID
        if candidate_id:
            raise InvalidUsage(error_message='Candidate already exists, creation failed',
                               error_code=custom_error.CANDIDATE_ALREADY_EXISTS,
                               additional_error_info={'id': candidate_id})

        # Raise an error if creation is requested and candidate_id is found
        candidate_id_from_dice_profile = get_candidate_id_if_found(dice_social_profile_id, dice_profile_id, domain_id)
        if candidate_id_from_dice_profile:
            raise InvalidUsage(error_message='Candidate already exists, creation failed',
                               error_code=custom_error.CANDIDATE_ALREADY_EXISTS,
                               additional_error_info={'id': candidate_id})

        # Figure out first_name, last_name, middle_name, and formatted_name from inputs
        if first_name or last_name or middle_name or formatted_name:
            if (first_name or last_name) and not formatted_name:
                # If first_name and last_name given but not formatted_name, guess it
                formatted_name = get_fullname_from_name_fields(first_name or '', middle_name or '', last_name or '')
            elif formatted_name and (not first_name or not last_name):
                # Otherwise, guess formatted_name from the other fields
                first_name, middle_name, last_name = get_name_fields_from_name(formatted_name)

    # Update is not possible without candidate ID
    if not candidate_id and is_updating:
        raise InvalidUsage('Candidate ID is required for updating', custom_error.MISSING_INPUT)

    if is_updating:  # Update Candidate
        candidate_id = _update_candidate(first_name, middle_name, last_name,
                                         formatted_name, objective, summary,
                                         candidate_id, user_id, resume_url)
    else:  # Add Candidate
        candidate_id = _add_candidate(first_name, middle_name, last_name,
                                      formatted_name, added_datetime, status_id,
                                      user_id, dice_profile_id, dice_social_profile_id,
                                      source_id, objective, summary, resume_url)

    candidate = Candidate.get_by_id(candidate_id)
    """
    :type candidate: Candidate
    """

    # Add or update Candidate's talent-pools
    if talent_pool_ids:  # TODO: track all updates
        _add_or_update_candidate_talent_pools(candidate_id, talent_pool_ids, is_creating, is_updating)

    # Add or update Candidate's address(es)
    if addresses:
        _add_or_update_candidate_addresses(candidate, addresses, user_id, is_updating)

    # Add or update Candidate's areas_of_interest
    if areas_of_interest:
        _add_or_update_candidate_areas_of_interest(candidate_id, areas_of_interest, user_id, edit_datetime,
                                                   is_updating)

    # Add or update Candidate's custom_field(s)
    if custom_fields:
        _add_or_update_candidate_custom_field_ids(candidate, custom_fields, added_datetime, user_id, is_updating)

    # Add or update Candidate's education(s)
    if educations:
        _add_or_update_educations(candidate, educations, added_datetime, user_id, is_updating)

    # Add or update Candidate's work experience(s)
    if work_experiences:
        _add_or_update_work_experiences(candidate, work_experiences, added_datetime, user_id, is_updating)

    # Add or update Candidate's work preference(s)
    if work_preference:
        _add_or_update_work_preference(candidate_id, work_preference, user_id)

    # Add or update Candidate's email(s)
    if emails:
        _add_or_update_emails(candidate_id, emails, user_id, is_updating)

    # Add or update Candidate's phone(s)
    if phones:
        _add_or_update_phones(candidate, phones, user_id, is_updating)

    # Add or update Candidate's military service(s)
    if military_services:
        _add_or_update_military_services(candidate, military_services, user_id, is_updating)

    # Add or update Candidate's preferred location(s)
    if preferred_locations:
        _add_or_update_preferred_locations(candidate, preferred_locations, user_id, is_updating)

    # Add or update Candidate's skill(s)
    if skills:
        _add_or_update_skills(candidate, skills, added_datetime, user_id, is_updating)

    # Add or update Candidate's social_network(s)
    if social_networks:
        _add_or_update_social_networks(candidate, social_networks, user_id, is_updating)

    # Commit to database after all insertions/updates are executed successfully
    db.session.commit()
    return dict(candidate_id=candidate_id)


def get_fullname_from_name_fields(first_name, middle_name, last_name):
    """
    Function will concatenate names if any, otherwise will return empty string
    :rtype: str
    """
    full_name = re.sub(' +', ' ', '%s %s %s' % (first_name, middle_name, last_name))
    return full_name.replace('None', '').strip()


def format_full_name(first_name=None, middle_name=None, last_name=None):
    # Figure out first_name, last_name, middle_name, and formatted_name from inputs
    if first_name or last_name or middle_name:
        if first_name or last_name:
            # If first_name and last_name given but not formatted_name, guess it
            return get_fullname_from_name_fields(first_name or '', middle_name or '', last_name or '')


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


def get_candidate_id_if_found(dice_social_profile_id, dice_profile_id, domain_id):
    """
    Function will search the db for a candidate with the same parameter(s) as provided
    :type dice_social_profile_id: int|long
    :type dice_profile_id: int|long
    :type domain_id: int|long
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


def _update_candidate(first_name, middle_name, last_name, formatted_name, objective,
                      summary, candidate_id, user_id, resume_url):
    """
    Function will update Candidate
    :return:    Candidate ID
    """
    # If formatted name is provided, must also update first name, middle name, and last name
    if formatted_name:
        parsed_names_object = HumanName(formatted_name)
        first_name = parsed_names_object.first
        middle_name = parsed_names_object.middle
        last_name = parsed_names_object.last

    update_dict = {'objective': objective, 'summary': summary, 'filename': resume_url}

    # Remove keys with empty values and strip each value
    update_dict = purge_dict(update_dict)

    # Update request dict with candidate names
    # Candidate name(s) will be removed if empty string is provided; None values will be ignored
    names_dict = dict(
        first_name=first_name, middle_name=middle_name, last_name=last_name,
        formatted_name=formatted_name or format_full_name(first_name, middle_name, last_name)
    )
    names_dict = {k: v for k, v in names_dict.items() if v is not None}

    # Add names' data to update_dict if at least one of name is provided
    if not all(v is None for v in names_dict.values()):
        update_dict.update(**names_dict)

    # Candidate will not be updated if update_dict is empty
    if not update_dict:
        return candidate_id

    # Candidate ID must be recognized
    candidate_object = Candidate.get_by_id(candidate_id)
    if not candidate_object:
        raise NotFoundError('Candidate not found', custom_error.CANDIDATE_NOT_FOUND)

    # Track all edits
    track_edits(update_dict=update_dict, table_name='candidate', candidate_id=candidate_id,
                user_id=user_id, query_obj=candidate_object)

    # Update
    candidate_object.update(**update_dict)

    return candidate_id


def _add_candidate(first_name, middle_name, last_name, formatted_name,
                   added_time, candidate_status_id, user_id,
                   dice_profile_id, dice_social_profile_id, source_id,
                   objective, summary, resume_url):
    """
    Function will create Candidate
    :rtype:  Candidate.id
    """
    candidate = Candidate(
        first_name=first_name, middle_name=middle_name, last_name=last_name, formatted_name=formatted_name,
        added_time=added_time, candidate_status_id=candidate_status_id, user_id=user_id,
        dice_profile_id=dice_profile_id, dice_social_profile_id=dice_social_profile_id,
        source_id=source_id, objective=objective, summary=summary, filename=resume_url,
        is_dirty=0  # TODO: is_dirty cannot be null. This should be removed once the field is successfully removed.
    )
    db.session.add(candidate)
    db.session.flush()
    return candidate.id


def _add_or_update_candidate_addresses(candidate, addresses, user_id, is_updating):
    """
    Function will update CandidateAddress or create a new one.
    :type addresses: list[dict[str, T]]
    """
    # If any of addresses is_default, set candidate's addresses' is_default to False
    candidate_id = candidate.id
    address_has_default = any([address.get('is_default') for address in addresses])
    if address_has_default:
        CandidateAddress.set_is_default_to_false(candidate_id)

    for i, address in enumerate(addresses):

        zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
        city = address['city'].strip() if address.get('city') else None
        country_code = address['country_code'].upper() if address.get('country_code') else None
        subdivision_code = address['subdivision_code'].upper() if address.get('subdivision_code') else None
        address_dict = dict(
            address_line_1=address['address_line_1'].strip() if address.get('address_line_1') else None,
            address_line_2=address['address_line_2'].strip() if address.get('address_line_2') else None,
            city=city,
            iso3166_subdivision=subdivision_code,
            iso3166_country=country_code,
            zip_code=zip_code,
            po_box=address['po_box'].strip() if address.get('po_box') else None,
            is_default=i == 0 if address_has_default else address.get('is_default'),
            coordinates=get_coordinates(zipcode=zip_code, city=city, state=subdivision_code)
        )

        # Remove keys that have None values
        address_dict = {k: v for k, v in address_dict.items() if v}

        # Prevent adding empty records to db
        if not address_dict:
            continue

        # Cache country code
        CachedData.country_codes.append(address_dict.get('iso3166_country'))

        address_id = address.get('id')
        if address_id:  # Update

            # CandidateAddress must be recognized before updating
            candidate_address_obj = CandidateAddress.get_by_id(address_id)
            if not candidate_address_obj:
                raise InvalidUsage('Candidate address not found', custom_error.ADDRESS_NOT_FOUND)

            # CandidateAddress must belong to Candidate
            if candidate_address_obj.candidate_id != candidate_id:
                raise ForbiddenError("Unauthorized candidate address", custom_error.ADDRESS_FORBIDDEN)

            # Track all updates
            track_edits(update_dict=address_dict, table_name='candidate_address', candidate_id=candidate_id,
                        user_id=user_id, query_obj=candidate_address_obj)

            # Update
            candidate_address_obj.update(**address_dict)

        else:  # Create if not an update
            address_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id))
            # Prevent duplicate insertions
            if not does_address_exist(candidate=candidate, address_dict=address_dict):
                db.session.add(CandidateAddress(**address_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=address_dict, table_name='candidate_address',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_candidate_areas_of_interest(candidate_id, areas_of_interest, user_id, edit_datetime, is_updating):
    """
    Function will add CandidateAreaOfInterest
    """
    for area_of_interest in areas_of_interest:
        # AreaOfInterest object must be recognized
        aoi_id = area_of_interest['area_of_interest_id']

        # Prevent duplicate insertions
        if CandidateAreaOfInterest.get_aoi(candidate_id=candidate_id, aoi_id=aoi_id):
            continue

        db.session.add(CandidateAreaOfInterest(candidate_id=candidate_id, area_of_interest_id=aoi_id))

        if is_updating:  # Track all updates
            track_areas_of_interest_edits(aoi_id, candidate_id, user_id, edit_datetime)


def _add_or_update_candidate_custom_field_ids(candidate, custom_fields, added_time, user_id, is_updating):
    """
    Function will update CandidateCustomField or create a new one.
    """
    candidate_id = candidate.id
    for custom_field in custom_fields:
        custom_field_dict = dict(
            value=custom_field['value'].strip() if custom_field.get('value') else None,
            custom_field_id=custom_field.get('custom_field_id')
        )

        candidate_custom_field_id = custom_field.get('id')
        if candidate_custom_field_id:   # Update

            # Remove keys with None values
            custom_field_dict = dict((k, v) for k, v in custom_field_dict.iteritems() if v is not None)

            # CandidateCustomField must be recognized
            can_custom_field_obj = CandidateCustomField.get_by_id(candidate_custom_field_id)
            if not can_custom_field_obj:
                error_message = 'Candidate custom field you are requesting to update does not exist'
                raise InvalidUsage(error_message, custom_error.CUSTOM_FIELD_NOT_FOUND)

            # CandidateCustomField must belong to Candidate
            if can_custom_field_obj.candidate_id != candidate_id:
                raise ForbiddenError(error_message="Unauthorized candidate custom field",
                                     error_code=custom_error.CUSTOM_FIELD_FORBIDDEN)

            # Track all updates
            track_edits(update_dict=custom_field_dict, table_name='candidate_custom_field',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_custom_field_obj)

            # Update CandidateCustomField
            can_custom_field_obj.update(**custom_field_dict)

        else:  # Add
            custom_field_dict.update(dict(added_time=added_time, candidate_id=candidate_id))
            # Prevent duplicate insertions
            if not does_candidate_cf_exist(candidate, custom_field_dict):
                db.session.add(CandidateCustomField(**custom_field_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=custom_field_dict, table_name='candidate_custom_field',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_educations(candidate, educations, added_datetime, user_id, is_updating):
    """
    Function will update CandidateEducation, CandidateEducationDegree, and
    CandidateEducationDegreeBullet or create new ones.
    """
    # If any of educations is_current, set all of Candidate's educations' is_current to False
    candidate_id, candidate_educations = candidate.id, candidate.educations
    if any([education.get('is_current') for education in educations]):
        CandidateEducation.set_is_current_to_false(candidate_id=candidate_id)

    for education in educations:
        # CandidateEducation
        country_code = education['country_code'].upper() if education.get('country_code') else None
        subdivision_code = education['subdivision_code'].upper() if education.get('subdivision_code') else None
        education_dict = dict(
            school_name=education['school_name'].strip() if education.get('school_name') else None,
            school_type=education['school_type'].strip() if education.get('school_type') else None,
            city=education['city'].strip() if education.get('city') else None,
            iso3166_subdivision=subdivision_code,
            iso3166_country=country_code,
            is_current=education.get('is_current')
        )

        # Remove keys with empty values
        education_dict = {k: v for k, v in education_dict.items() if v}

        # Prevent empty records from being added to the db
        education_degrees = education.get('degrees') or []
        if not education_dict and not education_degrees:
            continue

        education_id = education.get('id')
        if education_id:  # Update

            # CandidateEducation must be recognized
            can_education_obj = CandidateEducation.get(education_id)
            if not can_education_obj:
                raise NotFoundError('Candidate education you are requesting does not exist',
                                    error_code=custom_error.EDUCATION_NOT_FOUND)

            # CandidateEducation must belong to Candidate
            if can_education_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate education', custom_error.EDUCATION_FORBIDDEN)

            # Track all changes made to CandidateEducation
            track_edits(update_dict=education_dict, table_name='candidate_education',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_education_obj)

            # Update CandidateEducation
            if education_dict:
                can_education_obj.update(**education_dict)

            # CandidateEducationDegree
            for education_degree in education_degrees:
                education_degree_dict = dict(
                    list_order=education_degree.get('list_order'),
                    degree_type=education_degree['type'].strip() if education_degree.get('type') else None,
                    degree_title=education_degree['title'].strip() if education_degree.get('title') else None,
                    start_year=education_degree.get('start_year'),
                    start_month=education_degree.get('start_month'),
                    end_year=education_degree.get('end_year'),
                    end_month=education_degree.get('end_month'),
                    gpa_num=education_degree.get('gpa'),
                    added_time=added_datetime,
                    classification_type_id=classification_type_id_from_degree_type(education_degree.get('type')),
                    start_time=education_degree.get('start_time'),
                    end_time=education_degree.get('end_time')
                )
                # Remove keys with None values
                education_degree_dict = {k: v for k, v in education_degree_dict.items() if v}

                # Prevent empty records from being inserted into db
                education_degree_bullets = education_degree.get('bullets') or []
                if not education_degree_dict and not education_degree_bullets:
                    continue

                education_degree_id = education_degree.get('id')
                if education_degree_id:  # Update CandidateEducationDegree

                    # CandidateEducationDegree must be recognized
                    can_edu_degree_obj = CandidateEducationDegree.get(education_degree_id)
                    if not can_edu_degree_obj:
                        raise NotFoundError('Candidate education degree not found', custom_error.DEGREE_NOT_FOUND)

                    # CandidateEducationDegree must belong to Candidate
                    if can_edu_degree_obj.candidate_education.candidate_id != candidate_id:
                        raise ForbiddenError('Unauthorized candidate degree', custom_error.DEGREE_FORBIDDEN)

                    # Track all changes made to CandidateEducationDegree
                    track_edits(update_dict=education_degree_dict, table_name='candidate_education_degree',
                                candidate_id=candidate_id, user_id=user_id, query_obj=can_edu_degree_obj)

                    # Update CandidateEducationDegree
                    if education_degree_dict:
                        can_edu_degree_obj.update(**education_degree_dict)

                    # CandidateEducationDegreeBullet
                    for education_degree_bullet in education_degree_bullets:
                        education_degree_bullet_dict = dict(
                            concentration_type=education_degree_bullet['major'].strip()
                            if education_degree_bullet.get('major') else None,
                            comments=education_degree_bullet['comments'].strip()
                            if education_degree_bullet.get('comments') else None
                        )

                        # Remove keys with None values
                        education_degree_bullet_dict = {k: v for k, v in education_degree_bullet_dict.items() if v}

                        # Prevent empty records from being inserted into db
                        if not education_degree_bullet_dict:
                            continue

                        education_degree_bullet_id = education_degree_bullet.get('id')
                        if education_degree_bullet_id:  # Update CandidateEducationDegreeBullet

                            # CandidateEducationDegreeBullet must be recognized
                            can_edu_degree_bullet_obj = CandidateEducationDegreeBullet.get(education_degree_bullet_id)
                            if not can_edu_degree_bullet_obj:
                                raise NotFoundError('Candidate education degree bullet not found',
                                                    error_code=custom_error.DEGREE_BULLET_NOT_FOUND)

                            # CandidateEducationDegreeBullet must belong to Candidate
                            if can_edu_degree_bullet_obj.candidate_education_degree. \
                                    candidate_education.candidate_id != candidate_id:
                                raise ForbiddenError('Unauthorized candidate degree bullet',
                                                     error_code=custom_error.DEGREE_BULLET_FORBIDDEN)

                            # Track all changes made to CandidateEducationDegreeBullet
                            track_edits(update_dict=education_degree_bullet_dict,
                                        table_name='candidate_education_degree_bullet',
                                        candidate_id=candidate_id, user_id=user_id,
                                        query_obj=can_edu_degree_bullet_obj)

                            can_edu_degree_bullet_obj.update(**education_degree_bullet_dict) # Update
                        else:   # Add CandidateEducationDegreeBullet
                            education_degree_bullet_dict.update(dict(added_time=added_datetime))
                            # Prevent duplicate entries
                            if not does_education_degree_bullet_exist(candidate_educations,
                                                                      education_degree_bullet_dict):
                                db.session.add(CandidateEducationDegreeBullet(**education_degree_bullet_dict))

                                if is_updating:  # Track all updates
                                    track_edits(update_dict=education_degree_bullet_dict,
                                                table_name='candidate_education_degree_bullet',
                                                candidate_id=candidate_id, user_id=user_id)

                else:   # Add CandidateEducationDegree
                    education_degree_dict.update(dict(candidate_education_id=education_id))
                    candidate_education_degree_id = get_education_degree_if_exists(candidate_educations,
                                                                                   education_degree_dict)
                    if not candidate_education_degree_id:
                        candidate_education_degree = CandidateEducationDegree(**education_degree_dict)
                        db.session.add(candidate_education_degree)
                        db.session.flush()
                        candidate_education_degree_id = candidate_education_degree.id

                        if is_updating:  # Track all updates
                            track_edits(update_dict=education_degree_dict, table_name='candidate_education_degree',
                                        candidate_id=candidate_id, user_id=user_id)

                    # Add CandidateEducationDegreeBullets
                    education_degree_bullets = education_degree.get('bullets') or []
                    for education_degree_bullet in education_degree_bullets:
                        education_degree_bullet_dict = dict(
                            concentration_type=education_degree_bullet['major'].strip()
                            if education_degree_bullet.get('major') else None,
                            comments=education_degree_bullet['comments'].strip()
                            if education_degree_bullet.get('comments') else None
                        )
                        # Remove keys with None values
                        education_degree_bullet_dict = {k: v for k, v in education_degree_bullet_dict.items() if v}

                        # Prevent empty records from being inserted into db
                        if not education_degree_bullet_dict:
                            continue

                        education_degree_bullet_dict.update(dict(
                            added_time=added_datetime, candidate_education_degree_id=candidate_education_degree_id))
                        db.session.add(CandidateEducationDegreeBullet(**education_degree_bullet_dict))

        else:  # Add
            # CandidateEducation
            # TODO: resume_id to be removed once all tables have been added & migrated
            education_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id, added_time=added_datetime,
                                       list_order=education.get('list_order') or 1))
            # Prevent duplicate entries
            education_id = get_education_if_exists(candidate_educations, education_dict, education_degrees)
            if not education_id:
                candidate_education = CandidateEducation(**education_dict)
                db.session.add(candidate_education)
                db.session.flush()
                education_id = candidate_education.id

                if is_updating:  # Track all updates
                    track_edits(update_dict=education_dict, table_name='candidate_education',
                                candidate_id=candidate_id, user_id=user_id)

            # CandidateEducationDegree
            for education_degree in education_degrees:
                degree_type=education_degree['type'].strip() if education_degree.get('type') else None
                degree_title=education_degree['title'].strip() if education_degree.get('title') else None
                education_degree_dict = dict(
                    list_order=education_degree.get('list_order'),
                    degree_type=degree_type,
                    degree_title=degree_title,
                    start_year=education_degree.get('start_year') if degree_title or degree_type else None,
                    start_month=education_degree.get('start_month') if degree_title or degree_type else None,
                    end_year=education_degree.get('end_year') if degree_title or degree_type else None,
                    end_month=education_degree.get('end_month') if degree_title or degree_type else None,
                    gpa_num=education_degree.get('gpa') if degree_title or degree_type else None,
                    classification_type_id=classification_type_id_from_degree_type(education_degree.get('type')),
                    start_time=education_degree.get('start_time') if degree_title or degree_type else None,
                    end_time=education_degree.get('end_time') if degree_title or degree_type else None
                )
                # Remove keys with None values
                education_degree_dict = {k: v for k, v in education_degree_dict.items() if v}

                # Prevent empty records from being inserted into db
                education_degree_bullets = education_degree.get('bullets') or []
                if not education_degree_dict and not education_degree_bullets:
                    continue

                # Update education_degree_dict with added_time
                education_degree_dict['added_time'] = added_datetime

                # Prevent duplicate entries
                candidate_education_degree_id = get_education_degree_if_exists(candidate_educations,
                                                                               education_degree_dict)
                if not candidate_education_degree_id:
                    # Update dict with candidate education ID
                    education_degree_dict['candidate_education_id'] = education_id
                    candidate_education_degree = CandidateEducationDegree(**education_degree_dict)
                    db.session.add(candidate_education_degree)  # Add CandidateEducationDegree
                    db.session.flush()
                    candidate_education_degree_id = candidate_education_degree.id

                    if is_updating:  # Track all updates
                        track_edits(update_dict=education_degree_dict, table_name='candidate_education_degree',
                                    candidate_id=candidate_id, user_id=user_id)

                # CandidateEducationDegreeBullet
                degree_bullets = education_degree.get('bullets') or []
                for degree_bullet in degree_bullets:
                    education_degree_bullet_dict = dict(
                        concentration_type=degree_bullet['major'].strip()
                        if degree_bullet.get('major') else None,
                        comments=degree_bullet['comments'].strip()
                        if degree_bullet.get('comments') else None
                    )

                    # Update education_degree_bullet_dict with candidate_education_degree_id & added_time
                    education_degree_bullet_dict['candidate_education_degree_id'] = candidate_education_degree_id
                    education_degree_bullet_dict['added_time'] = added_datetime

                    # Prevent duplicate entries
                    if not does_education_degree_bullet_exist(candidate_educations, education_degree_bullet_dict):
                        # Add CandidateEducationDegreeBullet
                        db.session.add(CandidateEducationDegreeBullet(**education_degree_bullet_dict))

                        if is_updating:  # Track all updates
                            track_edits(update_dict=education_degree_bullet_dict,
                                        table_name='candidate_education_degree_bullet',
                                        candidate_id=candidate_id, user_id=user_id)


def _add_or_update_work_experiences(candidate, work_experiences, added_time, user_id, is_updating):
    """
    Function will update CandidateExperience and CandidateExperienceBullet
    or create new ones.
    """
    # If any of work_experiences' is_current is True, set all of candidate's experiences' is_current to False
    candidate_id, candidate_experiences = candidate.id, candidate.experiences
    current_year = datetime.datetime.utcnow().year
    if any([experience.get('is_current') for experience in work_experiences]):
        CandidateExperience.set_is_current_to_false(candidate_id=candidate_id)

    # Identify maximum start_year of all provided experiences
    latest_start_date = max(experience.get('start_year') for experience in work_experiences)
    for work_experience in work_experiences:

        start_year = work_experience.get('start_year')

        # end_year of job must be None if it's candidate's current job
        is_current, end_year = work_experience.get('is_current'), work_experience.get('end_year')
        if is_current:
            end_year = None

        if start_year:
            # if end_year is not provided, it will be set to current_year assuming it's the most recent job
            if not end_year and (start_year == latest_start_date):
                end_year = current_year
            # if end_year is not provided, and it's not the latest job, end_year will be latest job's start_year + 1
            elif not end_year and (start_year != latest_start_date):
                end_year = start_year + 1

        country_code = work_experience['country_code'].upper().strip() if work_experience.get('country_code') else None
        subdivision_code = work_experience['subdivision_code'].upper().strip() \
            if work_experience.get('subdivision_code') else None
        experience_dict = dict(
            list_order=work_experience.get('list_order') or 1,
            organization=work_experience['organization'].strip() if work_experience.get('organization') else None,
            position=work_experience['position'].strip() if work_experience.get('position') else None,
            city=work_experience['city'].strip() if work_experience.get('city') else None,
            iso3166_subdivision=subdivision_code,
            iso3166_country=country_code,
            end_month=work_experience.get('end_month') or 1,
            start_year=start_year,
            start_month=work_experience.get('start_month') or 1,
            end_year=end_year,
            is_current=is_current
        )

        experience_id = work_experience.get('id')
        if experience_id:  # Update

            # Remove keys with empty values
            experience_dict = {k: v for k, v in experience_dict.items() if v}

            # CandidateExperience must be recognized
            can_exp_obj = CandidateExperience.get(experience_id)
            if not can_exp_obj:
                raise InvalidUsage('Candidate experience not found', custom_error.EXPERIENCE_NOT_FOUND)

            # CandidateExperience must belong to Candidate
            if can_exp_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate experience', custom_error.EXPERIENCE_FORBIDDEN)

            # Add up candidate's total months of experience
            update_total_months_experience(candidate, experience_dict, can_exp_obj)

            # Track all changes made to CandidateExperience
            track_edits(update_dict=experience_dict, table_name='candidate_experience',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_exp_obj)

            # Update CandidateExperience
            can_exp_obj.update(**experience_dict)

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('bullets') or []
            for experience_bullet in experience_bullets:
                experience_bullet_dict = dict(
                    list_order=experience_bullet.get('list_order'),
                    description=experience_bullet['description'].strip() if experience_bullet.get(
                        'description') else None
                )

                # Remove keys with None values
                experience_bullet_dict = {k: v for k, v in experience_bullet_dict.items() if v}

                # Prevent empty data from being inserted into db
                if not experience_bullet_dict:
                    continue

                experience_bullet_id = experience_bullet.get('id')
                if experience_bullet_id:  # Update

                    # CandidateExperienceBullet must be recognized
                    can_exp_bullet_obj = CandidateExperienceBullet.get(experience_bullet_id)
                    if not can_exp_bullet_obj:
                        raise InvalidUsage('Candidate experience bullet not found',
                                           error_code=custom_error.EXPERIENCE_BULLET_NOT_FOUND)

                    # CandidateExperienceBullet must belong to Candidate
                    if can_exp_bullet_obj.candidate_experience.candidate_id != candidate_id:
                        raise ForbiddenError('Unauthorized candidate experience bullet',
                                             error_code=custom_error.EXPERIENCE_BULLET_FORBIDDEN)

                    # Track all changes made to CandidateExperienceBullet
                    track_edits(update_dict=experience_bullet_dict, table_name='candidate_experience_bullet',
                                candidate_id=candidate_id, user_id=user_id, query_obj=can_exp_bullet_obj)

                    can_exp_bullet_obj.update(**experience_bullet_dict)
                else:  # Add
                    # Update experience_bullet_dict with added_time
                    experience_bullet_dict['added_time'] = added_time
                    experience_bullet_dict.update(dict(candidate_experience_id=experience_id))
                    db.session.add(CandidateExperienceBullet(**experience_bullet_dict))

                    if is_updating:  # Track all updates
                        track_edits(update_dict=experience_bullet_dict, table_name='candidate_experience_bullet',
                                    candidate_id=candidate_id, user_id=user_id)

        else:  # Add
            experience_dict.update(dict(candidate_id=candidate_id, added_time=added_time, resume_id=candidate_id))
            # Prevent duplicate entries
            experience_id = get_work_experience_if_exists(candidate_experiences, experience_dict)
            if not experience_id:
                experience = CandidateExperience(**experience_dict)
                db.session.add(experience)
                db.session.flush()
                experience_id = experience.id

                # Add up candidate's total months of experience
                update_total_months_experience(candidate, experience_dict)

                if is_updating:  # Track all updates
                    track_edits(update_dict=experience_dict, table_name='candidate_experience',
                                candidate_id=candidate_id, user_id=user_id)

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('bullets') or []
            for experience_bullet in experience_bullets:
                experience_bullet_dict = dict(
                    list_order=experience_bullet.get('list_order'),
                    description=experience_bullet['description'].strip() if experience_bullet.get(
                        'description') else None
                )
                # Remove keys with None values
                experience_bullet_dict = {k: v for k, v in experience_bullet_dict.items() if v}

                # Prevent empty data from being inserted into db
                if not experience_bullet_dict:
                    continue

                # Prevent duplicate entries
                if not does_experience_bullet_exist(candidate_experiences, experience_bullet_dict):
                    # Update experience_bullet_dict with experience_id and added_time
                    experience_bullet_dict['candidate_experience_id'] = experience_id
                    experience_bullet_dict['added_time'] = added_time
                    db.session.add(CandidateExperienceBullet(**experience_bullet_dict))

                    if is_updating:  # Track all updates
                        track_edits(update_dict=experience_bullet_dict, table_name='candidate_experience_bullet',
                                    candidate_id=candidate_id, user_id=user_id)


def _add_or_update_work_preference(candidate_id, work_preference, user_id):
    """
    Function will update CandidateWorkPreference or create a new one.
    """
    work_preference_dict = dict(
        relocate=work_preference.get('relocate') or False,
        authorization=work_preference['authorization'].strip() if work_preference.get('authorization') else None,
        telecommute=work_preference.get('telecommute') or False,
        travel_percentage=work_preference.get('travel_percentage'),
        hourly_rate=work_preference.get('hourly_rate'),
        salary=work_preference.get('salary'),
        tax_terms=work_preference['employment_type'].strip() if work_preference.get('employment_type') else None,
        security_clearance=work_preference.get('security_clearance') or False,
        third_party=work_preference.get('third_party') or False
    )

    # Remove empty values from update_dict
    work_preference_dict = {k: v for k, v in work_preference_dict.items() if v}

    work_preference_id = work_preference.get('id')
    if work_preference_id:  # Update

        # CandidateWorkPreference must be recognized
        can_work_pref_obj = CandidateWorkPreference.get(work_preference_id)
        if not can_work_pref_obj:
            raise NotFoundError('Candidate work preference not found', custom_error.WORK_PREF_NOT_FOUND)

        # CandidateWorkPreference must belong to Candidate
        if can_work_pref_obj.candidate_id != candidate_id:
            raise ForbiddenError('Unauthorized candidate work preference', custom_error.WORK_PREF_FORBIDDEN)

        # Track all updates
        track_edits(update_dict=work_preference_dict, table_name='candidate_work_preference',
                    candidate_id=candidate_id, user_id=user_id, query_obj=can_work_pref_obj)

        # Update
        can_work_pref_obj.update(**work_preference_dict)

    else:  # Add
        # Only 1 CandidateWorkPreference is permitted for each Candidate
        if CandidateWorkPreference.get_by_candidate_id(candidate_id):
            raise InvalidUsage("Candidate work preference already exists", custom_error.WORK_PREF_EXISTS)

        work_preference_dict.update(dict(candidate_id=candidate_id))
        db.session.add(CandidateWorkPreference(**work_preference_dict))


def _add_or_update_emails(candidate_id, emails, user_id, is_updating):
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
        email_label = 'Primary' if (not emails_has_label and i == 0) else (email.get('label') or '').title()
        email_address = email.get('address')

        email_dict = dict(
            address=email_address,
            email_label_id=EmailLabel.email_label_id_from_email_label(email_label),
            is_default=is_default
        )

        # Remove empty values from email_dict
        email_dict = {k: v for k, v in email_dict.items() if v}

        email_id = email.get('id')
        if email_id:  # Update
            # CandidateEmail must be recognized
            candidate_email_obj = CandidateEmail.get(email_id)
            if not candidate_email_obj:
                raise NotFoundError('Candidate email not found', custom_error.EMAIL_NOT_FOUND)

            # CandidateEmail must belong to Candidate
            if candidate_email_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate email', custom_error.EMAIL_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=email_dict, table_name='candidate_email',
                        candidate_id=candidate_id, user_id=user_id, query_obj=candidate_email_obj)

            # Update CandidateEmail
            candidate_email_obj.update(**email_dict)

        else:  # Add
            email = CandidateEmail.query.filter(CandidateEmail.address == email_address,
                                                CandidateEmail.candidate_id == candidate_id).first()
            # Prevent duplicate entries
            if not email:
                email_dict.update(dict(candidate_id=candidate_id))
                db.session.add(CandidateEmail(**email_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=email_dict, table_name='candidate_email',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_phones(candidate, phones, user_id, is_updating):
    """
    Function will update CandidatePhone or create new one(s).
    """
    # If any of phones' is_default is True, set all of candidate's phones' is_default to False
    candidate_id, candidate_phones = candidate.id, candidate.phones
    if any([phone.get('is_default') for phone in phones]):
        CandidatePhone.set_is_default_to_false(candidate_id)

    phones_has_label = any([phone.get('label') for phone in phones])
    phones_has_default = any([phone.get('is_default') for phone in phones])
    for i, phone in enumerate(phones):

        # If there's no is_default, the first phone should be default
        is_default = i == 0 if not phones_has_default else phone.get('is_default')
        # If there's no label, the first phone's label will be 'Home', rest will be 'Other'
        phone_label = 'Home' if (not phones_has_label and i == 0) else (phone.get('label') or '').strip().title()
        # Format phone number
        value = (phone.get('value') or '').strip()
        iso3166_country_code = CachedData.country_codes[0] if CachedData.country_codes else None
        phone_number_obj = parse_phone_number(value, iso3166_country_code=iso3166_country_code) if value else None
        """
        :type phone_number_obj: PhoneNumber
        """

        # phonenumbers.format() will append "+None" if phone_number_obj.country_code is None
        if not phone_number_obj.country_code:
            value = phone_number_obj.national_number
        else:
            value = phonenumbers.format_number(phone_number_obj, phonenumbers.PhoneNumberFormat.E164)

        # Clear CachedData's country_codes to prevent aggregating unnecessary data
        CachedData.country_codes = []
        # if value:
        phone_dict = dict(
            value=value,
            extension=phone_number_obj.extension if phone_number_obj else None,
            phone_label_id=PhoneLabel.phone_label_id_from_phone_label(phone_label),
            is_default=is_default
        )

        # Remove keys with empty values
        phone_dict = {k: v for k, v in phone_dict.items() if v}

        # Prevent adding empty records to db
        if not phone_dict:
            continue

        candidate_phone_id = phone.get('id')
        if candidate_phone_id:  # Update

            # CandidatePhone must be recognized
            can_phone_obj = CandidatePhone.get(candidate_phone_id)
            if not can_phone_obj:
                raise NotFoundError('Candidate phone not found', custom_error.PHONE_NOT_FOUND)

            # CandidatePhone must belong to Candidate
            if can_phone_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate phone', custom_error.PHONE_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=phone_dict, table_name='candidate_phone',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_phone_obj)

            # Update CandidatePhone
            can_phone_obj.update(**phone_dict)

        else:  # Add
            if value:  # Value is required for creating phone
                phone_dict.update(dict(candidate_id=candidate_id))
                # Prevent duplicate entries
                if not does_phone_exist(candidate_phones, phone_dict):
                    db.session.add(CandidatePhone(**phone_dict))

                    if is_updating:  # Track all updates
                        track_edits(update_dict=phone_dict, table_name='candidate_phone',
                                    candidate_id=candidate_id, user_id=user_id)


def _add_or_update_military_services(candidate, military_services, user_id, is_updating):
    """
    Function will update CandidateMilitaryService or create new one(s).
    """
    candidate_id, candidate_military_services = candidate.id, candidate.military_services
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
            iso3166_country=military_service['country_code'].upper() if military_service.get('country_code') else None,
            service_status=military_service['status'].strip() if military_service.get('status') else None,
            highest_rank=military_service['highest_rank'] if military_service.get('highest_rank') else None,
            highest_grade=military_service['highest_grade'].strip() if military_service.get('highest_grade') else None,
            branch=military_service['branch'].strip() if military_service.get('branch') else None,
            comments=military_service['comments'].strip() if military_service.get('comments') else None,
            from_date=from_date,
            to_date=to_date
        )

        # Remove keys with empty values
        military_service_dict = {k: v for k, v in military_service_dict.items() if v}

        # Prevent adding empty data to db
        if not military_service_dict:
            continue

        military_service_id = military_service.get('id')
        if military_service_id:  # Update

            # CandidateMilitaryService must be recognized
            can_military_service_obj = CandidateMilitaryService.get(military_service_id)
            if not can_military_service_obj:
                raise NotFoundError('Candidate military service not found', custom_error.MILITARY_NOT_FOUND)

            # CandidateMilitaryService must belong to Candidate
            if can_military_service_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate military service', custom_error.MILITARY_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=military_service_dict, table_name='candidate_military_service',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_military_service_obj)

            # Update CandidateMilitaryService
            can_military_service_obj.update(**military_service_dict)

        else:  # Add
            military_service_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id))
            if not does_military_service_exist(candidate_military_services, military_service_dict):
                db.session.add(CandidateMilitaryService(**military_service_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=military_service_dict, table_name='candidate_military_service',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_preferred_locations(candidate, preferred_locations, user_id, is_updating):
    """
    Function will update CandidatePreferredLocation or create a new one.
    """
    candidate_id, candidate_preferred_locations = candidate.id, candidate.preferred_locations
    for preferred_location in preferred_locations:

        country_code = preferred_location['country_code'].strip().upper() \
            if preferred_location.get('country_code') else None
        subdivision_code = preferred_location['subdivision_code'].strip().upper() \
            if preferred_location.get('subdivision_code') else None
        preferred_location_dict = dict(
            address=preferred_location['address'].strip() if preferred_location.get('address') else None,
            iso3166_country=country_code,
            iso3166_subdivision=subdivision_code,
            city=preferred_location['city'].strip() if preferred_location.get('city') else None,
            region=preferred_location['state'].strip() if preferred_location.get('state') else None,
            zip_code=sanitize_zip_code(preferred_location.get('zip_code'))
        )

        # Remove keys with empty values
        preferred_location_dict = {k: v for k, v in preferred_location_dict.items() if v}

        # Prevent inserting empty records into db
        if not preferred_location_dict:
            continue

        preferred_location_id = preferred_location.get('id')
        if preferred_location_id:  # Update
            # CandidatePreferredLocation must be recognized
            can_preferred_location_obj = CandidatePreferredLocation.get(preferred_location_id)
            if not can_preferred_location_obj:
                raise NotFoundError('Candidate preferred location not found', custom_error.PREFERRED_LOCATION_NOT_FOUND)

            # CandidatePreferredLocation must belong to Candidate
            if can_preferred_location_obj.candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate preferred location',
                                     error_code=custom_error.PREFERRED_LOCATION_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=preferred_location_dict, table_name='candidate_preferred_location',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_preferred_location_obj)

            # Update CandidatePreferredLocation
            can_preferred_location_obj.update(**preferred_location_dict)

        else:  # Add
            preferred_location_dict.update(dict(candidate_id=candidate_id))
            # Prevent duplicate entries
            if not does_preferred_location_exist(candidate_preferred_locations, preferred_location_dict):
                db.session.add(CandidatePreferredLocation(**preferred_location_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=preferred_location_dict, table_name='candidate_preferred_location',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_skills(candidate, skills, added_time, user_id, is_updating):
    """
    Function will update CandidateSkill or create new one(s).
    """
    candidate_id = candidate.id
    for skill in skills:

        # Convert ISO 8601 date format to datetime object
        last_used_date = skill.get('last_used_date')
        if last_used_date:
            last_used_date = dateutil.parser.parse(skill.get('last_used_date'))

        skill_id = skill.get('id')
        description = skill['name'].strip() if skill.get('name') else None

        # total_months & last_used will only be retrieved if skill-name (description) or skill_id is provided
        skill_dict = dict(
            list_order=skill.get('list_order'),
            description=description,
            total_months=skill.get('months_used') if (description or skill_id) else None,
            last_used=last_used_date if (description or skill_id) else None
        )

        # Remove keys with empty values
        skill_dict = {k: v for k, v in skill_dict.items() if v}

        # Prevent adding records if empty dict
        if not skill_dict:
            continue

        if skill_id:  # Update
            # CandidateSkill must be recognized
            can_skill_obj = CandidateSkill.get(skill_id)
            if not can_skill_obj:
                raise NotFoundError('Candidate skill not found', custom_error.SKILL_NOT_FOUND)

            # CandidateSkill must belong to Candidate
            if can_skill_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate skill', custom_error.SKILL_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=skill_dict, table_name='candidate_skill',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_skill_obj)

            # Update CandidateSkill
            can_skill_obj.update(**skill_dict)

        else:  # Add
            skill_dict.update(dict(candidate_id=candidate_id, resume_id=candidate_id, added_time=added_time))
            # Prevent duplicate entries
            if not does_skill_exist(candidate.skills, skill_dict):
                db.session.add(CandidateSkill(**skill_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=skill_dict, table_name='candidate_skill',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_social_networks(candidate, social_networks, user_id, is_updating):
    """
    Function will update CandidateSocialNetwork or create new one(s).
    """
    candidate_id, candidate_sns = candidate.id, candidate.social_networks
    for social_network in social_networks:

        social_network_dict = dict(
            social_network_id=social_network_id_from_name(social_network['name'].strip()),
            social_profile_url=social_network['profile_url'].strip()
        )

        social_network_id = social_network.get('id')
        if social_network_id:  # Update

            # CandidateSocialNetwork must be recognized
            can_sn_obj = CandidateSocialNetwork.get(social_network_id)
            if not can_sn_obj:
                raise NotFoundError(error_message='Candidate social network not found',
                                    error_code=custom_error.SOCIAL_NETWORK_NOT_FOUND)

            # CandidateSocialNetwork must belong to Candidate
            if can_sn_obj.candidate_id != candidate_id:
                raise ForbiddenError(error_message='Unauthorized candidate social network',
                                     error_code=custom_error.SOCIAL_NETWORK_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=social_network_dict, table_name='candidate_social_network',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_sn_obj)

            can_sn_obj.update(**social_network_dict)

        else:  # Add
            social_network_dict.update(dict(candidate_id=candidate_id))
            # Prevent duplicate entries
            if not does_social_network_exist(candidate_sns, social_network_dict):
                db.session.add(CandidateSocialNetwork(**social_network_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=social_network_dict, table_name='candidate_social_network',
                                candidate_id=candidate_id, user_id=user_id)


def _add_or_update_candidate_talent_pools(candidate_id, talent_pool_ids, is_creating, is_updating):

    talent_pools_to_be_added = talent_pool_ids.get('add')
    talent_pools_to_be_deleted = talent_pool_ids.get('delete')

    if is_creating or is_updating and talent_pools_to_be_added:
        for talent_pool_id in talent_pools_to_be_added:
            talent_pool = TalentPool.query.get(int(talent_pool_id))
            if not talent_pool:
                raise NotFoundError("TalentPool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError("TalentPool and logged in user belong to different domains")

            if not TalentPoolGroup.get(talent_pool_id, request.user.user_group_id):
                raise ForbiddenError("TalentPool %s doesn't belong to UserGroup %s of logged-in "
                                        "user" % (talent_pool_id, request.user.user_group_id))

            # In case candidate was web-hidden, the recreated with the same talent-pool-id
            talent_pool_candidate = TalentPoolCandidate.get(candidate_id, talent_pool_id)
            if talent_pool_candidate and is_updating:
                pass
            else:
                # Prevent duplicate entries
                if not TalentPoolCandidate.get(candidate_id, talent_pool_id):
                    db.session.add(TalentPoolCandidate(candidate_id=candidate_id, talent_pool_id=talent_pool_id))

    if is_updating and talent_pools_to_be_deleted:
        for talent_pool_id in talent_pools_to_be_deleted:
            talent_pool = TalentPool.query.get(int(talent_pool_id))
            if not talent_pool:
                raise NotFoundError("TalentPool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError("TalentPool and logged in user belong to different domains")

            if not TalentPoolGroup.get(talent_pool_id, request.user.user_group_id):
                raise ForbiddenError("TalentPool %s doesn't belong to UserGroup %s of logged-in "
                                        "user" % (talent_pool_id, request.user.user_group_id))

            talent_pool_candidate = TalentPoolCandidate.get(candidate_id, talent_pool_id)
            if not talent_pool_candidate:
                raise InvalidUsage("Candidate %s doesn't belong to TalentPool %s" %
                                   (candidate_id, talent_pool_id))
            else:
                db.session.delete(talent_pool_candidate)


def get_search_params_of_smartlists(smartlist_ids):
    """
    This method will return list of search_params of smartlists
    :param smartlist_ids: IDs of smartlists
    :return:
    """
    if not isinstance(smartlist_ids, list):
        smartlist_ids = [smartlist_ids]

    smartlists = Smartlist.query.with_entities(Smartlist.id, Smartlist.search_params).filter(
            Smartlist.id.in_(smartlist_ids)).all()

    search_params = []

    for smartlist_id, smartlist_search_params in smartlists:
        try:
            if smartlist_search_params and json.loads(smartlist_search_params):
                search_params.append(json.loads(smartlist_search_params))
        except Exception as e:
            raise InvalidUsage(error_message="Search params of smartlist %s are in bad format "
                                             "because: %s" % (smartlist_id, e.message))

    logger.info("Search Params for smartlist_ids %s are following: %s" % (smartlist_ids, search_params))

    return search_params


def update_total_months_experience(candidate, experience_dict=None, candidate_experience=None, deleted=False):
    """
    Function will update candidate's total months of experiences.
    Edge cases:
        i. If one of candidate's experiences is removed, its total months will be subtracted from
           candidate's current total-months-of-experience
       ii. If an existing candidate experience's dates are updated; candidate.total_months_experience
            will be updated accordingly
      iii. Candidate's total months of experience will simply be aggregated if a new experience has been added

    This function does not effect candidate's total months of experience in case all of candidate's
      experiences have been removed. That functionality is accounted for in CandidateExperienceResource/delete()
    :type candidate:  Candidate
    :type experience_dict:  dict[str]
    :type candidate_experience:  CandidateExperience
    :type deleted:  bool
    """
    # Starting point for total_months_experience
    total_months_experience = 0

    # This is to prevent code from breaking in case of experience_dict.get(key)
    if experience_dict is None:
        experience_dict = {}

    if candidate.total_months_experience is None:
        candidate.total_months_experience = 0

    start_year, end_year = experience_dict.get('start_year'), experience_dict.get('end_year')
    start_month, end_month = experience_dict.get('start_month'), experience_dict.get('end_month')

    if start_year and end_year:
        total_months_experience = (end_year - start_year) * 12 + (end_month - start_month)

    if candidate_experience:
        previous_start_year, previous_end_year = candidate_experience.start_year, candidate_experience.end_year
        previous_start_month, previous_end_month = candidate_experience.start_month, candidate_experience.end_month

        if deleted:  # A CandidateExperience has been removed
            total_months_experience = - (previous_end_year - previous_start_year) * 12 + \
                                      (previous_end_month - previous_start_month)

        else:  # An existing CandidateExperience's dates have been updated
            if start_year and end_year:
                total_months_experience = ((end_year - start_year) * 12 + (end_month - start_month) -
                    (previous_end_year - previous_start_year) * 12 + (previous_end_month - previous_start_month))

    candidate.total_months_experience += total_months_experience
    return


class CachedData(object):
    """
    This class will contain data that may be required by other functions but should be cleared
      when its data is no longer needed
    """
    country_codes = []
