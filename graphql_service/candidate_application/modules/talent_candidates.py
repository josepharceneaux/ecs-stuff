# TODO: Add file docstring & remove unnecessary import statements
# Standard library
import re
from datetime import datetime
from decimal import Decimal

import phonenumbers

# SQLAlchemy Models
from graphql_service.common.models.db import db
from graphql_service.common.models.candidate import Candidate, CandidateEmail, PhoneLabel
from graphql_service.common.models.user import User
from graphql_service.common.models.misc import AreaOfInterest, CustomField

# Helpers
from graphql_service.common.utils.handy_functions import purge_dict
from graphql_service.common.utils.validators import is_valid_email, sanitize_zip_code, parse_phone_number
from graphql_service.common.geo_services.geo_coordinates import get_coordinates
from helpers import track_updates
from helpers import remove_duplicates, clean

# Error handling
from graphql_service.common.error_handling import InvalidUsage, ForbiddenError


def add_or_edit_candidate_from_params(
        user,
        primary_data,
        is_updating=False,
        candidate_id=None,
        existing_candidate_data=None,
        addresses=None,
        educations=None,
        emails=None,
        phones=None,
        areas_of_interest=None,
        candidate_custom_fields=None,
        experiences=None,
        military_services=None,
        preferred_locations=None,
        references=None,
        skills=None,
        social_networks=None,
        tags=None,
        notes=None,
        work_preferences=None,
        photos=None,
        added_datetime=None,
        updated_datetime=None):
    """
    Function will add or update candidate.
    :param user: authorized user
    :type  user: User
    :param primary_data: candidate's top level data that is stored in Candidate-table
    :type  primary_data: dict
    :type is_updating:  bool
    :param existing_candidate_data:
    :param addresses: candidate's address collection
    :type  addresses: list
    :param educations: candidate's education collection
    :type  educations: list
    :param emails: candidate's email collection
    :type  emails: list
    :param phones: candidate's phone collection
    :type  phones: list
    :param areas_of_interest: candidate's area of interest collection
    :type  areas_of_interest: list
    :param candidate_custom_fields: candidate's custom field collection
    :type  candidate_custom_fields: list
    :param experiences: candidate's work experience collection
    :type  experiences: list
    :param military_services: candidate's military service collection
    :type  military_services: list
    :param preferred_locations: candidate's job preferred location collection
    :type  preferred_locations: list
    :param references: candidate's reference collection
    :type  references: list
    :param skills: candidate's skill set
    :type  skills: list
    :param social_networks: candidate's social network collection
    :type  social_networks: list
    :param tags: candidate's tag collection
    :type  tags: list
    :param notes: notes about the candidate
    :type  notes: list
    :param work_preferences: candidate's work preferences
    :type  work_preferences: list
    :param photos: candidate's photos collection
    :type  photos: list
    :param added_datetime: timestamp of creation
    :type  added_datetime: str
    :param updated_datetime: timestamp of profile update
    :type  updated_datetime: str
    :rtype: dict
    """
    # TODO: Add/improve docstrings & comments
    # TODO: Complete all checks and validations
    # TODO: Track all edits (including deletes)

    assert isinstance(primary_data, dict), "Candidate's primary data must be of type dict"

    candidate_data = primary_data.copy()

    # Candidate's primary data such as first_name, last_name, objective, summary, etc.
    if primary_data:
        validated_primary_data = _primary_data(primary_data=candidate_data,
                                               user_id=user.id,
                                               existing_data=existing_candidate_data,
                                               added_datetime=added_datetime,
                                               is_updating=is_updating,
                                               updated_datetime=updated_datetime,
                                               candidate_id=candidate_id)
        candidate_data = validated_primary_data

    # Areas of Interest
    if areas_of_interest:
        validated_areas_of_interest = _add_or_update_areas_of_interest(areas_of_interest, user)
        candidate_data['areas_of_interest'] = validated_areas_of_interest

    # Addresses
    if addresses:
        validated_addresses_data = _add_or_update_addresses(addresses=addresses,
                                                            user_id=user.id,
                                                            is_updating=is_updating,
                                                            existing_data=existing_candidate_data,
                                                            candidate_id=candidate_id)
        candidate_data['addresses'] = validated_addresses_data

    # Custom Fields
    if candidate_custom_fields:
        validated_custom_fields_data = _add_or_update_custom_fields(candidate_custom_fields, user)
        candidate_data['candidate_custom_fields'] = validated_custom_fields_data

    # Educations
    if educations:
        validated_educations_data = _add_or_update_educations(educations)
        candidate_data['educations'] = validated_educations_data

    # Emails
    if emails:
        validated_emails_data = _add_or_update_emails(emails=emails,
                                                      is_updating=is_updating,
                                                      user_id=user.id,
                                                      existing_data=existing_candidate_data,
                                                      candidate_id=candidate_id)
        candidate_data['emails'] = validated_emails_data

    # Experiences
    if experiences:
        validated_experiences_data = _add_or_update_experiences(experiences)
        candidate_data['experiences'] = validated_experiences_data

    # Military Services
    if military_services:
        validated_military_services_data = _add_or_update_military_services(military_services)
        candidate_data['military_services'] = validated_military_services_data

    # Notes
    if notes:
        validated_notes_data = _add_or_update_notes(notes, user.id)
        candidate_data['notes'] = validated_notes_data

    # Phones
    if phones:
        validated_phones_data = _add_or_update_phones(phones)
        candidate_data['phones'] = validated_phones_data

    # Photos
    if photos:
        validated_photos_data = _add_or_update_photos(photos, is_updating)
        candidate_data['photos'] = validated_photos_data

    # Preferred Locations
    if preferred_locations:
        validated_preferred_locations_data = _add_or_update_preferred_locations(preferred_locations)
        candidate_data['preferred_locations'] = validated_preferred_locations_data

    # References
    if references:
        validated_references_data = _add_or_update_references(references)
        candidate_data['references'] = validated_references_data

    # Skills
    if skills:
        validated_skills_data = _add_or_update_skills(skills)
        candidate_data['skills'] = validated_skills_data

    # Social Networks
    if social_networks:
        validated_social_networks_data = _add_or_update_social_networks(social_networks)
        candidate_data['social_networks'] = validated_social_networks_data

    # Subscription Preferences
    # Tags
    if tags:
        validated_tags_data = _add_or_update_tags(tags)
        candidate_data['tags'] = validated_tags_data

    # Talent Pools
    # Views

    # Work Preference
    if work_preferences:
        validated_work_preference_data = _add_or_update_work_preferences(work_preferences)
        candidate_data['work_preferences'] = validated_work_preference_data

    return candidate_data


