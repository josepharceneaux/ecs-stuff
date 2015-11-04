"""
Helper functions related to retrieving, creating, updating, and deleting candidates
"""
# Standard libraries
import datetime
from datetime import date

# Database connection and logger
from candidate_service.candidate_app import db, logger

# Models
from candidate_service.common.models.candidate import (
    Candidate, EmailLabel, CandidateEmail, CandidatePhone, PhoneLabel,
    CandidateWorkPreference, CandidatePreferredLocation, CandidateAddress,
    CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField,
    CandidateSocialNetwork, SocialNetwork, CandidateEducationDegreeBullet,
    CandidateExperienceBullet
)
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.email_marketing import (EmailCampaign, EmailCampaignSend)
from candidate_service.common.models.misc import (Country, AreaOfInterest, CustomField)
from candidate_service.common.models.user import User

# Error handling
from common.error_handling import InvalidUsage

# Validations
from common.utils.validators import (sanitize_zip_code, is_number)

# Common utilities
from common.utils.common_functions import get_coordinates


##################################################
# Helper Functions For Retrieving Candidate Info #
##################################################
def fetch_candidate_info(candidate_id, fields=None):
    """
    Fetch for candidate object via candidate's id
    :type       candidate_id: int
    :type       fields: None | str

    :return:    Candidate dict
    :rtype:     dict[str, T]
    """
    assert isinstance(candidate_id, int)
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
        emails = email_label_and_address(candidate=candidate)

    phones = None
    if get_all_fields or 'phones' in fields:
        phones = phone_label_and_value(candidate=candidate)

    candidate_addresses = None
    if get_all_fields or 'addresses' in fields:
        candidate_addresses = addresses(candidate=candidate)

    candidate_work_experiences = None
    if get_all_fields or 'work_experiences' in fields:
        candidate_work_experiences = work_experiences(candidate_id=candidate_id)

    candidate_work_preference = None
    if get_all_fields or 'work_preferences' in fields:
        candidate_work_preference = work_preference(candidate=candidate)

    candidate_preferred_locations = None
    if get_all_fields or 'preferred_locations' in fields:
        candidate_preferred_locations = preferred_locations(candidate=candidate)

    candidate_educations = None
    if get_all_fields or 'educations' in fields:
        candidate_educations = educations(candidate=candidate)

    candidate_skills = None
    if get_all_fields or 'skills' in fields:
        candidate_skills = skills(candidate=candidate)

    candidate_interests = None
    if get_all_fields or 'areas_of_interest' in fields:
        candidate_interests = areas_of_interest(candidate_id=candidate_id)

    candidate_military_services = None
    if get_all_fields or 'military_services' in fields:
        candidate_military_services = military_services(candidate=candidate)

    candidate_custom_fields = None
    if get_all_fields or 'custom_fields' in fields:
        candidate_custom_fields = custom_fields(candidate=candidate)

    candidate_social_networks = None
    if get_all_fields or 'social_networks' in fields:
        candidate_social_networks = social_network_name_and_url(candidate=candidate)

    history = None
    if get_all_fields or 'contact_history' in fields:
        history = contact_history(candidate=candidate)

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


def email_label_and_address(candidate):
    candidate_emails = candidate.candidate_emails
    return [{
                'label': db.session.query(EmailLabel).get(email.email_label_id).description,
                'address': email.address
            } for email in candidate_emails]


def phone_label_and_value(candidate):
    candidate_phones = candidate.candidate_phones
    return [{
                'label': db.session.query(PhoneLabel).get(phone.phone_label_id).description,
                'value': phone.value
            } for phone in candidate_phones]


def addresses(candidate):
    candidate_addresses = candidate.candidate_addresses
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
    candidate_experiences = db.session.query(CandidateExperience). \
        filter_by(candidate_id=candidate_id). \
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


def work_preference(candidate):
    candidate_work_preference = candidate.candidate_work_preferences
    return {
        'authorization': candidate_work_preference.authorization,
        'employment_type': candidate_work_preference.tax_terms,
        'security_clearance': candidate_work_preference.security_clearance,
        'willing_to_relocate': candidate_work_preference.relocate,
        'telecommute': candidate_work_preference.telecommute,
        'travel_percentage': candidate_work_preference.travel_percentage,
        'third_party': candidate_work_preference.third_party
    } if candidate_work_preference else None


