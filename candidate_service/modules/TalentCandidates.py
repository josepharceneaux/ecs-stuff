from candidate_service.common.models.candidate import db
from candidate_service.common.models.candidate import (
    Candidate, EmailLabel, CandidateEmail, CandidatePhone, PhoneLabel,
    CandidateWorkPreference, CandidatePreferredLocation, CandidateAddress,
    CandidateExperience, CandidateEducation, CandidateEducationDegree
)
from candidate_service.common.models.email_marketing import (
    EmailCampaign, EmailCampaignSend
)
from candidate_service.common.models.misc import Country
from candidate_service.common.models.user import User
from candidate_service.app import logger
from datetime import date


def does_candidate_belong_to_user(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    """
    candidate_row = db.session.query(Candidate).join(User).filter(
        Candidate.id == candidate_id, Candidate.user_id == user_row.id,
        User.domain_id == user_row.domain_id
    ).first()

    return True if candidate_row else False


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

    # history = None
    # if get_all_fields or 'contact_history' in fields:
    #     history = contact_history(candidate_id=candidate_id)

    return_dict = {
        'id': candidate_id,
        'full_name': full_name,
        'emails': emails,
        'phones': phones,
        'addresses': candidate_addresses,
        'work_experience': candidate_work_experiences,
        'work_preference': candidate_work_preference,
        'preferred_locations': candidate_preferred_locations,
        'educations': candidate_educations,
        # 'contact_history': history
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
                                         month=candidate_experience.start_moth or 1),
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


def date_of_employment(year, month, day=1):
    return date(year, month, day) if year else None


def country_name_from_country_id(country_id):
    if not country_id:
        return 'United States'
    country = db.session.query(Country).get(country_id)
    if country:
        return country.name
    else:
        logger.info('country_name_from_country_id: country_id is not recognized: %s', country_id)
        return 'United States'


# def contact_history(candidate_id):
#     timeline = []
#
#     # Campaign sends & campaigns
#     email_campaign_sends = db.session.query(EmailCampaignSend).filter_by(candidate_id=candidate_id)
#     for email_campaign_send in email_campaign_sends:
#         if not email_campaign_sends.email_campaign_id:
#             logger.error("contact_history: email_campaign_send has no email_campaign_id: %s", email_campaign_send.id)
#             continue
#         email_campaign = db.session.query(EmailCampaign).get(email_campaign_send.email_campaign_id)
#         # todo: complete event_type
#         timeline.insert(0, dict(event_datetime=email_campaign_send.sentTime,
#                                 event_type='',
#                                 campaign_name=email_campaign.name))
#
#     # Sort events by datetime and convert all the datetimes to isoformat
#     timeline = sorted(timeline, key=lambda entry: entry['event_datetime'], reverse=True)
#     for event in timeline:
#         event['event_datetime'] = event['event_datetime'].isoformat()
#
#     return dict(timeline=timeline)