def _primary_data(primary_data, user_id=None, existing_data=None, added_datetime=None,
                  is_updating=False, updated_datetime=None, candidate_id=None):
    """
    Function will return candidate's validated primary data
    :rtype: dict
    """
    primary_dict_data = dict(
        first_name=primary_data.get('first_name'),
        middle_name=primary_data.get('middle_name'),
        last_name=primary_data.get('last_name'),
        source_id=primary_data.get('source_id'),
        status_id=primary_data.get('status_id'),
        objective=primary_data.get('objective'),
        summary=primary_data.get('summary'),
        resume_url=primary_data.get('resume_url')
    )

    # Remove empty data
    primary_dict_data = purge_dict(primary_dict_data)

    # added_datetime must be included if candidate is not being updated & primary_dict_data is not empty at this point
    if not is_updating:
        assert added_datetime is not None, 'added_datetime is required when creating candidate'
        primary_dict_data['id'] = primary_data['id']
        primary_dict_data['added_datetime'] = added_datetime

    # Add updated_datetime if candidate is being updated
    if is_updating:
        assert updated_datetime is not None, 'updated_datetime is required when updating candidate'
        assert candidate_id is not None, 'candidate ID is required for tracking updates'

        # Track all changes made to candidate's primary information
        track_updates(user_id=user_id,
                      candidate_id=candidate_id,
                      existing_data=existing_data,
                      new_data=primary_dict_data)

        # Add stringified datetime into primary_dict_data
        primary_dict_data['updated_datetime'] = updated_datetime

    return primary_dict_data


def _add_or_update_areas_of_interest(areas_of_interest, user):
    # Remove duplicate data
    areas_of_interest = remove_duplicates(areas_of_interest)

    # Area of interest IDs must belong to candidate's domain
    aoi_ids = [aoi['area_of_interest_id'] for aoi in areas_of_interest]
    if not AreaOfInterest.query.filter(
            AreaOfInterest.id.in_(aoi_ids), AreaOfInterest.domain_id != user.domain_id).count() == 0:
        raise ForbiddenError("Area of interest IDs must belong to user's domain")

    # TODO: track updates

    return areas_of_interest


