# TODO: Add file docstring & remove unnecessary import statements
# Standard library
import re
from datetime import datetime
from copy import deepcopy
from decimal import Decimal

import phonenumbers
import pycountry
from nameparser import HumanName

# SQLAlchemy Models
from graphql_service.common.models.db import db
from graphql_service.common.models.candidate import CandidateEmail, PhoneLabel
from graphql_service.common.models.misc import AreaOfInterest

# Helpers
from graphql_service.common.utils.handy_functions import purge_dict
from graphql_service.common.utils.validators import is_valid_email, sanitize_zip_code, parse_phone_number
from graphql_service.common.geo_services.geo_coordinates import get_coordinates

from helpers import remove_duplicates

from graphql_service.common.utils.datetime_utils import DatetimeUtils


def add_or_edit_candidate_from_params(user_id, primary_data, is_updating=False,
                                      retrieved_candidate=None, addresses=None, educations=None,
                                      emails=None, phones=None, areas_of_interest=None,
                                      candidate_custom_fields=None, experiences=None, military_services=None,
                                      preferred_locations=None, references=None, skills=None, social_networks=None,
                                      tags=None, notes=None, work_preference=None, photos=None, updated_datetime=None):
    # TODO: Add/improve docstrings & comments
    # TODO: Include error handling
    # TODO: Complete all checks and validations
    # TODO: Track all edits (including deletes)

    assert isinstance(primary_data, dict), "Candidate's primary data must be of type dict"

    candidate_data = primary_data.copy()
    added_datetime = candidate_data.get('added_datetime')

    if primary_data and is_updating:
        validated_primary_data = _update_candidates_primary_data(candidate_data, updated_datetime)
        candidate_data = validated_primary_data

    # Areas of Interest
    # if areas_of_interest:
    #     validated_areas_of_interest = _add_or_edit_areas_of_interest(areas_of_interest, added_datetime)
    #     candidate_data['areas_of_interest'] = validated_areas_of_interest

    # Addresses
    if addresses:
        validated_addresses_data = _add_or_update_addresses(addresses=addresses,
                                                            added_datetime=added_datetime,
                                                            is_updating=is_updating)
        candidate_data['addresses'] = validated_addresses_data

    # Custom Fields

    # Edits

    # Educations
    if educations:
        validated_educations_data = _add_or_edit_educations(educations, added_datetime)
        candidate_data['educations'] = validated_educations_data

    # Emails
    if emails:
        validated_emails_data = _add_or_edit_emails(emails=emails, added_datetime=added_datetime)
        candidate_data['emails'] = validated_emails_data

    # Experiences
    if experiences:
        validated_experiences_data = _add_or_edit_experiences(experiences, added_datetime)
        candidate_data['experiences'] = validated_experiences_data

    # Military Services
    if military_services:
        validated_military_services_data = _add_or_edit_military_services(military_services, added_datetime)
        candidate_data['military_services'] = validated_military_services_data

    # Notes
    if notes:
        validated_notes_data = _add_or_edit_notes(notes, user_id, added_datetime)
        candidate_data['notes'] = validated_notes_data

    # Phones
    if phones:
        validated_phones_data = _add_or_edit_phones(phones, added_datetime)
        candidate_data['phones'] = validated_phones_data

    # Photos
    if photos:
        validated_photos_data = _add_or_edit_photos(photos, added_datetime)
        candidate_data['photos'] = validated_photos_data

    # Preferred Locations
    if preferred_locations:
        validated_preferred_locations_data = _add_or_edit_preferred_locations(preferred_locations, added_datetime)
        candidate_data['preferred_locations'] = validated_preferred_locations_data

    # References
    if references:
        validated_references_data = _add_or_edit_references(references, added_datetime)
        candidate_data['references'] = validated_references_data

    # Skills
    if skills:
        validated_skills_data = _add_or_edit_skills(skills, added_datetime)
        candidate_data['skills'] = validated_skills_data

    # Social Networks
    if social_networks:
        validated_social_networks_data = _add_or_edit_social_networks(social_networks, added_datetime)
        candidate_data['social_networks'] = validated_social_networks_data

    # Subscription Preferences
    # Tags
    if tags:
        validated_tags_data = _add_or_edit_tags(tags, added_datetime)
        candidate_data['tags'] = validated_tags_data

    # Talent Pools
    # Views

    # Work Preference
    if work_preference:
        validated_work_preference_data = _add_or_edit_work_preference(work_preference, added_datetime)
        candidate_data['work_preference'] = validated_work_preference_data

    return candidate_data


