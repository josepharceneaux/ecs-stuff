from candidate_service.candidate_app import db, logger
from candidate_service.common.models.candidate import (
    Candidate, EmailLabel, CandidateEmail, CandidatePhone, PhoneLabel,
    CandidateWorkPreference, CandidatePreferredLocation, CandidateAddress,
    CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField,
    CandidateSocialNetwork, SocialNetwork
)
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.email_marketing import (EmailCampaign, EmailCampaignSend)
from candidate_service.common.models.misc import (Country, AreaOfInterest, CustomField)
from datetime import date


def fetch_candidate_info(candidate_id, fields=None):
    """
    Fetched for candidate object via candidate's id
    :type       candidate_id: int
    :type       fields: None | str

    :return:    Candidate dict
    :rtype:     dict[str, T]
    """
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

    emails = None
    if get_all_fields or 'emails' in fields:
        emails = email_label_and_address(candidate_id=candidate_id)

    phones = None
    if get_all_fields or 'phones' in fields:
        phones = phone_label_and_value(candidate_id=candidate_id)

    candidate_addresses = None
    if get_all_fields or 'addresses' in fields:
        candidate_addresses = addresses(candidate_id=candidate_id)

    candidate_work_experiences = None
    if get_all_fields or 'work_experiences' in fields:
        candidate_work_experiences = work_experiences(candidate_id=candidate_id)

    candidate_work_preference = None
    if get_all_fields or 'work_preferences' in fields:
        candidate_work_preference = work_preference(candidate_id=candidate_id)

    candidate_preferred_locations = None
    if get_all_fields or 'preferred_locations' in fields:
        candidate_preferred_locations = preferred_locations(candidate_id=candidate_id)

    candidate_educations = None
    if get_all_fields or 'educations' in fields:
        candidate_educations = educations(candidate_id=candidate_id)

    candidate_skills = None
    if get_all_fields or 'skills' in fields:
        candidate_skills = skills(candidate_id=candidate_id)

    candidate_interests = None
    if get_all_fields or 'areas_of_interest' in fields:
        candidate_interests = areas_of_interest(candidate_id=candidate_id)

    candidate_military_services = None
    if get_all_fields or 'military_services' in fields:
        candidate_military_services = military_services(candidate_id=candidate_id)

    candidate_custom_fields = None
    if get_all_fields or 'custom_fields' in fields:
        candidate_custom_fields = custom_fields(candidate_id=candidate_id)

    candidate_social_networks = None
    if get_all_fields or 'social_networks' in fields:
        candidate_social_networks = social_network_name_and_url(candidate_id=candidate_id)

    history = None
    if get_all_fields or 'contact_history' in fields:
        history = contact_history(candidate_id=candidate_id)

    openweb_id = None
    if get_all_fields or 'openweb_id' in fields:
        openweb_id = candidate.dice_social_profile_id

    dice_profile_id = None
    if get_all_fields or 'dice_profile_id' in fields:
        dice_profile_id = candidate.dice_profile_id

    return_dict = {
        'id': candidate_id,
        'full_name': full_name,
        'created_at_datetime': None,
        'emails': emails,
        'phones': phones,
        'addresses': candidate_addresses,
        'work_experiences': candidate_work_experiences,
        'work_preference': candidate_work_preference,
        'preferred_locations': candidate_preferred_locations,
        'educations': candidate_educations,
        'skills': candidate_skills,
        'areas_of_interest': candidate_interests,
        'military_services': candidate_military_services,
        'custom_fields': candidate_custom_fields,
        'social_networks': candidate_social_networks,
        'contact_history': history,
        'openweb_id': openweb_id,
        'dice_profile_id': dice_profile_id
    }

    # Remove all values that are empty
    return_dict = dict((k, v) for k, v in return_dict.iteritems() if v is not None)
    return return_dict


def email_label_and_address(candidate_id):
    candidate_emails = db.session.query(CandidateEmail).filter_by(candidate_id=candidate_id)
    return [{
        'label': db.session.query(EmailLabel).get(email.email_label_id).description,
        'address': email.address
    } for email in candidate_emails]


def phone_label_and_value(candidate_id):
    candidate_phones = db.session.query(CandidatePhone).filter_by(candidate_id=candidate_id)
    return [{
        'label': db.session.query(PhoneLabel).get(phone.phone_label_id).description,
        'value': phone.value
    } for phone in candidate_phones]


def addresses(candidate_id):
    candidate_addresses = db.session.query(CandidateAddress).\
        filter_by(candidate_id=candidate_id)
    return [{
        'address_line_1': candidate_address.address_line_1,
        'address_line_2': candidate_address.address_line_2,
        'city': candidate_address.city,
        'state': candidate_address.state,
        'zip_code': candidate_address.zip_code,
        'po_box': candidate_address.po_box,
        'country': country_name_from_country_id(country_id=candidate_address.country_id),
        'latitude': candidate_address.coordinates and candidate_address.coordinates.split(',')[0],
        'longitude': candidate_address.coordinates and candidate_address.coordinates.split(',')[1],
        'is_default': candidate_address.is_default
    } for candidate_address in candidate_addresses]