def _add_or_update_addresses(addresses, user_id=None, is_updating=None, existing_data=None, candidate_id=None):
    # Remove duplicates
    addresses = remove_duplicates(addresses)

    # Aggregate formatted & validated address data
    validated_addresses_data = []

    # Check if any of the addresses is set as the default address
    addresses_have_default = [isinstance(address.get('is_default'), bool) for address in addresses]

    for index, address in enumerate(addresses):
        zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
        city = clean(address.get('city'))
        iso3166_subdivision = address.get('iso3166_subdivision')

        address_dict = dict(
            address_line_1=address.get('address_line_1'),
            address_line_2=address.get('address_line_2'),
            zip_code=zip_code,
            city=city,
            iso3166_subdivision=iso3166_subdivision,
            iso3166_country=address.get('iso3166_country'),
            po_box=clean(address.get('po_box')),
            is_default=index == 0 if not addresses_have_default else address.get('is_default'),
            coordinates=get_coordinates(zipcode=zip_code, city=city, state=iso3166_subdivision)
        )

        # Remove empty data from address dict
        address_dict = purge_dict(address_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('addresses')[index],
                          new_data=address_dict,
                          attribute='address')

        # Prevent adding empty records
        if not address_dict:
            continue

        validated_addresses_data.append(address_dict)

    return validated_addresses_data


def _add_or_update_custom_fields(custom_fields, user):
    # Remove duplicate data
    custom_fields = remove_duplicates(custom_fields)

    # Custom field IDs must belong to candidate's domain
    custom_field_ids = [custom_field['id'] for custom_field in custom_fields]
    if not CustomField.query.filter(
            CustomField.id.in_(custom_field_ids), CustomField.domain_id != user.domain_id).count() == 0:
        raise ForbiddenError("Custom field IDs must belong to user's domain")

    # TODO: track updates

    return map(purge_dict, custom_fields)


def _add_or_update_educations(educations, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicates
    educations = remove_duplicates(educations)

    # Aggregate formatted & validated education data
    validated_education_data = []

    for index, education in enumerate(educations):
        education_dict = dict(
            school_name=education.get('school_name'),
            school_type=education.get('school_type'),
            city=education.get('city'),
            iso3166_country=(education.get('iso3166_country') or '').upper(),
            iso3166_subdivision=(education.get('iso3166_subdivision') or '').upper(),
            is_current=education.get('is_current')
        )

        # Remove empty data
        education_dict = purge_dict(education_dict)

        # track updates
        if is_updating:
            existing_education = existing_data.get('educations')[index]
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_education,
                          new_data=education_dict,
                          attribute='education')

        # Prevent adding empty records
        if not education_dict:
            continue

        validated_education_data.append(education_dict)

        degrees = education.get('degrees')
        if degrees:
            # Remove duplicates
            degrees = remove_duplicates(degrees)  # todo: may not be necessary

            # Aggregate formatted & validated degree data
            checked_degree_data = []

            for i, degree in enumerate(degrees):
                # Because DynamoDB is too cool for floats
                gpa = Decimal(degree['gpa']) if degree.get('gpa') else None

                degree_dict = dict(
                    start_year=degree.get('start_year'),
                    start_month=degree.get('start_month'),
                    end_year=degree.get('end_year'),
                    end_month=degree.get('end_month'),
                    gpa=gpa,
                    degree_type=degree.get('degree_type'),
                    degree_title=degree.get('degree_title'),
                    concentration=degree.get('concentration'),
                    comments=degree.get('comments')
                )

                # Remove empty data
                degree_dict = purge_dict(degree_dict)

                # track updates
                if is_updating:
                    existing_degrees = existing_education
                    track_updates(user_id=user_id,
                                  candidate_id=candidate_id,
                                  existing_data=existing_degrees[i],
                                  new_data=degree_dict,
                                  attribute='education_degree')

                # Prevent adding empty records
                if not degree_dict:
                    continue

                checked_degree_data.append(degree_dict)

            # Aggregate degree data to the corresponding education data
            validated_education_data[index]['degrees'] = checked_degree_data

    return validated_education_data