def _update_candidates_primary_data(primary_data, updated_datetime):
    """
    """
    update_dict = dict(
        first_name=primary_data.get('first_name'),
        middle_name=primary_data.get('middle_name'),
        last_name=primary_data.get('last_name'),
        source_id=primary_data.get('source_id'),
        status_id=primary_data.get('status_id'),
        objective=primary_data.get('objective'),
        summary=primary_data.get('summary'),
        resume_url=primary_data.get('resume_url'),
        updated_datetime=updated_datetime
    )

    # Remove empty data
    update_dict = purge_dict(update_dict)

    # Candidate will not be updated if update_dict is empty
    if not update_dict:
        return

    return update_dict


# TODO: complete function
# def _add_or_edit_areas_of_interest(areas_of_interest, user, added_datetime):
#     # Aggregate formatted & validated areas of interest
#     validated_areas_of_interest = []
#
#     aoi_ids = set()
#     for area_of_interest in areas_of_interest:
#         aoi_id = area_of_interest.get('area_of_interest_id')
#         if aoi_id:
#             if not AreaOfInterest.get(aoi_id):
#                 raise Exception
#         aoi_ids.add(aoi_id)
#
#     # TODO: Add this validation earlier in the code
#     if aoi_ids:
#         exists = AreaOfInterest.query.filter(AreaOfInterest.id.in_(aoi_ids),
#                                              AreaOfInterest.domain_id != user.domain_id).count() == 0
#         if not exists:
#             raise Exception
#
#     # TODO: Prevent duplicate insertions


def _add_or_update_addresses(addresses, added_datetime, is_updating=False):
    # Aggregate formatted & validated address data
    validated_addresses_data = []

    # Check if any of the addresses is set as the default address
    addresses_have_default = [isinstance(address.get('is_default'), bool) for address in addresses]

    for i, address in enumerate(addresses):
        zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
        city = clean(address.get('city'))
        iso3166_subdivision = address.get('iso3166_subdivision')

        address_dict = dict(
            address_line_1=address.get('address_line_1'),
            address_line_2=address.get('address_line_2'),
            added_datetime=added_datetime,
            zip_code=zip_code,
            city=city,
            iso3166_subdivision=iso3166_subdivision,
            iso3166_country=address.get('iso3166_country'),
            po_box=clean(address.get('po_box')),
            is_default=i == 0 if not addresses_have_default else address.get('is_default'),
            coordinates=get_coordinates(zipcode=zip_code, city=city, state=iso3166_subdivision)
        )

        # Remove empty data from address dict
        address_dict = purge_dict(address_dict)

        validated_addresses_data.append(address_dict)

    return remove_duplicates(validated_addresses_data)


# TODO: complete function's operation/logic
# def _add_or_edit_custom_fields(custom_fields, added_datetime):
#     pass


def _add_or_edit_educations(educations, added_datetime):
    # Aggregate formatted & validated education data
    validated_education_data = []

    for i, education in enumerate(educations):
        validated_education_data.append(dict(
            school_name=education.get('school_name'),
            school_type=education.get('school_type'),
            city=education.get('city'),
            iso3166_country=(education.get('iso3166_country') or '').upper(),
            iso3166_subdivision=(education.get('iso3166_subdivision') or '').upper(),
            is_current=education.get('is_current'),
            added_datetime=education.get('added_datetime') or added_datetime,
            updated_datetime=DatetimeUtils.to_utc_str(datetime.utcnow())
        ))

        degrees = education.get('degrees')
        if degrees:
            # Aggregate formatted & validated degree data
            checked_degree_data = []

            for degree in degrees:
                # Because DynamoDB is too cool for floats
                gpa = Decimal(degree['gpa']) if degree.get('gpa') else None

                checked_degree_data.append(dict(
                    added_datetime=degree.get('added_datetime') or added_datetime,
                    # updated_datetime=updated_datetime,
                    start_year=degree.get('start_year'),
                    start_month=degree.get('start_month'),
                    end_year=degree.get('end_year'),
                    end_month=degree.get('end_month'),
                    gpa=gpa,
                    degree_type=degree.get('degree_type'),
                    degree_title=degree.get('degree_title'),
                    concentration=degree.get('concentration'),
                    comments=degree.get('comments')
                ))

            # Aggregate degree data to the corresponding education data
            validated_education_data[i]['degrees'] = checked_degree_data

    return validated_education_data