def work_experiences(candidate_id):
    # Candidate experiences queried from db and returned in descending order
    candidate_experiences = db.session.query(CandidateExperience).\
        filter_by(candidate_id=candidate_id).\
        order_by(CandidateExperience.is_current.desc(), CandidateExperience.start_year.desc(),
                 CandidateExperience.start_month.desc())
    return [{
        'company': candidate_experience.organization,
        'role': candidate_experience.position,
        'start_date': date_of_employment(year=candidate_experience.start_year,
                                         month=candidate_experience.start_month or 1),
        'end_date': date_of_employment(year=candidate_experience.end_year,
                                       month=candidate_experience.end_month or 1),
        'city': candidate_experience.city,
        'country': country_name_from_country_id(country_id=candidate_experience.country_id),
        'is_current': candidate_experience.is_current
    } for candidate_experience in candidate_experiences]


def work_preference(candidate_id):
    candidate_work_preference = db.session.query(CandidateWorkPreference).\
        filter_by(candidate_id=candidate_id).first()
    return {
        'authorization': candidate_work_preference.authorization,
        'employment_type': candidate_work_preference.tax_terms,
        'security_clearance': candidate_work_preference.security_clearance,
        'willing_to_relocate': candidate_work_preference.relocate,
        'telecommute': candidate_work_preference.telecommute,
        'travel_percentage': candidate_work_preference.travel_percentage,
        'third_party': candidate_work_preference.third_party
    } if candidate_work_preference else None


def preferred_locations(candidate_id):
    candidate_preferred_locations = db.session.query(CandidatePreferredLocation).\
        filter_by(candidate_id=candidate_id)
    return [{
        'address': preferred_location.address,
        'city': preferred_location.city,
        'region': preferred_location.region,
        'country': country_name_from_country_id(country_id=preferred_location.country_id)
    } for preferred_location in candidate_preferred_locations]


def educations(candidate_id):
    candidate_educations = db.session.query(CandidateEducation).\
        filter_by(candidate_id=candidate_id)
    return [{
        'school_name': education.school_name,
        'degree_details': degree_info(education_id=education.id),
        'city': education.city,
        'state': education.state,
        'country': country_name_from_country_id(country_id=education.country_id)
    } for education in candidate_educations]


def degree_info(education_id):
    education = db.session.query(CandidateEducationDegree).\
        filter_by(candidate_education_id=education_id)
    return [{
        'degree_title': degree.degree_title,
        'degree_type': degree.degree_type,
        'start_date': degree.start_time.date().isoformat() if degree.start_time else None,
        'end_date': degree.end_time.date().isoformat() if degree.end_time else None
    } for degree in education]


def skills(candidate_id):
    candidate_skills = db.session.query(CandidateSkill).\
        filter_by(candidate_id=candidate_id)
    return [{
        'name': skill.description,
        'month_used': skill.total_months,
        'last_used_date': skill.last_used.isoformat() if skill.last_used else None
    } for skill in candidate_skills]


def areas_of_interest(candidate_id):
    candidate_interests = db.session.query(CandidateAreaOfInterest).\
        filter_by(candidate_id=candidate_id)
    return [{
        'id': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).id,
        'name': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).description
    } for interest in candidate_interests]


def military_services(candidate_id):
    candidate_military_experience = db.session.query(CandidateMilitaryService).\
        filter_by(candidate_id=candidate_id)
    return [{
        'branch': military_info.branch,
        'service_status': military_info.service_status,
        'highest_grade': military_info.highest_grade,
        'highest_rank': military_info.highest_rank,
        'start_date': military_info.from_date,
        'end_date': military_info.to_date,
        'country': country_name_from_country_id(country_id=military_info.country_id)
    } for military_info in candidate_military_experience]


def custom_fields(candidate_id):
    candidate_custom_fields = db.session.query(CandidateCustomField).\
        filter_by(candidate_id=candidate_id)
    return [{
        'id': candidate_custom_field.custom_field_id,
        'name': db.session.query(CustomField).get(candidate_custom_field.custom_field_id),
        'value': candidate_custom_field.value,
        'created_at_datetime': candidate_custom_field.added_time.isoformat()
    } for candidate_custom_field in candidate_custom_fields]


def social_network_name_and_url(candidate_id):
    candidate_social_networks = db.session.query(CandidateSocialNetwork).\
        filter_by(candidate_id=candidate_id)
    return [{
        'name': social_network_name(social_network_id=social_network.social_network_id),
        'url': social_network.social_profile_url
    } for social_network in candidate_social_networks]


class ContactHistoryEvent:
    def __init__(self):
        pass

    CREATED_AT = 'created_at'
    EMAIL_SEND = 'email_send'
    EMAIL_OPEN = 'email_open'   # Todo: Implement opens and clicks into timeline
    EMAIL_CLICK = 'email_click'


def contact_history(candidate_id):
    timeline = []

    # Campaign sends & campaigns
    email_campaign_sends = db.session.query(EmailCampaignSend).filter_by(candidate_id=candidate_id)
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


def country_name_from_country_id(country_id):
    if not country_id:
        return 'United States'
    country = db.session.query(Country).get(country_id)
    if country:
        return country.name
    else:
        logger.info('country_name_from_country_id: country_id is not recognized: %s',
                    country_id)
        return 'United States'


def social_network_name(social_network_id):
    social_network = db.session.query(SocialNetwork).get(social_network_id)
    if social_network:
        return social_network.name
    else:
        logger.info('social_network_name: social_network from ID not recognized: %s',
                    social_network_id)
        return None


def get_candidate_id_from_candidate_email(candidate_email):
    candidate_email_row = db.session.query(CandidateEmail).\
        filter_by(address=candidate_email).first()
    if not candidate_email_row:
        logger.info('get_candidate_id_from_candidate_email: candidate email not recognized: %s',
                    candidate_email)
        return None

    return candidate_email_row.candidate_id