def preferred_locations(candidate):
    candidate_preferred_locations = candidate.candidate_preferred_locations
    return [{
                'address': preferred_location.address,
                'city': preferred_location.city,
                'region': preferred_location.region,
                'country': country_name_from_country_id(country_id=preferred_location.country_id)
            } for preferred_location in candidate_preferred_locations]


def educations(candidate):
    candidate_educations = candidate.candidate_educations
    return [{
                'school_name': education.school_name,
                'degree_details': degree_info(education_id=education.id),
                'city': education.city,
                'state': education.state,
                'country': country_name_from_country_id(country_id=education.country_id)
            } for education in candidate_educations]


def degree_info(education_id):
    education = db.session.query(CandidateEducationDegree). \
        filter_by(candidate_education_id=education_id)
    return [{
                'degree_title': degree.degree_title,
                'degree_type': degree.degree_type,
                'start_date': degree.start_time.date().isoformat() if degree.start_time else None,
                'end_date': degree.end_time.date().isoformat() if degree.end_time else None
            } for degree in education]


def skills(candidate):
    candidate_skills = candidate.candidate_skills
    return [{
                'name': skill.description,
                'month_used': skill.total_months,
                'last_used_date': skill.last_used.isoformat() if skill.last_used else None
            } for skill in candidate_skills]


def areas_of_interest(candidate_id):
    candidate_interests = db.session.query(CandidateAreaOfInterest). \
        filter_by(candidate_id=candidate_id)
    return [{
                'id': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).id,
                'name': db.session.query(AreaOfInterest).get(interest.area_of_interest_id).description
            } for interest in candidate_interests]


def military_services(candidate):
    candidate_military_experience = candidate.candidate_military_services
    return [{
                'branch': military_info.branch,
                'service_status': military_info.service_status,
                'highest_grade': military_info.highest_grade,
                'highest_rank': military_info.highest_rank,
                'start_date': military_info.from_date,
                'end_date': military_info.to_date,
                'country': country_name_from_country_id(country_id=military_info.country_id)
            } for military_info in candidate_military_experience]


def custom_fields(candidate):
    candidate_custom_fields = candidate.candidate_custom_fields
    return [{
                'id': candidate_custom_field.custom_field_id,
                'name': db.session.query(CustomField).get(candidate_custom_field.custom_field_id),
                'value': candidate_custom_field.value,
                'created_at_datetime': candidate_custom_field.added_time.isoformat()
            } for candidate_custom_field in candidate_custom_fields]


def social_network_name_and_url(candidate):
    candidate_social_networks = candidate.candidate_social_network
    return [{
                'name': social_network_name(social_network_id=social_network.social_network_id),
                'url': social_network.social_profile_url
            } for social_network in candidate_social_networks]


class ContactHistoryEvent:
    def __init__(self):
        pass

    CREATED_AT = 'created_at'
    EMAIL_SEND = 'email_send'
    EMAIL_OPEN = 'email_open'  # Todo: Implement opens and clicks into timeline
    EMAIL_CLICK = 'email_click'


def contact_history(candidate):
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
    candidate_email_row = db.session.query(CandidateEmail). \
        filter_by(address=candidate_email).first()
    if not candidate_email_row:
        logger.info('get_candidate_id_from_candidate_email: candidate email not recognized: %s',
                    candidate_email)
        return None

    return candidate_email_row.candidate_id


# TODO: move function to Email Marketing Service
def retrieve_email_campaign_send(email_campaign, candidate_id):
    """
    :param email_campaign:
    :param candidate_id:
    :rtype:     list(dict)
    """
    from candidate_service.common.models.email_marketing import EmailCampaignSend

    email_campaign_send_rows = db.session.query(EmailCampaignSend). \
        filter_by(EmailCampaignSend.email_campaign_id == email_campaign.id,
                  EmailCampaignSend.candidate_id == candidate_id)

    return [{
                'candidate_id': email_campaign_send_row.candidate_id,
                'sent_time': email_campaign_send_row.sent_time
            } for email_campaign_send_row in email_campaign_send_rows]