def _add_or_edit_emails(emails, added_datetime):
    # Aggregate formatted & validated email data
    validated_email_data = []

    # Check if any of the emails is set as the default email
    emails_have_default = [isinstance(email.get('is_default'), bool) for email in emails]

    for i, email in enumerate(emails):
        # Label
        label = (email.get('label') or '').title()
        if not label or label not in CandidateEmail.labels_mapping.keys():
            label = 'Other'

        # First email will be set as default if no other email is set as default
        default = i == 0 if not any(emails_have_default) else email.get('is_default')

        validated_email_data.append(
            dict(label=label, address=clean(email.get('address')),
                 is_default=default, added_datetime=added_datetime)
        )

    return remove_duplicates(validated_email_data)


def _add_or_edit_experiences(experiences, added_datetime):
    # Aggregate formatted & validated experiences data
    validated_experiences_data = []

    # Identify experiences' maximum start year
    latest_start_year = max(experience.get('start_year') for experience in experiences)

    for experience in experiences:
        start_year, end_year = experience.get('start_year'), experience.get('end_year')
        is_current = experience.get('is_current')

        # End year of experience must be none if it's candidate's current job
        if is_current:
            end_year = None

        if start_year:
            # If end_year is not provided and experience is candidate's current job, set end year to current year
            if not end_year and (start_year == latest_start_year):
                end_year = datetime.utcnow().year
            # if end_year is not provided, and it's not the latest job, end_year will be latest job's start_year + 1
            elif not end_year and (start_year != latest_start_year):
                end_year = start_year + 1

        # Start year must not be greater than end year
        if (start_year and end_year) and start_year > end_year:
            raise Exception

        country_code = clean(experience.get('iso3166_country')).upper()
        subdivision_code = clean(experience.get('iso3166_subdivision')).upper()

        experience_dict = dict(
            organization=clean(experience.get('organization')),
            position=clean(experience.get('position')),
            city=clean(experience.get('city')),
            iso3166_subdivision=subdivision_code,
            iso3166_country=country_code,
            start_year=start_year,
            start_month=experience.get('start_month') or 1,
            end_year=end_year,
            end_month=experience.get('end_month') or 1,
            is_current=is_current,
            description=clean(experience.get('description')),
            added_datetime=added_datetime
        )

        # TODO: add validations & accumulate total months experience for candidate

        validated_experiences_data.append(experience_dict)

    return validated_experiences_data


def _add_or_edit_military_services(military_services, added_datetime):
    # Aggregate formatted & validated military services' data
    validated_military_services_data = []

    for service in military_services:
        service_dict = dict(
            iso3166_country=service.get('iso3166_country').upper(),
            service_status=service.get('status'),
            highest_rank=service.get('highest_rank'),
            highest_grade=service.get('highest_grade'),
            branch=service.get('branch'),
            comments=service.get('comments'),
            start_year=service.get('start_year'),
            start_month=service.get('start_month'),
            end_year=service.get('end_year'),
            end_month=service.get('end_month'),
            added_datetime=added_datetime
        )

        # Remove keys with empty values
        service_dict = purge_dict(service_dict)

        validated_military_services_data.append(service_dict)

    return validated_military_services_data


def _add_or_edit_notes(notes, user_id, added_datetime):
    # Aggregate formatted & validated notes' data
    checked_notes_data = []

    for note in notes:
        note_dict = dict(
            owner_user_id=user_id,
            title=note.get('title'),
            comment=note.get('comment'),
            added_datetime=added_datetime
        )

        # Remove empty data
        note_dict = purge_dict(note_dict)

        checked_notes_data.append(note_dict)

    return checked_notes_data


def _add_or_edit_phones(phones, added_datetime):
    # Aggregate formatted & validated phones' data
    checked_phones_data = []

    # Check if phone label and default have been provided
    phones_have_label = any([phone.get('label') for phone in phones])
    phones_have_default = any([isinstance(phone.get('is_default'), bool) for phone in phones])

    # If duplicate phone numbers are provided, we will only use one of them
    seen = set()
    for phone in phones:
        phone_value = phone.get('value')
        if phone_value and phone_value in seen:
            phones.remove(phone)
        seen.add(phone_value)

    for index, phone in enumerate(phones):

        # If there is no default value, the first phone should be set as the default phone
        is_default = index == 0 if not phones_have_default else phone.get('is_default')

        # If there's no label, the first phone's label will be 'Home', rest will be 'Other'
        phone_label = PhoneLabel.DEFAULT_LABEL if (not phones_have_label and index == 0) \
            else clean(phone.get('label')).title()

        # Phone number must contain at least 7 digits
        # http://stackoverflow.com/questions/14894899/what-is-the-minimum-length-of-a-valid-international-phone-number
        value = clean(phone.get('value'))
        number = re.sub('\D', '', value)
        if len(number) < 7:
            print("Phone number ({}) must be at least 7 digits".format(value))

        iso3166_country_code = phone.get('iso3166_country')
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

        phone_dict = dict(
            value=value,
            extension=phone_number_obj.extension if phone_number_obj else None,
            label=phone_label,
            is_default=is_default,
            added_datetime=added_datetime
        )

        # Remove keys with empty values
        phone_dict = purge_dict(phone_dict)

        # Prevent adding empty records to db
        if not phone_dict:
            continue

        # Save data
        checked_phones_data.append(phone_dict)

    return checked_phones_data


