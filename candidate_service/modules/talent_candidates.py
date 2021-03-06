"""
Helper functions for candidate CRUD operations and tracking edits made to the Candidate
"""
# Standard libraries
import datetime
import hashlib
import re
import urlparse
from datetime import date

import dateutil.parser
import phonenumbers
import pycountry
import simplejson as json
from flask import request, has_request_context
from nameparser import HumanName
from candidate_service.candidate_app import logger
from candidate_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from candidate_service.common.geo_services.geo_coordinates import get_coordinates
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.candidate import (
    Candidate, CandidateEmail, CandidatePhone, CandidateWorkPreference, CandidatePreferredLocation,
    CandidateAddress, CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField, CandidateSocialNetwork,
    SocialNetwork, CandidateEducationDegreeBullet, CandidateExperienceBullet, ClassificationType,
    CandidatePhoto, PhoneLabel, EmailLabel, CandidateSubscriptionPreference
)
from candidate_service.modules.mergehub import MergeHub, GtDict
from candidate_service.modules.tags import create_tags, update_candidate_tags
from candidate_service.common.models.candidate_edit import CandidateView
from candidate_service.common.models.db import db
from candidate_service.common.models.email_campaign import EmailCampaign, EmailCampaignSend, \
    EmailCampaignSendUrlConversion
from candidate_service.common.models.language import CandidateLanguage
from candidate_service.common.models.misc import AreaOfInterest, UrlConversion, Product, \
    CustomFieldCategory, CustomField
from candidate_service.common.models.smartlist import Smartlist
from candidate_service.common.models.talent_pools_pipelines import TalentPoolCandidate, TalentPool, TalentPoolGroup
from candidate_service.common.models.user import User, Permission
from candidate_service.common.utils.datetime_utils import DatetimeUtils
from candidate_service.common.utils.handy_functions import purge_dict
from candidate_service.common.utils.iso_standards import (get_country_name, get_subdivision_name,
                                                          get_country_code_from_name)
from candidate_service.common.utils.talent_s3 import get_s3_url
from candidate_service.common.utils.validators import sanitize_zip_code, is_number, parse_phone_number
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.modules.validators import (does_candidate_cf_exist, get_work_experience_if_exists,
                                                  does_experience_bullet_exist,
                                                  do_phones_exist, does_preferred_location_exist, does_skill_exist,
                                                  does_social_network_exist, do_emails_exist, remove_duplicates)