###########################################
# Helper Functions For Creating Candidate #
###########################################
def create_candidate_from_params(
        user_id,
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
        area_of_interest_ids=None,
        custom_field_ids=None,
        social_networks=None,
        work_experiences=None,
        work_preference=None,
        preferred_locations=None,
        skills=None,
        dice_social_profile_id=None,
        dice_profile_id=None,
        added_time=None,
        domain_can_read=None,
        domain_can_write=None,
        source_id=None,
        objective=None,
        summary=None
):
    """
    Function will parse each parameter and create a new Candidate.

    If all parameters are provided, function will also create:
        CandidateAddress, CandidateAreaOfInterest, CandidateCustomField,
        CandidateEducation, CandidateEducationDegree, CandidateEducationDegreeBullet,
        CandidateWorkPreference, CandidateEmail, CandidatePhone,
        CandidateMilitaryService, CandidatePreferredLocation,
        CandidateSkill, CandidateSocialNetwork

    :type user_id:                  int
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
    :type area_of_interest_ids:     list
    :type custom_field_ids:         list
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
    domain_can_read = domain_can_read or 1
    domain_can_write = domain_can_write or 1

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

    # Check if candidate exists
    candidate_id = does_candidate_id_exist(dice_social_profile_id=dice_social_profile_id,
                                           dice_profile_id=dice_profile_id,
                                           domain_id=domain_id,
                                           emails=emails)

    # Return error if candidate_id is found
    if candidate_id:
        logger.info('create_candidate_from_params: Candidate already exists; candidate_id: %s', candidate_id)
        raise InvalidUsage(error_message="Candidate already exists; creation failed.")

    # Add Candidate to db
    candidate = Candidate(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        formatted_name=formatted_name,
        added_time=added_time,
        candidate_status_id=status_id,
        user_id=user_id,
        domain_can_read=domain_can_read,
        domain_can_write=domain_can_write,
        dice_profile_id=dice_profile_id,
        dice_social_profile_id=dice_social_profile_id,
        source_id=source_id,
        objective=objective,
        summary=summary,
        is_dirty=0  # todo: is_dirty cannot be null. This should be removed once the field is successfully removed.
    )
    db.session.add(candidate)
    db.session.flush()
    candidate_id = candidate.id

    # Add Candidate's address(es)
    if addresses:
        address_has_default = any([address.get('is_default') for address in addresses])
        for i, address in enumerate(addresses):
            address_line_1 = address.get('address_line_1')
            address_line_2 = address.get('address_line_2')
            city = address.get('city')
            state = address.get('state')
            country_id = country_id_from_country_name_or_code(address.get('country'))
            zip_code = sanitize_zip_code(address.get('zip_code'))
            po_box = address.get('po_box')
            is_default = address.get('is_default')
            coordinates = get_coordinates(zip_code, city, state)
            # If there's no is_default, the first address should be default
            is_default = i == 0 if address_has_default else is_default

            db.session.add(CandidateAddress(
                candidate_id=candidate_id,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                city=city,
                state=state,
                country_id=country_id,
                zip_code=zip_code,
                po_box=po_box,
                is_default=is_default,
                coordinates=coordinates,
                resume_id=candidate_id  # todo: this is to be removed once all tables have been added & migrated
            ))

    # Add Candidate's areas_of_interest
    if area_of_interest_ids:
        for area_of_interest_id in area_of_interest_ids:
            db.session.add(CandidateAreaOfInterest(
                candidate_id=candidate_id,
                area_of_interest_id=area_of_interest_id
            ))

    # Add Candidate's custom_field(s)
    if custom_field_ids:
        for custom_field_id in custom_field_ids:
            db.session.add(CandidateCustomField(
                candidate_id=candidate_id,
                custom_field_id=custom_field_id,
                added_time=added_time
            ))

    # Add Candidate's education(s)
    if educations:
        for education in educations:

            list_order = education.get('list_order', 1)
            school_name = education.get('school_name')
            school_type = education.get('school_type')
            city = education.get('city')
            state = education.get('state')
            country_id = country_id_from_country_name_or_code(education.get('country'))
            is_current = education.get('is_current')
            candidate_education = CandidateEducation(
                candidate_id=candidate_id,
                list_order=list_order,
                school_name=school_name,
                school_type=school_type,
                city=city,
                state=state,
                country_id=country_id,
                is_current=is_current,
                added_time=added_time,
                resume_id=candidate_id  # todo: this is to be removed once all tables have been added & migrated
            )
            db.session.add(candidate_education)
            db.session.flush()

            # Degree(s)
            candidate_education_id = candidate_education.id
            education_degrees = education.get('degrees')
            assert isinstance(education_degrees, list)
            for education_degree in education_degrees:
                list_order = education_degree.get('list_order', 1)
                degree_type = education_degree.get('type')
                degree_title = education_degree.get('title')
                start_year = education_degree.get('start_year')
                start_month = education_degree.get('start_month')
                end_year = education_degree.get('end_year')
                end_month = education_degree.get('end_month')
                gpa_num = education_degree.get('gpa_num')
                gpa_denom = education_degree.get('gpa_denom')
                classification_type_id = classification_type_id_from_degree_type(degree_type)
                start_time = education_degree.get('start_time')
                end_time = education_degree.get('end_time')
                candidate_education_degree = CandidateEducationDegree(
                    candidate_education_id=candidate_education_id,
                    list_order=list_order,
                    degree_type=degree_type,
                    degree_title=degree_title,
                    start_year=start_year,
                    start_month=start_month,
                    end_year=end_year,
                    end_month=end_month,
                    gpa_num=gpa_num,
                    gpa_denom=gpa_denom,
                    added_time=added_time,
                    classification_type_id=classification_type_id,
                    start_time=start_time,
                    end_time=end_time
                )
                db.session.add(candidate_education_degree)
                db.session.flush()

                # Degree Bullet(s)
                candidate_education_degree_id = candidate_education_degree.id
                degree_bullets = education_degree.get('degree_bullets')
                assert isinstance(degree_bullets, list)
                for degree_bullet in degree_bullets:
                    concentration_type = degree_bullet.get('concentration_type')
                    comments = degree_bullet.get('comments')
                    db.session.add(CandidateEducationDegreeBullet(
                        candidate_education_degree_id=candidate_education_degree_id,
                        concentration_type=concentration_type,
                        comments=comments,
                        added_time=added_time
                    ))

    # Add Candidate's work experience(s)
    if work_experiences:
        for work_experience in work_experiences:

            list_order = work_experience.get('list_order', 1)
            organization = work_experience.get('organization')
            position = work_experience.get('position')
            city = work_experience.get('city')
            state = work_experience.get('state')
            end_month = work_experience.get('end_month')
            start_year = work_experience.get('start_year')
            country_id = country_id_from_country_name_or_code(work_experience.get('country'))
            start_month = work_experience.get('start_month')
            end_year = work_experience.get('end_year')
            is_current = work_experience.get('is_current', 0)
            experience = CandidateExperience(
                candidate_id=candidate_id,
                list_order=list_order,
                organization=organization,
                position=position,
                city=city,
                state=state,
                end_month=end_month,
                start_year=start_year,
                country_id=country_id,
                start_month=start_month,
                end_year=end_year,
                is_current=is_current,
                added_time=added_time,
                resume_id=candidate_id  # todo: this is to be removed once all tables have been added & migrated
            )
            db.session.add(experience)
            db.session.flush()

            experience_id = experience.id
            experience_bullets = work_experience.get('work_experience_bullets')
            assert isinstance(experience_bullets, list)
            for experience_bullet in experience_bullets:
                list_order = experience_bullet.get('list_order', 1)
                description = experience_bullet.get('description')
                db.session.add(CandidateExperienceBullet(
                    candidate_experience_id=experience_id,
                    list_order=list_order,
                    description=description,
                    added_time=added_time
                ))

    # Add Candidate's work preference(s)
    if work_preference:
        db.session.add(CandidateWorkPreference(
            candidate_id=candidate_id,
            relocate=work_preference.get('relocate'),
            authorization=work_preference.get('authorization'),
            telecommute=work_preference.get('telecommute'),
            travel_percentage=work_preference.get('travel_percentage'),
            hourly_rate=work_preference.get('hourly_rate'),
            salary=work_preference.get('salary'),
            tax_terms=work_preference.get('tax_terms')
        ))

    # Add Candidate's email(s)
    if emails:
        emails_has_default = any([email.get('is_default') for email in emails])
        for i, email in enumerate(emails):
            email_address = email.get('address')
            is_default = email.get('is_default')
            email_label_id = email_label_id_from_email_label(email_label=email['label'])
            # If there's no is_default, the first email should be default
            is_default = i == 0 if emails_has_default else is_default

            db.session.add(CandidateEmail(
                candidate_id=candidate_id,
                address=email_address,
                is_default=is_default,
                email_label_id=email_label_id
            ))

    # Add Candidate's phone(s)
    if phones:
        phone_has_default = any([phone.get('is_default') for phone in phones])
        for i, phone in enumerate(phones):
            phone_number = phone.get('value')
            is_default = phone.get('is_default')
            phone_label_id = phone_label_id_from_phone_label(phone_label=phone['label'])
            # If there's no is_default, the first phone should be default
            is_default = i == 0 if phone_has_default else is_default

            db.session.add(CandidatePhone(
                candidate_id=candidate_id,
                value=phone_number,
                is_default=is_default,
                phone_label_id=phone_label_id
            ))

    # Add Candidate's military service(s)
    if military_services:
        for military_service in military_services:
            # Get country_id
            country_id = country_id_from_country_name_or_code(military_service.get('country'))

            db.session.add(CandidateMilitaryService(
                candidate_id=candidate_id,
                country_id=country_id,
                service_status=military_service.get('service_status'),
                highest_rank=military_service.get('highest_rank'),
                highest_grade=military_service.get('highest_grade'),
                branch=military_service.get('branch'),
                comments=military_service.get('comments'),
                from_date=military_service.get('from_date'),
                to_date=military_service.get('to_date'),
                resume_id=candidate_id  # todo: this is to be removed once all tables have been added & migrated
            ))

    # Add Candidate's preferred location(s)
    if preferred_locations:
        for preferred_location in preferred_locations:
            # Get country_id
            country_id = country_id_from_country_name_or_code(preferred_location.get('country'))
            # Validate Zip Code(s)
            zip_code = sanitize_zip_code(preferred_location.get('zip_code'))

            db.session.add(CandidatePreferredLocation(
                candidate_id=candidate_id,
                address=preferred_location.get('address'),
                country_id=country_id,
                city=preferred_location.get('city'),
                region=preferred_location.get('region'),
                zip_code=zip_code,
            ))

    # Add Candidate's skill(s)
    if skills:
        for skill in skills:
            db.session.add(CandidateSkill(
                candidate_id=candidate_id,
                list_order=skill.get('list_order', 1),
                description=skill.get('description'),
                added_time=added_time,
                total_months=skill.get('total_months'),
                last_used=skill.get('last_used'),
                resume_id=candidate_id  # todo: this is to be removed once all tables have been added & migrated
            ))

    # Add Candidate's social_network(s)
    if social_networks:
        for social_network in social_networks:
            # Get social_network_id
            social_network_id = social_network_id_from_name(social_network.get('name'))
            db.session.add(CandidateSocialNetwork(
                candidate_id=candidate_id,
                social_network_id=social_network_id,
                social_profile_url=social_network.get('profile_url')
            ))

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
    for email in emails:
        email_address = email.get('address')
        candidate_email = db.session.query(CandidateEmail).join(Candidate).join(User).filter(
            CandidateEmail.address == email_address, User.domain_id == domain_id
        ).first()
        if candidate_email:
            return candidate_email.candidate_id

    return None


def country_id_from_country_name_or_code(country_name_or_code):
    """
    Function will find and return ID of the country matching with country_name_or_code
    If not match is found, default return is 1 => 'United States'

    :return: Country.id
    """
    from candidate_service.common.models.misc import Country

    all_countries = db.session.query(Country).all()
    if country_name_or_code:
        matching_country_id = next((row.id for row in all_countries
                                    if row.code.lower() == country_name_or_code.lower()
                                    or row.name.lower() == country_name_or_code.lower()), None)
        return matching_country_id
    return 1


def classification_type_id_from_degree_type(degree_type):
    """
    Function will return classification_type ID of the classification_type that matches
    with degree_type. E.g. degree_type = 'Masters' => classification_type_id: 5
    :return:    classification_type_id or None
    """
    matching_classification_type_id = None
    from candidate_service.common.models.candidate import ClassificationType

    if degree_type:
        all_classification_types = db.session.query(ClassificationType).all()
        matching_classification_type_id = next((row.id for row in all_classification_types
                                                if row.code.lower() == degree_type.lower()), None)
    return matching_classification_type_id


def email_label_id_from_email_label(email_label):
    """
    Function retrieves email_label_id from email_label
    e.g. 'Primary' => 1
    :return:  email_label ID if email_label is recognized, otherwise 1 ('Primary')
    """
    email_label_row = db.session.query(EmailLabel).filter_by(description=email_label).first()
    if email_label_row:
        return email_label_row.id
    else:
        logger.error('email_label_id_from_email_label: email_label not recognized: %s', email_label)
        return 1


def phone_label_id_from_phone_label(phone_label):
    """
    Function retrieves phone_label_id from phone_label
    e.g. 'Primary' => 1
    :return:  phone_label ID if phone_label is recognized, otherwise 1 ('Primary')
    """
    phone_label_row = db.session.query(PhoneLabel).filter_by(description=phone_label).first()
    if phone_label_row:
        return phone_label_row.id
    else:
        logger.error('phone_label_id_from_phone_label: phone_label not recognized: %s', phone_label)
        return 1


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