def _add_or_edit_photos(photos, added_datetime):
    # Aggregate formatted & validated photos' data
    checked_photos_data = []

    # Check if of candidate's photos has is_default set to true
    photo_has_default = any(photo.get('is_default') for photo in photos)

    # todo: if photo_has_default; all other photos' is_default must be set to false

    for index, photo in enumerate(photos):
        # If there is no default value, the first photo will be set as the default photo
        is_default = index == 0 if not photo_has_default else photo.get('is_default')

        photo_dict = dict(
            image_url=photo['image_url'],
            is_default=is_default,
            added_datetime=added_datetime
        )

        # todo: prevent duplicate insertions

        checked_photos_data.append(photo_dict)

    return checked_photos_data


def _add_or_edit_preferred_locations(preferred_locations, added_datetime):
    # Aggregate formatted & validated preferred locations' data
    checked_preferred_locations_data = []

    for preferred_location in preferred_locations:
        preferred_location_dict = dict(
            iso3166_country=clean(preferred_location.get('iso3166_country')).upper(),
            iso3166_subdivision=clean(preferred_location.get('iso3166_subdivision')).upper(),
            city=clean(preferred_location.get('city')),
            zip_code=sanitize_zip_code(preferred_location.get('zip_code')),
            added_datetime=added_datetime
        )

        # Remove empty data
        preferred_location_dict = purge_dict(preferred_location_dict, strip=False)

        # todo: prevent duplicate insertions

        checked_preferred_locations_data.append(preferred_location_dict)

    return checked_preferred_locations_data


def _add_or_edit_references(references, added_datetime):
    # Aggregate formatted & validated references' data
    checked_references_data = []

    for reference in references:
        reference_dict = dict(
            reference_name=reference.get('reference_name'),
            reference_email=reference.get('reference_email'),
            reference_phone=reference.get('reference_phone'),
            reference_web_address=reference.get('reference_web_address'),
            position_title=reference.get('position_title'),
            comments=reference.get('comments'),
            added_datetime=added_datetime
        )

        # Remove empty data
        reference_dict = purge_dict(reference_dict)

        # todo: prevent duplicate insertions

        checked_references_data.append(reference_dict)

    return checked_references_data


def _add_or_edit_skills(skills, added_datetime):
    # Aggregate formatted & validated skills' data
    checked_skills_data = []

    for skill in skills:
        skill_dict = dict(
            name=skill.get('name'),
            months_used=skill.get('months_used'),
            last_used_year=skill.get('last_used_year'),
            last_used_month=skill.get('last_used_month'),
            added_datetime=added_datetime
        )

        # Remove empty data
        skill_dict = purge_dict(skill_dict)

        # todo: prevent duplicate insertions

        checked_skills_data.append(skill_dict)

    return checked_skills_data


def _add_or_edit_social_networks(social_networks, added_datetime):
    # Aggregate formatted & validated social networks' data
    checked_social_networks_data = []

    for social_network in social_networks:
        social_network_dict = dict(
            name=social_network.get('name'),
            profile_url=social_network.get('profile_url'),
            added_datetime=added_datetime
        )

        # todo: prevent duplicate insertions

        checked_social_networks_data.append(social_network_dict)

    return checked_social_networks_data


def _add_or_edit_tags(tags, added_datetime):
    # Aggregate formatted & validated tags' data
    checked_tags_data = []

    for tag in tags:
        # todo: prevent duplicate insertions

        checked_tags_data.append(dict(name=tag['name'], added_datetime=added_datetime))

    return checked_tags_data


def _add_or_edit_work_preference(work_preference, added_datetime):
    # todo: candidate should have only one work preference
    return work_preference


def clean(value):
    """
    :rtype: str
    """
    return (value or '').strip()