def _add_or_update_emails(emails, is_updating, user_id=None, existing_data=None, candidate_id=None):
    # Remove duplicates
    emails = remove_duplicates(emails)

    # Aggregate formatted & validated email data
    validated_emails_data = []

    # Check if any of the emails is set as the default email
    emails_have_default = [isinstance(email.get('is_default'), bool) for email in emails]

    for i, email in enumerate(emails):
        # Label
        label = (email.get('label') or '').title()
        if not label or label not in CandidateEmail.labels_mapping.keys():
            label = 'Other'

        # First email will be set as default if no other email is set as default
        default = i == 0 if not any(emails_have_default) else email.get('is_default')

        email_address = clean(email.get('address'))
        email_dict = dict(label=label, address=email_address, is_default=default)

        # Email address must be valid
        if email_address and not is_valid_email(email_address):
            raise InvalidUsage(error_message='Invalid email address')

        # Remove empty data
        email_dict = purge_dict(email_dict, strip=False)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('emails')[i],
                          new_data=email_dict,
                          attribute='email')

        # Prevent adding empty records
        if not email_dict:
            continue

        validated_emails_data.append(email_dict)

    return validated_emails_data


def _add_or_update_experiences(experiences, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicates
    experiences = remove_duplicates(experiences)

    # Aggregate formatted & validated experiences data
    validated_experiences_data = []

    # Identify experiences' maximum start year
    latest_start_year = max(experience.get('start_year') for experience in experiences)

    for index, experience in enumerate(experiences):
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
            description=clean(experience.get('description'))
        )

        # Remove empty data
        experience_dict = purge_dict(experience_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('experiences')[index],
                          new_data=experience_dict,
                          attribute='email')

        # Prevent adding empty records
        if not experience_dict:
            continue

        # TODO: accumulate total months experience for candidate

        validated_experiences_data.append(experience_dict)

    return validated_experiences_data


def _add_or_update_military_services(military_services, is_updating=False, user_id=None,
                                     candidate_id=None, existing_data=None):
    # Remove duplicates
    military_services = remove_duplicates(military_services)

    # Aggregate formatted & validated military services' data
    validated_military_services_data = []

    for index, service in enumerate(military_services):
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
            end_month=service.get('end_month')
        )

        # Remove empty data
        service_dict = purge_dict(service_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('military_services')[index],
                          new_data=service_dict,
                          attribute='military_service')

        # Prevent adding empty records
        if not service_dict:
            continue

        validated_military_services_data.append(service_dict)

    return validated_military_services_data


def _add_or_update_notes(notes, user_id, is_updating=False, candidate_id=None, existing_data=None):
    # Remove duplicates
    notes = remove_duplicates(notes)

    # Aggregate formatted & validated notes' data
    validated_notes_data = []

    for index, note in enumerate(notes):
        note_dict = dict(
            owner_user_id=user_id,
            title=note.get('title'),
            comment=note.get('comment')
        )

        # Remove empty data
        note_dict = purge_dict(note_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('notes')[index],
                          new_data=note_dict,
                          attribute='note')

        # Prevent adding empty records
        if not note_dict:
            continue

        validated_notes_data.append(note_dict)

    return validated_notes_data


def _add_or_update_phones(phones, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicates
    phones = remove_duplicates(phones)

    # Aggregate formatted & validated phones' data
    validated_phones_data = []

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
            # TODO: for now, we will just need to log this but do not raise client error
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
            is_default=is_default
        )

        # Remove empty data
        phone_dict = purge_dict(phone_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('phones')[index],
                          new_data=phone_dict,
                          attribute='phone')

        # Prevent adding empty records
        if not phone_dict:
            continue

        # Save data
        validated_phones_data.append(phone_dict)

    return validated_phones_data


def _add_or_update_photos(photos, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicates
    photos = remove_duplicates(photos)

    # Aggregate formatted & validated photos' data
    validated_photos_data = []

    # Check if of candidate's photos has is_default set to true
    photo_has_default = any([isinstance(photo.get('is_default'), bool) for photo in photos])

    for index, photo in enumerate(photos):
        # If there is no default value, the first photo will be set as the default photo
        is_default = index == 0 if not photo_has_default else photo.get('is_default')

        photo_dict = dict(
            image_url=photo.get('image_url'),
            is_default=is_default
        )

        # Remove empty data
        photo_dict = purge_dict(photo_dict)

        # If photo is being added, image_url is required
        if not is_updating and not photo_dict.get('image_url'):
            raise InvalidUsage('Image url is required when adding candidate')

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('photos')[index],
                          new_data=photo_dict,
                          attribute='photo')

        validated_photos_data.append(photo_dict)

    return validated_photos_data