from track_changes import track_edits, track_areas_of_interest_edits


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
        if (not has_request_context()) or Permission.PermissionNames.CAN_GET_CANDIDATE_SOCIAL_PROFILE in request.user_permissions:
            social_networks = candidate_social_networks(candidate=candidate)
        else:
            raise ForbiddenError("You are not authorized to get social networks of this candidate")

    history = None
    if get_all_fields or 'contact_history' in fields:
        if (not has_request_context()) or Permission.PermissionNames.CAN_GET_CANDIDATE_CONTACT_HISTORY in request.user_permissions:
            history = candidate_contact_history(candidate=candidate)
        else:
            raise ForbiddenError("You are not authorized to get contact history of this candidate")

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

    # Get candidate's source product information
    source_product_info = None
    source_product_id = candidate.source_product_id
    if source_product_id:
        source_product = Product.get(source_product_id)
        source_product_info = source_product.to_json()
    return {
        'id': candidate_id,
        'owner_id': candidate.user_id,
        'status_id': candidate.candidate_status_id,
        'first_name': candidate.first_name,
        'middle_name': candidate.middle_name,
        'last_name': candidate.last_name,
        'full_name': full_name,
        'created_at_datetime': created_at_datetime,
        'updated_at_datetime': DatetimeUtils.utc_isoformat(candidate.updated_datetime),
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
        'resume_url': resume_url,
        'source_id': candidate.source_id,
        'source_detail': candidate.source_detail,
        'source_product_id': source_product_id,
        'source_product_info': source_product_info,
        'summary': candidate.summary,
        'objective': candidate.objective,
        'title': candidate.title
    }


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
    experiences = db.session.query(CandidateExperience).filter_by(candidate_id=candidate_id). \
        order_by(CandidateExperience.is_current.desc(),
                 CandidateExperience.end_year.desc(),
                 CandidateExperience.start_year.desc(),
                 CandidateExperience.end_month.desc(),
                 CandidateExperience.start_month.desc())
    return [{'id': experience.id,
             'organization': experience.organization,
             'position': experience.position,
             'start_date': date_of_employment(year=experience.start_year, month=experience.start_month or 1),
             'end_date': date_of_employment(year=experience.end_year, month=experience.end_month or 1),
             'start_year': experience.start_year,
             'start_month': experience.start_month,
             'end_year': experience.end_year,
             'end_month': experience.end_month,
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
             'start_year': degree.start_year,
             'start_month': degree.start_month,
             'end_year': degree.end_year,
             'end_month': degree.end_month,
             'gpa': json.dumps(degree.gpa_num, use_decimal=True) if degree.gpa_num else None,
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
    military_services = CandidateMilitaryService.query.\
        filter_by(candidate_id=candidate_id).\
        order_by(CandidateMilitaryService.to_date.desc())

    services = []
    for service in military_services:
        # format inputs
        from_date, to_date = None, None
        service_from_date = service.from_date
        service_to_date = service.to_date
        service_start_year = service.start_year
        service_start_month = service.start_month
        service_end_year = service.end_year
        service_end_month = service.end_month

        from_date_start_year, from_date_start_month = None, None
        if service_from_date:
            from_date = str(service_from_date.date())
            from_date_start_year = service_from_date.year
            from_date_start_month = service_from_date.month

        to_date_end_year, to_date_end_month = None, None
        if service_to_date:
            to_date = str(service_to_date.date())
            to_date_end_year = service_to_date.year
            to_date_end_month = service_to_date.month

        start_year = service_start_year or from_date_start_year
        start_month = service_start_month or from_date_start_month
        end_year = service_end_year or to_date_end_year
        end_month = service_end_month or to_date_end_month

        services.append(dict(
            id=service.id,
            branch=service.branch,
            status=service.service_status,
            highest_grade=service.highest_grade,
            highest_rank=service.highest_rank,
            from_date=from_date,
            to_date=to_date,
            start_year=start_year,
            start_month=start_month,
            end_year=end_year,
            end_month=end_month,
            country=get_country_name(service.iso3166_country),
            comments=service.comments
        ))

    return services


def candidate_custom_fields(candidate):
    """
    Function will return custom field information linked to the candidate, which include:
      - candidate's domain custom field ID
      - candidate's custom field value
      - candidate's domain custom field subcategory
    :type candidate:    Candidate
    :rtype              [dict]
    """

    candidate_custom_fields_data = []

    for candidate_custom_field in CandidateCustomField.query.filter_by(candidate_id=candidate.id):
        # TODO: Product has decided to punt cf-subcategories for later -Amir
        # subcategory_id = candidate_custom_field.custom_field_subcategory_id
        # if subcategory_id:
        #     sub_cat = CustomFieldSubCategory.get(subcategory_id)  # type: CustomFieldSubCategory
        #     sub_cat_data = {'id': sub_cat.id, 'name': sub_cat.name}
        # else:
        #     sub_cat_data = None

        candidate_custom_fields_data.append(
            {
                'id': candidate_custom_field.id,
                'custom_field_id': candidate_custom_field.custom_field_id,
                'value': candidate_custom_field.value,
                'created_at_datetime': candidate_custom_field.added_time.isoformat(),
                'custom_field_category_id': candidate_custom_field.custom_field_category_id
                # 'custom_field_subcategory': sub_cat_data
            }
        )

    return candidate_custom_fields_data


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

        email_campaign = EmailCampaign.get(email_campaign_send.campaign_id)
        event_datetime = email_campaign_send.sent_datetime
        event_type = ContactHistoryEvent.EMAIL_SEND

        timeline.insert(0, dict(id=hashlib.md5('{}{}{}'.format(str(event_datetime), event_type, str(email_campaign.id)))
                                .hexdigest(),
                                email_campaign_id=email_campaign.id,
                                event_datetime=email_campaign_send.sent_datetime,
                                event_type=ContactHistoryEvent.EMAIL_SEND,
                                campaign_name=email_campaign.name))

    # Get email campaign sends if its url was clicked by the candidate
    open_email_campaign_sends = EmailCampaignSend.get_candidate_open_email_campaign_send(int(candidate.id))

    for open_email_campaign_send_ in open_email_campaign_sends:
        # Get email campaign send's url conversion
        url_conversion_id = EmailCampaignSendUrlConversion.query.filter(
            EmailCampaignSendUrlConversion.email_campaign_send_id == open_email_campaign_send_.id
        ).first().url_conversion_id
        url_conversion = UrlConversion.get(url_conversion_id)

        event_datetime = url_conversion.last_hit_time
        event_type = ContactHistoryEvent.EMAIL_OPEN

        timeline.append(dict(
            id=hashlib.md5('{}{}{}'.format(str(event_datetime), event_type, str(email_campaign.id))).hexdigest(),
            email_campaign_id=email_campaign.id,
            campaign_name=email_campaign.name,
            event_type=event_type,
            event_datetime=event_datetime
        ))

    timeline_with_valid_event_datetime = filter(lambda entry: isinstance(entry['event_datetime'],
                                                                         datetime.datetime), timeline)
    timeline_with_null_event_datetime = filter(lambda entry: entry['event_datetime'] is None, timeline)

    # Sort events by datetime and convert all date-times to ISO format
    timeline = sorted(timeline_with_valid_event_datetime, key=lambda entry: entry['event_datetime'], reverse=True)
    for event in timeline:
        event['event_datetime'] = event['event_datetime'].isoformat()

    timeline += timeline_with_null_event_datetime

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
    assert isinstance(candidate_id, (int, long))

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
        source_detail=None,
        source_product_id=None,
        objective=None,
        summary=None,
        talent_pool_ids=None,
        resume_url=None,
        resume_text=None,
        tags=None,
        title=None
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

    :type   user_id:                int|long
    :type   is_creating:            bool
    :type   is_updating:            bool
    :type   candidate_id:           int
    :type   first_name:             basestring
    :type   last_name:              basestring
    :type   middle_name:            basestring
    :type   formatted_name:         str
    :type   status_id:              int
    :type   emails:                 list
    :type   phones:                 list
    :type   addresses:              list
    :type   educations:             list
    :type   military_services:      list
    :type   areas_of_interest:      list
    :type   custom_fields:          list
    :type   social_networks:        list
    :type   work_experiences:       list
    :type   work_preference:        dict
    :type   preferred_locations:    list
    :type   skills:                 list
    :type   dice_social_profile_id: int
    :type   dice_profile_id:        int
    :type   added_datetime:         str
    :param  source_id:              Source of candidate's intro, e.g. job-fair
    :type   source_product_id       int
    :type   source_id:              int
    :type   objective:              basestring
    :type   summary:                basestring
    :type   talent_pool_ids:        dict
    :type   resume_url              basestring
    :type   resume_text             basestring
    :type   tags                    list
    :type   title                   basestring
    :rtype                          dict
    """
    # Format inputs
    added_datetime = added_datetime or datetime.datetime.utcnow()
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
                               additional_error_info={'id': candidate_id_from_dice_profile})

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
        candidate_id = _update_candidate(first_name, middle_name, last_name, formatted_name,
                                         objective, summary, candidate_id, user_id, resume_url,
                                         source_id, source_detail, source_product_id, status_id,
                                         resume_text, title)
    else:  # Add Candidate
        candidate_id = _add_candidate(first_name, middle_name, last_name, formatted_name,
                                      added_datetime, status_id, user_id, dice_profile_id,
                                      dice_social_profile_id, source_id, source_detail,
                                      source_product_id, objective, summary, resume_url,
                                      resume_text, title)

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
        _add_or_update_emails(candidate, emails, user_id, is_updating)

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
        if (is_creating and Permission.PermissionNames.CAN_ADD_CANDIDATE_SOCIAL_PROFILE in request.user_permissions) or (
                    is_updating and Permission.PermissionNames.CAN_EDIT_CANDIDATE_SOCIAL_PROFILE in request.user_permissions):
            _add_or_update_social_networks(candidate, social_networks, user_id, is_updating)
        else:
            raise ForbiddenError("You are not authorized to add/modify social networks of this candidate")

    if tags:
        if is_creating:
            create_tags(candidate_id, tags)
        else:
            update_candidate_tags(candidate_id, tags)

    # Commit to database after all insertions/updates are executed successfully
    db.session.commit()
    return dict(candidate_id=candidate_id)


def get_fullname_from_name_fields(first_name, middle_name, last_name):
    """
    Function will concatenate names if any, otherwise will return empty string
    :rtype: str
    """
    full_name = re.sub(' +', ' ', '%s %s %s' % (first_name, middle_name, last_name))
    # remove 'None's, get rid of double space between first and last if middle was not provided, and strip outer spaces
    return full_name.replace('None', '').replace('  ', ' ').strip()


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


def social_network_id_from_name(name=None):
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


def _update_candidate(first_name, middle_name, last_name, formatted_name, objective, summary,
                      candidate_id, user_id, resume_url, source_id, source_detail,
                      source_product_id, candidate_status_id, resume_text, title):
    """
    Function will update Candidate's primary information.
    Candidate's Primary information include:
      - first name, middle name, last name, status ID, source ID, objective, summary, and resume url

    Caveats:
        - status_id, source_id, objective, summary, and resume_url will be deleted if their
            respective values are NULL.
        - candidate's full name, first name, middle name, and/or last name will be removed
            if their respective values are an empty string. NULL values will be ignored.

    :return:  Candidate ID
    :rtype: int | long
    """
    # If formatted name is provided, must also update first name, middle name, and last name
    if formatted_name:
        parsed_names_object = HumanName(formatted_name)
        first_name = parsed_names_object.first
        middle_name = parsed_names_object.middle
        last_name = parsed_names_object.last

    update_dict = {
        'objective': objective, 'summary': summary, 'filename': resume_url,
        'source_id': source_id, 'source_detail': source_detail,
        'candidate_status_id': candidate_status_id,
        'source_product_id': source_product_id, 'resume_text': resume_text,
        'title': title
    }

    # Strip each key-value and remove keys with empty-string-values
    update_dict = purge_dict(update_dict, remove_empty_strings_only=True)

    # Update request dict with candidate names
    # Candidate name(s) will be removed if empty string is provided; None values will be ignored
    names_dict = dict(
        first_name=first_name, middle_name=middle_name, last_name=last_name,
        formatted_name=formatted_name or format_full_name(first_name, middle_name, last_name)
    )
    # Only remove keys with None values; keys with empty strings will be used for deleting
    # For example, if first_name = '', candidate's first name will be removed from db
    names_dict = {k: v for k, v in names_dict.items() if v is not None}

    # Add names' data to update_dict if at least one of name is provided
    if not all(v is None for v in names_dict.values()):
        update_dict.update(**names_dict)

    # Candidate will not be updated if update_dict is empty
    if not update_dict:
        return candidate_id

    candidate_object = Candidate.get_by_id(candidate_id)

    # Track all edits
    # TODO: some edits are delete
    track_edits(update_dict=update_dict, table_name='candidate', candidate_id=candidate_id,
                user_id=user_id, query_obj=candidate_object)

    # Update
    candidate_object.update(**update_dict)

    return candidate_id


def _add_candidate(first_name, middle_name, last_name, formatted_name,
                   added_time, candidate_status_id, user_id, dice_profile_id,
                   dice_social_profile_id, source_id, source_detail, source_product_id,
                   objective, summary, resume_url, resume_text, title):
    """
    Function will add Candidate and its primary information to db
    All empty values (None or empty strings) will be ignored
    :rtype:  int | long
    """
    # TODO: is_dirty cannot be null. This should be removed once the column is successfully removed.
    add_dict = dict(
        first_name=first_name, middle_name=middle_name, last_name=last_name,
        formatted_name=formatted_name, added_time=added_time,
        candidate_status_id=candidate_status_id, user_id=user_id,
        source_product_id=source_product_id, dice_profile_id=dice_profile_id,
        dice_social_profile_id=dice_social_profile_id, source_id=source_id,
        source_detail=source_detail,  objective=objective, summary=summary,
        filename=resume_url, resume_text=resume_text, title=title, is_dirty=0
    )

    # All empty values must be removed
    add_dict = purge_dict(add_dict)

    candidate = Candidate(**add_dict)
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
    addresses = remove_duplicates(addresses)
    validate_existing_objects(addresses, CandidateAddress, candidate_id, is_updating, 'address',
                              custom_error.ADDRESS_NOT_FOUND, custom_error.ADDRESS_FORBIDDEN)

    formatted_addresses = list(parse_addresses(addresses, candidate, has_default=address_has_default))
    if is_updating:
        mergehub = MergeHub(candidate, dict(addresses=formatted_addresses))
        formatted_addresses = mergehub.merge_addresses()
    for address in [address for address in formatted_addresses if not address.id]:
        db.session.add(CandidateAddress(**address))
        track_edits(update_dict=address, table_name='candidate_address',
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
    # Remove identical data
    custom_field_items = None
    for i, custom_field in enumerate(custom_fields):
        if custom_field.items() == custom_field_items:
            del custom_fields[i]
        else:
            custom_field_items = custom_field.items()

    candidate_id = candidate.id

    for custom_field in custom_fields:  # type: dict

        # In case a list of custom field values are provided, we must remove all white spaces and all empty/none values
        values = filter(None, [value.strip() for value in (custom_field.get('values') or []) if value])

        custom_field_dict = dict(
            values=values or [(custom_field.get('value') or '').strip()],
            custom_field_id=custom_field.get('custom_field_id'),
            custom_field_subcategory_id=custom_field.get('custom_field_subcategory_id'),
            custom_field_category_id=custom_field.get('custom_field_category_id')
        )

        # Remove empty values
        custom_field_dict = {k: v for k, v in custom_field_dict.items() if v}

        custom_field_id = custom_field_dict.get('custom_field_id')
        custom_field_category_id = custom_field_dict.get('custom_field_category_id')

        if custom_field_category_id:
            # Custom field category ID must be recognized
            cf_category = CustomFieldCategory.get(custom_field_category_id)  # type: CustomFieldCategory
            if not cf_category:
                raise NotFoundError("Custom field category ID not recognized")

            # Custom field category must belong to custom field
            if custom_field_id and cf_category.custom_field_id != custom_field_id:
                raise ForbiddenError("Custom field category does not belong to custom field")
            # Match custom field category to custom field if cf-id is not provided
            elif not custom_field_id:
                custom_field_obj = CustomField.get(cf_category.custom_field_id)
                if not custom_field_obj or (custom_field_obj and custom_field_obj.domain_id != request.user.domain_id):
                    raise ForbiddenError("Custom field category does not belong to user's domain")

        candidate_custom_field_id = custom_field.get('id')

        for value in custom_field_dict.get('values'):

            if candidate_custom_field_id:   # Update

                # Remove keys with None values
                custom_field_dict = purge_dict(custom_field_dict)

                # CandidateCustomField must be recognized
                can_custom_field_obj = CandidateCustomField.get_by_id(candidate_custom_field_id)
                if not can_custom_field_obj:
                    raise InvalidUsage(
                        error_message='Candidate custom field you are requesting to update does not exist',
                        error_code=custom_error.CUSTOM_FIELD_NOT_FOUND
                    )

                # CandidateCustomField must belong to Candidate
                if can_custom_field_obj.candidate_id != candidate_id:
                    raise ForbiddenError(error_message="Unauthorized candidate custom field",
                                         error_code=custom_error.CUSTOM_FIELD_FORBIDDEN)

                # Track all updates
                track_edits(update_dict=custom_field_dict,
                            table_name='candidate_custom_field',
                            candidate_id=candidate_id,
                            user_id=user_id,
                            query_obj=can_custom_field_obj,
                            value=value,
                            column_name='value')

                # Update CandidateCustomField
                can_custom_field_obj.update(value=value, custom_field_category_id=custom_field_category_id)

            else:  # Add
                custom_field_dict.update(dict(added_time=added_time, candidate_id=candidate_id))
                custom_field_id = custom_field_dict.get('custom_field_id')

                # Making sure no candidate_custom_field should be added without it's parent custom_field
                if not custom_field_id:
                    raise InvalidUsage(
                        error_message='No custom_field_id provided.',
                        error_code=custom_error.NO_CUSTOM_FIELD_ID_PROVIDED
                    )
                # TODO: Product decided to punt subcategory feature to a later time -Amir
                # custom_field_subcategory_id = custom_field_dict.get('custom_field_subcategory_id')

                # Prevent duplicate insertions
                if not does_candidate_cf_exist(candidate=candidate, custom_field_id=custom_field_id,
                                               value=value, custom_field_category_id=custom_field_category_id):
                    custom_field_dict['value'] = value
                    custom_field_dict.pop('values', None)
                    db.session.add(CandidateCustomField(**custom_field_dict))

                    if is_updating:  # Track all updates
                        track_edits(update_dict=custom_field_dict,
                                    table_name='candidate_custom_field',
                                    candidate_id=candidate_id,
                                    user_id=user_id,
                                    value=value,
                                    column_name='value')


def _add_or_update_educations(candidate, educations, added_datetime, user_id, is_updating):
    """
    Function will update CandidateEducation, CandidateEducationDegree, and
    CandidateEducationDegreeBullet or create new ones.
    """
    # Remove identical data
    educations = remove_duplicates(educations)

    # If any of educations is_current, set all of Candidate's educations' is_current to False
    candidate_id = candidate.id
    if is_updating and any([education.get('is_current') for education in educations]):
        CandidateEducation.set_is_current_to_false(candidate_id=candidate_id)

    validate_existing_objects(educations, CandidateEducation, candidate_id, is_updating, 'education',
                              custom_error.EDUCATION_NOT_FOUND, custom_error.EDUCATION_FORBIDDEN)

    candidate_utils = CandidateAddUpdateUtils(candidate_id, user_id, added_datetime)

    formatted_educations = []
    formatted_degrees = []
    formatted_bullets = []
    for education in educations:
        education_dict = parse_education(education)
        if not education_dict:
            continue
        education_dict.update(list_order=education.get('list_order') or 1)
        degrees = education_dict.pop('degrees', [])
        formatted_bullets.append([degree.pop('bullets', []) for degree in degrees])

        if not education_dict and not degrees:
            continue
        formatted_degrees.append(degrees)
        formatted_educations.append(education_dict)

    mergehub = MergeHub(candidate, dict(educations=formatted_educations))
    if is_updating:
        # if it is a candidate update, merge with existing education objects
        new_educations = mergehub.merge_educations()
    else:
        new_educations = [(education_dict, None) for education_dict in formatted_educations]

    """
    `new_educations` is a list of tuples where each tuple contains two items. At 0 index, there is new
    education dict object given by end-user and on index 1, there will be existing SqlAlchemy object of matching
    education or it will be None if it is not match of any existing education object.
    """
    # Iterate over all education objects and save those that are not duplicate of existing objects
    for index, (education_dict, existing_education_obj) in enumerate(new_educations):
        if not existing_education_obj:
            education_obj = candidate_utils.add_new_education(education_dict)
            track_edits(update_dict=education_dict, table_name='candidate_education',
                        candidate_id=candidate_id, user_id=user_id)
            candidate_utils.add_new_degrees_and_bullets(formatted_degrees[index], formatted_bullets[index],
                                                        education_obj)
        else:
            new_degrees = mergehub.merge_degrees(existing_education_obj.degrees, formatted_degrees[index])
            for degree_index, (degree_dict, existing_degree_obj) in enumerate(new_degrees):
                if not existing_degree_obj:
                    degree_obj = candidate_utils.add_new_degree(degree_dict, existing_education_obj.id)
                    candidate_utils.add_new_bullets(formatted_bullets[index][degree_index], degree_obj)
                else:
                    new_bullets = mergehub.merge_bullets(existing_degree_obj.bullets,
                                                         formatted_bullets[index][degree_index])
                    new_bullets = [bullet_dict for bullet_dict, bullet_obj in new_bullets if not bullet_obj]
                    candidate_utils.add_new_bullets(new_bullets, existing_degree_obj)


def _add_or_update_work_experiences(candidate, work_experiences, added_time, user_id, is_updating):
    """
    Function will update CandidateExperience and CandidateExperienceBullet
    or create new ones.
    """
    # Remove identical data
    experience_items = None
    for i, experience in enumerate(work_experiences):
        if experience.items() == experience_items:
            del work_experiences[i]
        else:
            experience_items = experience.items()

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

        # Start year cannot be greater than end year
        if (start_year and end_year) and start_year > end_year:
            raise InvalidUsage('Start year ({}) cannot be greater than end year ({})'.format(start_year, end_year))

        country_code = work_experience['country_code'].upper().strip() if work_experience.get('country_code') else None
        subdivision_code = work_experience['subdivision_code'].upper().strip() \
            if work_experience.get('subdivision_code') else None
        experience_dict = dict(
            list_order=work_experience.get('list_order') or 1,
            organization=work_experience['organization'].strip() if work_experience.get('organization') else None,
            position=work_experience['position'].strip() if work_experience.get('position') else None,
            city=work_experience['city'].strip() if work_experience.get('city') else None,
            iso3166_subdivision=subdivision_code,
            state=(work_experience.get('state') or '').strip(),
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
            experience_dict = purge_dict(experience_dict)

            # CandidateExperience must be recognized
            can_exp_obj = CandidateExperience.get(experience_id)
            if not can_exp_obj:
                raise InvalidUsage('Candidate experience not found', custom_error.EXPERIENCE_NOT_FOUND)

            # CandidateExperience must belong to Candidate
            if can_exp_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate experience', custom_error.EXPERIENCE_FORBIDDEN)

            # If start year needs to be updated, it must not be greater than existing end year
            if start_year and not end_year and (start_year > can_exp_obj.end_year):
                raise InvalidUsage('Start year ({}) cannot be greater than end year ({})'.format(start_year,
                                                                                                 can_exp_obj.end_year))
            # If end year needs to be updated, it must not be less than existing start year
            if end_year and not start_year and (end_year < can_exp_obj.start_year):
                raise InvalidUsage('End year ({}) cannot be less than start year ({})'.format(end_year,
                                                                                              can_exp_obj.start_year))

            # Add up candidate's total months of experience
            update_total_months_experience(candidate, experience_dict, can_exp_obj)

            # Track all changes made to CandidateExperience
            track_edits(update_dict=experience_dict, table_name='candidate_experience',
                        candidate_id=candidate_id, user_id=user_id, query_obj=can_exp_obj)

            # Update CandidateExperience
            can_exp_obj.update(**experience_dict)

            # CandidateExperienceBullet
            experience_bullets = work_experience.get('bullets') or []
            for experience_bullet in remove_duplicates(experience_bullets):

                description = (experience_bullet.get('description') or '').strip()
                experience_bullet_dict = dict(list_order=experience_bullet.get('list_order'), description=description)

                # Remove keys with None values
                experience_bullet_dict = purge_dict(experience_bullet_dict)

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
                    track_edits(update_dict=experience_bullet_dict,
                                table_name='candidate_experience_bullet',
                                candidate_id=candidate_id,
                                user_id=user_id,
                                query_obj=can_exp_bullet_obj)

                    can_exp_bullet_obj.update(**experience_bullet_dict)
                else:  # Add
                    # Update experience_bullet_dict with added_time
                    experience_bullet_dict['added_time'] = added_time
                    experience_bullet_dict.update(dict(candidate_experience_id=experience_id))
                    db.session.add(CandidateExperienceBullet(**experience_bullet_dict))

                    if is_updating:  # Track all updates
                        track_edits(update_dict=experience_bullet_dict,
                                    table_name='candidate_experience_bullet',
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
            for experience_bullet in remove_duplicates(experience_bullets):

                description = (experience_bullet.get('description') or '').strip()
                experience_bullet_dict = dict(list_order=experience_bullet.get('list_order'), description=description)

                # Remove keys with None values
                experience_bullet_dict = purge_dict(experience_bullet_dict)

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
    work_preference_dict = purge_dict(work_preference_dict)

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


def _add_or_update_emails(candidate, emails, user_id, is_updating):
    """
    Function will update CandidateEmail or create new one(s).
    """
    candidate_id = candidate.id

    # Raise an error if more than one email is set as "default"
    is_default_values = [email.get('is_default') for email in emails]
    if len(filter(None, is_default_values)) > 1:
        raise InvalidUsage('Only one email should be set as default email', custom_error.INVALID_USAGE)

    # If any of emails' is_default is True, set all of candidate's emails' is_default to False
    if any(is_default_values):
        CandidateEmail.set_is_default_to_false(candidate_id)

    # Check if any of the emails have a label
    emails_has_label = any([email.get('label') for email in emails])

    # Check if any of the emails is set as the default email
    emails_has_default = any([isinstance(email.get('is_default'), bool) for email in emails])

    # If duplicate email addresses are provided, we will only use one of them
    seen = set()
    for email in emails:
        email_address = email.get('address')
        if email_address and email_address in seen:
            emails.remove(email)
        seen.add(email_address)

    for index, email in enumerate(remove_duplicates(emails)):

        # If none of the provided emails have "is_default" set to true and none of candidate's existing emails
        #   is set to default, then the first provided email will be a default email
        is_default = index == 0 if (not emails_has_default and not CandidateEmail.has_default_email(candidate_id)) \
            else email.get('is_default')

        # If there's no label, the first email's label will be 'Primary'; rest will be 'Other'
        email_label = EmailLabel.PRIMARY_DESCRIPTION if (not emails_has_label and index == 0) \
            else (email.get('label') or '').strip().title()

        email_address = email.get('address')

        email_dict = dict(
            address=email_address,
            email_label_id=EmailLabel.email_label_id_from_email_label(email_label),
            is_default=is_default
        )

        # Remove empty values from email_dict
        email_dict = purge_dict(email_dict)

        email_id = email.get('id')
        if email_id:  # Update
            # CandidateEmail must be recognized
            candidate_email_obj = CandidateEmail.get(email_id)
            if not candidate_email_obj:
                raise NotFoundError('Candidate email not found', custom_error.EMAIL_NOT_FOUND)

            # CandidateEmail must belong to Candidate
            if candidate_email_obj.candidate_id != candidate_id:
                raise ForbiddenError('Unauthorized candidate email', custom_error.EMAIL_FORBIDDEN)

            # Email must not belong to another candidate in the same domain
            matching_email = CandidateEmail.get_email_in_users_domain(request.user.domain_id, email_address)
            if matching_email and matching_email.candidate_id != candidate_id:
                raise ForbiddenError("Email (address = {}) belongs to someone else!".
                                     format(matching_email.address), custom_error.EMAIL_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=email_dict, table_name='candidate_email',
                        candidate_id=candidate_id, user_id=user_id, query_obj=candidate_email_obj)

            # Update CandidateEmail
            candidate_email_obj.update(**email_dict)

        else:  # Add
            if is_updating:  # append email to existing candidate's records

                # Email must not belong to another candidate in the same domain
                matching_email = CandidateEmail.get_email_in_users_domain(request.user.domain_id, email_address)
                if matching_email:
                    if matching_email.candidate_id != candidate_id:
                        raise ForbiddenError("Email (address = {}) belongs to someone else!".
                                             format(matching_email.address), custom_error.EMAIL_FORBIDDEN)
                    else:  # prevent adding duplicate email address(s) to candidate's records
                        continue
                # prevent adding duplicate email address(s) to candidate's records
                elif do_emails_exist(candidate.emails, email_dict):
                    continue

                email_dict.update(dict(candidate_id=candidate_id))
                db.session.add(CandidateEmail(**email_dict))

                # Track all changes
                track_edits(update_dict=email_dict, table_name='candidate_email',
                            candidate_id=candidate_id, user_id=user_id)

            else:  # add email to new candidate
                email_dict.update(dict(candidate_id=candidate_id))
                db.session.add(CandidateEmail(**email_dict))


def _add_or_update_phones(candidate, phones, user_id, is_updating):
    """
    Function will update CandidatePhone or create new one(s).
    """
    candidate_id = candidate.id

    # Raise an error if more than one email is set as "default"
    is_default_values = [phone.get('is_default') for phone in phones]
    if len(filter(None, is_default_values)) > 1:
        raise InvalidUsage('Only one phone should be set as default', custom_error.INVALID_USAGE)

    # If any of phones' is_default is True, set all of candidate's phones' is_default to False
    if any(is_default_values):
        CandidatePhone.set_is_default_to_false(candidate_id)

    # Check if phone label and default have been provided
    phones_has_label = any([phone.get('label') for phone in phones])
    phones_has_default = any([isinstance(phone.get('is_default'), bool) for phone in phones])

    # If duplicate phone numbers are provided, we will only use one of them
    seen = set()
    for phone in phones:
        phone_value = phone.get('value')
        if phone_value and phone_value in seen:
            phones.remove(phone)
        seen.add(phone_value)

    for i, phone in enumerate(remove_duplicates(phones)):

        # If there's no is_default, the first phone should be default
        is_default = i == 0 if not phones_has_default else phone.get('is_default')

        # If there's no label, the first phone's label will be 'Home', rest will be 'Other'
        phone_label = PhoneLabel.DEFAULT_LABEL if (not phones_has_label and i == 0) \
            else (phone.get('label') or '').strip().title()

        # Format phone number
        value = (phone.get('value') or '').strip()

        # Phone number must contain at least 7 digits
        # http://stackoverflow.com/questions/14894899/what-is-the-minimum-length-of-a-valid-international-phone-number
        number = re.sub('\D', '', value)
        if len(number) < 7:
            raise InvalidUsage("Phone number ({}) must be at least 7 digits".format(value), custom_error.INVALID_PHONE)

        iso3166_country_code = CachedData.country_codes[0] if CachedData.country_codes else None
        phone_number_obj = parse_phone_number(value, iso3166_country_code=iso3166_country_code) if value else None
        """
        :type phone_number_obj: PhoneNumber
        """

        # phonenumbers.format() will append "+None" if phone_number_obj.country_code is None
        if phone_number_obj:
            if not phone_number_obj.country_code:
                value = str(phone_number_obj.national_number)
            else:
                value = str(phonenumbers.format_number(phone_number_obj, phonenumbers.PhoneNumberFormat.E164))

        # Phone number must not belong to any other candidate in the same domain
        matching_phone_values = CandidatePhone.search_phone_number_in_user_domain(value, request.user)
        if matching_phone_values and matching_phone_values[0].candidate_id != candidate_id:
            # TODO: this validation should be happening much earlier. For now we need this for a hotfix but should be revisited later
            raise InvalidUsage(error_message='Candidate already exists, creation failed',
                               error_code=custom_error.CANDIDATE_ALREADY_EXISTS,
                               additional_error_info={'id': matching_phone_values[0].candidate_id})

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
        phone_dict = purge_dict(phone_dict)

        # Prevent adding empty records to db
        if not phone_dict:
            continue

        candidate_phone_id = phone.get('id')
        if candidate_phone_id:  # Update

            # CandidatePhone must be recognized
            can_phone_obj = CandidatePhone.get(candidate_phone_id)
            if not can_phone_obj:
                raise NotFoundError(error_message='Candidate phone not found',
                                    error_code=custom_error.PHONE_NOT_FOUND,
                                    additional_error_info={'id': candidate_phone_id})

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

                if is_updating:  # append phone to existing candidate's records

                    # Prevent adding duplicate phone number(s) to candidate's profile
                    if matching_phone_values and matching_phone_values[0].candidate_id == candidate_id:
                        continue
                    elif do_phones_exist(candidate.phones, phone_dict):
                        continue

                    db.session.add(CandidatePhone(**phone_dict))

                    # Track all changes
                    track_edits(update_dict=phone_dict, table_name='candidate_phone',
                                candidate_id=candidate_id, user_id=user_id)
                else:  # add phone to new candidate
                    # Prevent adding duplicate phone number(s) to candidate's profile
                    if matching_phone_values and matching_phone_values[0].candidate_id == candidate_id:
                        continue
                    elif do_phones_exist(candidate.phones, phone_dict):
                        continue

                    db.session.add(CandidatePhone(**phone_dict))


def _add_or_update_military_services(candidate, military_services, user_id, is_updating):
    """
    Function will update CandidateMilitaryService or create new one(s).
    """
    candidate_id = candidate.id
    for military_service in remove_duplicates(military_services):

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
            to_date=to_date,
            start_year=military_service.get('start_year'),
            start_month=military_service.get('start_month'),
            end_year=military_service.get('end_year'),
            end_month=military_service.get('end_month')
        )

        # Remove keys with empty values
        military_service_dict = purge_dict(military_service_dict)

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
            db.session.add(CandidateMilitaryService(**military_service_dict))
            if is_updating:  # Track all updates
                track_edits(update_dict=military_service_dict, table_name='candidate_military_service',
                            candidate_id=candidate_id, user_id=user_id)


def _add_or_update_preferred_locations(candidate, preferred_locations, user_id, is_updating):
    """
    Function will update CandidatePreferredLocation or create a new one.
    """
    candidate_id, candidate_preferred_locations = candidate.id, candidate.preferred_locations
    for preferred_location in remove_duplicates(preferred_locations):

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
        preferred_location_dict = purge_dict(preferred_location_dict)

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
    for skill in remove_duplicates(skills):

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
        skill_dict = purge_dict(skill_dict)

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
    for social_network in remove_duplicates(social_networks):

        social_network_dict = dict(
            social_network_id=social_network_id_from_name((social_network.get('name') or '').strip()),
            social_profile_url=(social_network.get('profile_url') or '').strip()
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
                raise ForbiddenError(error_message='Unauthorized candidate social network: %s' % can_sn_obj.social_profile_url,
                                     error_code=custom_error.SOCIAL_NETWORK_FORBIDDEN)

            # Track all changes
            track_edits(update_dict=social_network_dict,
                        table_name='candidate_social_network',
                        candidate_id=candidate_id,
                        user_id=user_id,
                        query_obj=can_sn_obj)

            # If social network name is None, we assume the name remains the same
            if not social_network_dict['social_network_id']:
                del social_network_dict['social_network_id']

            can_sn_obj.update(**social_network_dict)

        else:  # Add
            social_network_dict.update(dict(candidate_id=candidate_id))
            # Prevent duplicate entries
            if not does_social_network_exist(candidate_sns, social_network_dict):
                db.session.add(CandidateSocialNetwork(**social_network_dict))

                if is_updating:  # Track all updates
                    track_edits(update_dict=social_network_dict,
                                table_name='candidate_social_network',
                                candidate_id=candidate_id,
                                user_id=user_id)


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

        # If start month and/or end month is not provided, we assume it was January
        previous_start_month = candidate_experience.start_month or 1
        previous_end_month = candidate_experience.end_month or 1

        # A CandidateExperience has been removed
        if deleted:
            if previous_end_year and previous_start_year:
                total_months_experience = - (previous_end_year - previous_start_year) * 12 + \
                                          (previous_end_month - previous_start_month)

        else:  # An existing CandidateExperience's dates have been updated

            this_total_months_experience, previous_total_months_experience = None, None
            if start_year and end_year:
                this_total_months_experience = (end_year - start_year) * 12 + (end_month - start_month)
            if previous_end_year and previous_start_year:
                previous_total_months_experience = (previous_end_year - previous_start_year) * 12 + (previous_end_month - previous_start_month)

            if this_total_months_experience and previous_total_months_experience:
                total_months_experience = this_total_months_experience - previous_total_months_experience
            elif this_total_months_experience and not previous_total_months_experience:
                total_months_experience = this_total_months_experience

    candidate.total_months_experience += total_months_experience
    return


def most_recent_position(work_experiences):
    start_year, start_month = None, None
    end_year, end_month = None, None
    found = None

    for index, experience in enumerate(work_experiences):
        if experience.get('is_current') is True:
            return experience['position']
        else:
            experience_start_year = experience.get('start_year')
            experience_start_month = experience.get('start_month')
            experience_end_year = experience.get('end_year')
            experience_end_month = experience.get('end_month')

            if not experience_start_year and not experience_end_year:
                continue

            if experience_start_year >= start_year:
                start_year = experience_start_year
                found = index
                if experience_start_month > start_month:
                    start_month = experience_start_month
                    found = index

            if experience_end_year >= end_year:
                end_year = experience_end_year
                found = index
                if experience_end_month > end_month:
                    end_month = experience_end_month
                    found = index

    return work_experiences[found].get('position') if found is not None else None


class CandidateTitle(object):
    def __init__(self, experiences=None, candidate_id=None):
        """
        :type experiences: list
        :type title: str
        :type candidate_id: int
        """
        self.title = None
        self.experiences = list(experiences) if experiences else None

        # Extrapolate job title from experiences data ONLY if title is not provided
        # and candidate is being created
        if not candidate_id and self.experiences:
            # title will be set to current experience's position if provided, otherwise it will be
            # extrapolated from the experiences data
            self.title = self.sorted_experiences(self.experiences)[0].get('position')

        # During candidate update, only change its title if title is set to empty string
        elif candidate_id:
            candidates_most_recent_exp = self.get_candidates_most_recent_experience(candidate_id)
            # If candidate exists, we need to compare candidate's existing experiences with provided experiences
            # and set candidate's title to its most recent position
            if self.experiences and candidates_most_recent_exp:
                self.experiences.append(candidates_most_recent_exp)
                self.title = self.sorted_experiences(self.experiences)[0].get('position')

    @staticmethod
    def sorted_experiences(experiences):
        """
        Method will sort candidate's experiences in descending order, ordered by sort_keys
        :type experiences: list
        :rtype: list[dict]
        """
        def sort_keys(keys):
            def get_values(dict_):
                return [dict_[k] for k in keys if k in dict_]
            return get_values

        ordered_experiences = sorted(experiences,
                                     key=sort_keys(['start_year', 'end_year', 'start_month', 'end_month']),
                                     reverse=True)

        for exp in experiences:
            if exp.get('is_current') is True:
                ordered_experiences.insert(0, exp)

        return ordered_experiences

    @staticmethod
    def get_candidates_most_recent_experience(candidate_id):
        """
        Method will retrieve & return candidate's most recent experience from database
        :type candidate_id: int
        :rtype: dict
        """
        # Retrieve candidate's most recent experience from db
        # If title is not provided and candidate has experience, its title will be its most recent position
        most_recent_experience = CandidateExperience.query.filter_by(candidate_id=candidate_id). \
            order_by(CandidateExperience.is_current.desc(),
                     CandidateExperience.end_year.desc(),
                     CandidateExperience.start_year.desc(),
                     CandidateExperience.end_month.desc(),
                     CandidateExperience.start_month.desc()).first()  # type: CandidateExperience
        return most_recent_experience.to_json() if most_recent_experience else None


class CachedData(object):
    """
    This class will contain data that may be required by other functions.
    Note: Should be cleared when its data is no longer needed
    """
    country_codes = []
    candidate_emails = []


def get_value(dict_item, key, function_name=None, default=None):
    """
    This function takes a dictionary and a key for which we need to return a value. It retrieves that key's values
    from dict and after parsing, returns the value.
    :param sict dict_item: dictionary object
    :param str key: key name
    :param str function_name: string function which will be applied on value like `upper`, `lower`, `title` etc.
    :param type(t) default: default value to e returned
    """
    val = dict_item[key].strip() if dict_item.get(key) else default
    if function_name and val:
        val = getattr(val, function_name)()
    return val


def validate_existing_objects(dict_objects, model, candidate_id, is_updating, entity_name, not_found_code=404,
                              forbidden_code=403):
    """
    This function validates that all dict objects with id field, there must be an object in db for that id.
    """
    ids = [obj['id'] for obj in dict_objects if 'id' in obj]
    if not is_updating and ids:
        raise InvalidUsage("Can't specify {} id while creating candidate".format(entity_name))

    # Not using model.query to avoid PEP8 warning in calling function
    objects = getattr(model, 'query').filter(model.id.in_(ids)).all()
    """
    Instead of querying model objects one by one in a loop much slow and this processing is too
    fast (i.e. looping and filtering objects)
    """
    if len(objects) != len(ids):
        missing_ids = set(ids) - set([obj.id for obj in objects])
        raise InvalidUsage('Candidate {}es not found with following ids: {}'.format(entity_name, missing_ids),
                           not_found_code)

    for obj in objects:
        if obj.candidate_id != candidate_id:
            raise ForbiddenError("Unauthorized candidate {}".format(entity_name), forbidden_code)
    return {obj.id: obj for obj in objects}


def parse_addresses(addresses, candidate, has_default=False):
    """
    This function takes a list of candidate addresses and parses them.
    """
    for i, address in enumerate(addresses):

        zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
        city = get_value(address, 'city')
        country_code = address.get('country_code')
        if country_code:
            country_code = get_country_code_from_name(country_code)
            if country_code:
                country_code = country_code.upper()
            else:
                logger.info("Country code was not found ... %s" % country_code)

        subdivision_code = address['subdivision_code'].upper() if address.get('subdivision_code') else None
        address_dict = dict(
            id=address.get('id'),
            address_line_1=get_value(address, 'address_line_1'),
            address_line_2=get_value(address, 'address_line_2'),
            city=city,
            state=(address.get('state') or '').strip(),
            iso3166_subdivision=subdivision_code,
            iso3166_country=country_code,
            zip_code=zip_code,
            po_box=get_value(address, 'po_box'),
            is_default=i == 0 if not has_default and (city or zip_code or country_code) else address.get('is_default'),
            coordinates=get_coordinates(zipcode=zip_code, city=city, state=subdivision_code)
        )

        # Remove keys that have None values
        address_dict = purge_dict(address_dict)

        # Prevent adding empty records to db
        if not address_dict or (len(address_dict) == 1 and 'is_default' in address_dict):
            # addresses.remove(address_dict)
            continue

        # Cache country code
        CachedData.country_codes.append(address_dict.get('iso3166_country'))
        address_dict.update(dict(candidate_id=candidate.id, resume_id=candidate.id))
        yield GtDict(address_dict)


def parse_education(education):
    """
    Parses education object/dict and removes None value keys
    """
    # CandidateEducation
    country_code = education['country_code'].upper() if education.get('country_code') else None
    subdivision_code = education['subdivision_code'].upper() if education.get('subdivision_code') else None
    education_dict = dict(
        school_name=(education.get('school_name') or '').strip(),
        school_type=(education.get('school_type') or '').strip(),
        city=(education.get('city') or '').strip(),
        state=(education.get('state') or '').strip(),
        iso3166_subdivision=subdivision_code,
        iso3166_country=country_code,
        is_current=education.get('is_current'),
        id=education.get('id')
    )
    education_dict = purge_dict(education_dict)
    if not education_dict:
        return education_dict

    degrees = education.get('degrees') or []
    formatted_degrees = []
    for degree in degrees:
        degree_dict = parse_degree(degree)
        if not degree_dict:
            continue
        formatted_degrees.append(degree_dict)

    education_dict['degrees'] = remove_duplicates(formatted_degrees)
    return GtDict(education_dict)


def parse_degree(education_degree):
    """
    Parses degree object (dict) and removes None value keys
    """
    # Start year must not be later than end year
    start_year, end_year = education_degree.get('start_year'), education_degree.get('end_year')
    if (start_year and end_year) and (start_year > end_year):
        raise InvalidUsage('Start year of education cannot be later than end year of education',
                           custom_error.INVALID_USAGE)

    # Degree end_time is necessary for searching. If degree's end-month is not provided, assume it's 1/jan
    end_month = education_degree.get('end_month')
    end_time = None
    if end_year:
        if end_month:
            end_time = datetime.datetime(end_year, end_month, 1)
        else:
            end_time = datetime.datetime(end_year, 1, 1)

    degree_type = education_degree['type'].strip() if education_degree.get('type') else None
    degree_title = education_degree['title'].strip() if education_degree.get('title') else None
    degree_id = education_degree.get('id')
    main_fields = degree_id or degree_title or degree_type
    education_degree_dict = dict(
        list_order=education_degree.get('list_order'),
        degree_type=degree_type,
        degree_title=degree_title,
        start_year=start_year if degree_id or degree_title or degree_type else None,
        start_month=education_degree.get('start_month') if main_fields else None,
        end_year=end_year if main_fields else None,
        end_month=end_month if main_fields else None,
        gpa_num=education_degree.get('gpa') if main_fields else None,
        classification_type_id=classification_type_id_from_degree_type(degree_type),
        start_time=education_degree.get('start_time') if main_fields else None,
        end_time=end_time if main_fields else None,
        id=degree_id
    )

    education_degree_dict = purge_dict(education_degree_dict)
    if not education_degree_dict:
        return education_degree_dict

    bullets = education_degree.get('bullets') or []
    formatted_bullets = []
    for bullet in bullets:
        bullet = parse_degree_bullet(bullet)
        if not bullet:
            continue
        formatted_bullets.append(bullet)
    education_degree_dict['bullets'] = remove_duplicates(formatted_bullets)
    return education_degree_dict


def parse_degree_bullet(degree_bullet):
    """
    Parses degree bullets and removes None value keys
    """
    degree_bullet_dict = dict(
        id=degree_bullet.get('id'),
        concentration_type=degree_bullet['major'].strip()
        if degree_bullet.get('major') else None,
        comments=degree_bullet['comments'].strip()
        if degree_bullet.get('comments') else None
    )
    # Remove keys with None values
    return purge_dict(degree_bullet_dict)


class CandidateAddUpdateUtils(object):
    """
    This class provides helper methods to add candidate related objects
    """
    def __init__(self, candidate_id, user_id, added_time):
        self.candidate_id = candidate_id
        self.user_id = user_id
        self.added_time = added_time

    def add_new_education(self, education_dict):
        """
        Update education dict with candidate info and saves in db
        """
        education_dict.update(candidate_id=self.candidate_id, resume_id=self.candidate_id, added_time=self.added_time)
        education_obj = CandidateEducation(**education_dict)
        db.session.add(education_obj)
        db.session.flush()
        return education_obj

    def add_new_degree(self, degree_dict, education_id):
        """
        Update education degree dict with candidate info and added_time and saves in db
        """
        degree_dict.update(candidate_education_id=education_id,
                           added_time=self.added_time)
        degree_obj = CandidateEducationDegree(**degree_dict)
        db.session.add(degree_obj)
        db.session.flush()
        track_edits(update_dict=degree_dict, table_name='candidate_education_degree',
                    candidate_id=self.candidate_id, user_id=self.user_id)
        return degree_obj

    def add_new_degrees_and_bullets(self, degrees, all_bullets, education):
        """
        Update education degrees and  bullets dict with candidate info and added_time save in db
        """
        for degree_index, degree_dict in enumerate(degrees):
            degree_obj = self.add_new_degree(degree_dict, education.id)
            self.add_new_bullets(all_bullets[degree_index], degree_obj)

    def add_new_bullets(self, bullets, degree):
        """
        Update education degree bullet dict with candidate info and added_time save in db
        """
        for bullet_dict in bullets:
            bullet_dict.update(candidate_education_degree_id=degree.id,
                               added_time=self.added_time)
            db.session.add(CandidateEducationDegreeBullet(**bullet_dict))
            track_edits(update_dict=bullet_dict, table_name='candidate_education_degree_bullet',
                        candidate_id=self.candidate_id, user_id=self.user_id)


# TODO: Combine `remove_nulls` and `remove_null_and_empty_string` into one function/class
def remove_nulls(dict_data):
    """
    Function will create a dict object from dict_data without the None values
    :type dict_data: dict
    :rtype: dict
    """
    return {k: v.strip() if isinstance(v, basestring) else v for k, v in dict_data.items() if v is not None}


def remove_null_and_empty_string(dict_data):
    """
    Function will create a dict object form dict_data without the None values and the empty string values
    :type dict_data: dict
    :rtype: dict
    """
    r = dict()
    for k, v in dict_data.items():
        if isinstance(v, basestring):
            v = v.strip()
            if v != '':
                r[k] = v
        elif v is not None:
            r[k] = v
    return r