def _add_or_update_preferred_locations(preferred_locations, is_updating=False, user_id=None,
                                       candidate_id=None, existing_data=None):
    # Remove duplicates
    preferred_locations = remove_duplicates(preferred_locations)

    # Aggregate formatted & validated preferred locations' data
    validated_preferred_locations_data = []

    for index, preferred_location in enumerate(preferred_locations):
        preferred_location_dict = dict(
            iso3166_country=clean(preferred_location.get('iso3166_country')).upper(),
            iso3166_subdivision=clean(preferred_location.get('iso3166_subdivision')).upper(),
            city=clean(preferred_location.get('city')),
            zip_code=sanitize_zip_code(preferred_location.get('zip_code'))
        )

        # Remove empty data
        preferred_location_dict = purge_dict(preferred_location_dict, strip=False)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('preferred_location')[index],
                          new_data=preferred_location_dict,
                          attribute='preferred_location')

        # Prevent adding empty records
        if not preferred_location_dict:
            continue

        validated_preferred_locations_data.append(preferred_location_dict)

    return validated_preferred_locations_data


def _add_or_update_references(references, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicate data
    references = remove_duplicates(references)

    # Aggregate formatted & validated references' data
    validated_references_data = []

    for index, reference in enumerate(references):
        reference_dict = dict(
            reference_name=reference.get('reference_name'),
            reference_email=reference.get('reference_email'),
            reference_phone=reference.get('reference_phone'),
            reference_web_address=reference.get('reference_web_address'),
            position_title=reference.get('position_title'),
            comments=reference.get('comments')
        )

        # Remove empty data
        reference_dict = purge_dict(reference_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('references')[index],
                          new_data=reference_dict,
                          attribute='reference')

        # Prevent adding empty records
        if not reference_dict:
            continue

        validated_references_data.append(reference_dict)

    return validated_references_data


def _add_or_update_skills(skills, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicate data
    skills = remove_duplicates(skills)

    # Aggregate formatted & validated skills' data
    validated_skills_data = []

    for index, skill in enumerate(skills):
        skill_dict = dict(
            name=skill.get('name'),
            months_used=skill.get('months_used'),
            last_used_year=skill.get('last_used_year'),
            last_used_month=skill.get('last_used_month')
        )

        # Remove empty data
        skill_dict = purge_dict(skill_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('skills')[index],
                          new_data=skill_dict,
                          attribute='skill')

        # Prevent adding empty records
        if not skill_dict:
            continue

        validated_skills_data.append(skill_dict)

    return validated_skills_data


def _add_or_update_social_networks(social_networks, is_updating=False, user_id=None,
                                   candidate_id=None, existing_data=None):
    # Remove duplicate data
    social_networks = remove_duplicates(social_networks)

    # Aggregate formatted & validated social networks' data
    checked_social_networks_data = []

    for index, social_network in enumerate(social_networks):
        social_network_dict = dict(
            name=social_network['name'].strip(),
            profile_url=social_network['profile_url'].strip(),
        )

        checked_social_networks_data.append(social_network_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('social_networks')[index],
                          new_data=social_network_dict,
                          attribute='social_network')

    return checked_social_networks_data


def _add_or_update_tags(tags, is_updating=False, user_id=None, candidate_id=None, existing_data=None):
    # Remove duplicate data
    tags = remove_duplicates(tags)

    # Aggregate formatted & validated tags' data
    validated_tags_data = []

    for index, tag in enumerate(tags):
        tag_dict = dict(name=tag['name'].strip())

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('tags')[index],
                          new_data=tag_dict,
                          attribute='tag')

    return validated_tags_data


def _add_or_update_work_preferences(work_preferences, is_updating=False, user_id=None,
                                    candidate_id=None, existing_data=None):
    # Remove duplicates
    work_preferences = remove_duplicates(work_preferences)

    # Aggregated formatted & validated work preferences' data
    validated_work_preferences = []

    for index, preference in enumerate(work_preferences):
        preference_dict = dict(
            relocate=preference.get('relocate'),
            authorization=preference.get('authorization'),
            telecommute=preference.get('telecommute'),
            travel_percentage=preference.get('travel_percentage'),
            hourly_rate=preference.get('hourly_rate'),
            salary=preference.get('salary'),
            tax_terms=preference.get('tax_terms')
        )
        # Remove empty data
        preference_dict = purge_dict(preference_dict)

        validated_work_preferences.append(preference_dict)

        # track updates
        if is_updating:
            track_updates(user_id=user_id,
                          candidate_id=candidate_id,
                          existing_data=existing_data.get('work_preference')[index],
                          new_data=preference_dict,
                          attribute='work_preference')

    return work_preferences
