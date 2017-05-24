"""
File contains logic for:
 - cleaning and validating candidate's data received from the client
 - tracking all changes to candidate's data
"""
import re
import phonenumbers
from datetime import datetime

from db_transaction import commit_transaction
from graphql_service.application import logger
from graphql_service.candidate_application.modules.helpers import clean
from track_edits import track_edits
from graphql_service.common.utils.handy_functions import purge_dict
from graphql_service.common.utils.datetime_utils import DatetimeUtils
from graphql_service.common.utils.validators import is_valid_email, sanitize_zip_code, parse_phone_number, is_number
from graphql_service.common.geo_services.geo_coordinates import get_coordinates
from graphql_service.common.utils.candidate_utils import remove_duplicates

from graphql_service.common.error_handling import InternalServerError, InvalidUsage, NotFoundError, ForbiddenError

from graphql_service.common.models.candidate import (
    Candidate, CandidateAddress, CandidateEducation, CandidateSubscriptionPreference,
    CandidateEducationDegree, CandidateWorkPreference, CandidateSkill
)
from graphql_service.common.models.misc import Product, CustomField, Frequency
from graphql_service.common.models.talent_pools_pipelines import TalentPool, TalentPoolGroup, TalentPoolCandidate
from graphql_service.common.models.candidate_edit import CandidateView

# Models
from graphql_service.common.models.db import db
from graphql_service.common.custom_errors.user import (
    FORBIDDEN_CUSTOM_FIELDS, TP_NOT_FOUND, TP_FORBIDDEN_2, TP_FORBIDDEN_1, INVALID_SP_ID
)
from graphql_service.common.custom_errors.candidate import (
    ADDRESS_NOT_FOUND, ADDRESS_FORBIDDEN, EDUCATION_NOT_FOUND, EDUCATION_FORBIDDEN,
    PREFERENCE_FORBIDDEN, PREFERENCE_NOT_FOUND, SKILL_FORBIDDEN, SKILL_NOT_FOUND, INVALID_EMAIL
)

from graphql_service.common.utils.iso_standards import country_code_if_valid


def add_or_edit_candidate_from_params(
        user,
        primary_data,
        talent_pool_id=None,
        is_updating=False,
        candidate_id=None,
        candidates_existing_data=None,
        addresses=None,
        educations=None,
        emails=None,
        phones=None,
        candidate_custom_fields=None,
        experiences=None,
        military_services=None,
        preferred_locations=None,
        references=None,
        skills=None,
        social_networks=None,
        tags=None,
        notes=None,
        frequency_id=None,
        is_candidate_viewed=False,
        work_preferences=None,
        photos=None
):
    """
    Function will:
      1. clean & validate candidate's data
      2. track edits in case of an update
      3. return candidate's data
        :param user: authorized user
        :type  user: User
        :param primary_data: candidate's top level data that is stored in Candidate-table
        :type  primary_data: dict
        :type talent_pool_id: int
        :type is_updating:  bool
        :type candidate_id: int
        :param candidates_existing_data: candidate's current data retrieved from ddb
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
        :param frequency_id: Subscription Frequency Id of candidate
        :type frequency_id: basestring
        :param is_candidate_viewed: Is candidate Profile viewed
        :type is_candidate_viewed: bools
        :param work_preferences: candidate's work preferences
        :type  work_preferences: list
        :param photos: candidate's photos collection
        :type  photos: list
        :rtype: dict
    """
    assert isinstance(primary_data, dict), "Candidate's primary data must be of type dict"
    candidate_data = primary_data.copy()

    # Candidate's primary data such as first_name, last_name, objective, summary, etc.
    if primary_data:
        validated_primary_data = _primary_data(primary_data=candidate_data,
                                               user_id=user.id,
                                               existing_data=candidates_existing_data,
                                               is_updating=is_updating,
                                               candidate_id=candidate_id)
        candidate_data = validated_primary_data

    # Link candidate to validated Talent Pool
    if talent_pool_id:
        validated_talent_pool_id = _add_candidates_talent_pool_id(talent_pool_id=talent_pool_id,
                                                                  user=user, candidate_id=candidate_id)
        candidate_data['talent_pool_id'] = validated_talent_pool_id

    # Addresses
    if addresses:
        validated_addresses_data = _add_or_update_addresses(addresses=addresses,
                                                            user_id=user.id,
                                                            is_updating=is_updating,
                                                            existing_data=candidates_existing_data,
                                                            candidate_id=candidate_id)
        candidate_data['addresses'] = validated_addresses_data

    # Custom Fields
    if candidate_custom_fields:
        validated_custom_fields_data = _add_or_update_custom_fields(custom_fields=candidate_custom_fields,
                                                                    user=user)
        candidate_data['candidate_custom_fields'] = validated_custom_fields_data

    # Educations
    if educations:
        validated_educations_data = _add_or_update_educations(educations=educations,
                                                              is_updating=is_updating,
                                                              user_id=user.id,
                                                              candidate_id=candidate_id,
                                                              existing_data=candidates_existing_data)
        candidate_data['educations'] = validated_educations_data

    # Emails
    if emails:
        validated_emails_data = _add_or_update_emails(emails=emails,
                                                      is_updating=is_updating,
                                                      user_id=user.id,
                                                      existing_data=candidates_existing_data,
                                                      candidate_id=candidate_id)
        candidate_data['emails'] = validated_emails_data

    # Experiences
    if experiences:
        validated_experiences_data = _add_or_update_experiences(experiences=experiences,
                                                                is_updating=is_updating,
                                                                user_id=user.id,
                                                                candidate_id=candidate_id,
                                                                existing_data=candidates_existing_data)
        candidate_data['experiences'] = validated_experiences_data

    # Military Services
    if military_services:
        validated_military_services_data = _add_or_update_military_services(military_services=military_services,
                                                                            is_updating=is_updating,
                                                                            user_id=user.id,
                                                                            candidate_id=candidate_id,
                                                                            existing_data=candidates_existing_data)
        candidate_data['military_services'] = validated_military_services_data

    # Notes
    if notes:
        validated_notes_data = _add_or_update_notes(notes=notes,
                                                    user_id=user.id,
                                                    is_updating=is_updating,
                                                    candidate_id=candidate_id,
                                                    existing_data=candidates_existing_data)
        candidate_data['notes'] = validated_notes_data

    # Phones
    if phones:
        validated_phones_data = _add_or_update_phones(phones=phones,
                                                      is_updating=is_updating,
                                                      user_id=user.id,
                                                      candidate_id=candidate_id,
                                                      existing_data=candidates_existing_data)
        candidate_data['phones'] = validated_phones_data

    # Photos
    if photos:
        validated_photos_data = _add_or_update_photos(photos=photos,
                                                      is_updating=is_updating,
                                                      user_id=user.id,
                                                      candidate_id=candidate_id,
                                                      existing_data=candidates_existing_data)
        candidate_data['photos'] = validated_photos_data

    # Preferred Locations
    if preferred_locations:
        validated_preferred_locations_data = _add_or_update_preferred_locations(preferred_locations=preferred_locations,
                                                                                is_updating=is_updating,
                                                                                user_id=user.id,
                                                                                candidate_id=candidate_id,
                                                                                existing_data=candidates_existing_data)
        candidate_data['preferred_locations'] = validated_preferred_locations_data

    # References
    if references:
        validated_references_data = _add_or_update_references(references=references,
                                                              is_updating=is_updating,
                                                              user_id=user.id,
                                                              candidate_id=candidate_id,
                                                              existing_data=candidates_existing_data)
        candidate_data['references'] = validated_references_data

    # Skills
    if skills:
        validated_skills_data = _add_or_update_skills(skills=skills,
                                                      is_updating=is_updating,
                                                      user_id=user.id,
                                                      candidate_id=candidate_id,
                                                      existing_data=candidates_existing_data)
        candidate_data['skills'] = validated_skills_data

    # Social Networks
    if social_networks:
        validated_social_networks_data = _add_or_update_social_networks(social_networks=social_networks,
                                                                        is_updating=is_updating,
                                                                        user_id=user.id,
                                                                        candidate_id=candidate_id,
                                                                        existing_data=candidates_existing_data)
        candidate_data['social_networks'] = validated_social_networks_data

    if frequency_id is not None:
        candidate_data['frequency_id'] = _add_or_update_candidate_subscription_preference(candidate_id, frequency_id)

    # Tags
    if tags:
        validated_tags_data = _add_or_update_tags(tags=tags,
                                                  is_updating=is_updating,
                                                  user_id=user.id,
                                                  candidate_id=candidate_id,
                                                  existing_data=candidates_existing_data)
        candidate_data['tags'] = validated_tags_data

    if is_candidate_viewed:
        candidate_viewed = CandidateView(user_id=user.id, candidate_id=candidate_id,
                                         view_type=3, view_datetime=datetime.utcnow())
        db.session.cadd(candidate_viewed)

    # Work Preference
    if work_preferences:
        validated_work_preference_data = _add_or_update_work_preferences(work_preferences=work_preferences,
                                                                         is_updating=is_updating,
                                                                         user_id=user.id,
                                                                         candidate_id=candidate_id,
                                                                         existing_data=candidates_existing_data)
        candidate_data['work_preferences'] = validated_work_preference_data

    return candidate_data


def _add_or_update_candidate_subscription_preference(candidate_id, frequency_id):
    """
    This method will add or update candidate subscription preference based on given arguments
    :param candidate_id: Id of Candidate
    :param frequency_id: Frequency Id
    :return:
    """
    frequency_id = frequency_id if is_number(frequency_id) else None
    if not frequency_id or (int(frequency_id) != -1 and not Frequency.query.get(frequency_id)):
        raise NotFoundError('Frequency ID not recognized: {}'.format(frequency_id))

    can_subs_pref = CandidateSubscriptionPreference.get_by_candidate_id(candidate_id)
    if not can_subs_pref:
        can_subs_pref = CandidateSubscriptionPreference(candidate_id=candidate_id, frequency_id=frequency_id)
        db.session.cadd(can_subs_pref)
    else:
        can_subs_pref.frequency_id = frequency_id

    return frequency_id


def _primary_data(primary_data, user_id, existing_data, is_updating, candidate_id):
    """
    Function will return candidate's validated primary data
    :rtype: dict
    """
    # Source Product ID must be recognized
    source_product_id = primary_data.get('source_product_id')
    if source_product_id and not Product.query.get(source_product_id):
        raise InvalidUsage(INVALID_SP_ID[0], INVALID_SP_ID[1])

    # Remove empty data
    primary_dict_data = purge(primary_data)

    if is_updating is True:
        # Update candidate's primary info in MySQL database
        db.session.cquery(Candidate).filter_by(id=candidate_id).update(primary_dict_data)
        commit_transaction()

        # Add updated_datetime if candidate is being updated
        primary_dict_data['updated_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow())

    return primary_dict_data


def _add_candidates_talent_pool_id(talent_pool_id, user, candidate_id):
    """
    Function will return talent pool ID after checking the following:
     - TP ID must be recognized
     - TP ID must belong to user's domain ID
     - TP ID must belong to user's group
    :rtype: int
    """
    talent_pool = TalentPool.query.get(talent_pool_id)
    if not talent_pool:
        raise NotFoundError(TP_NOT_FOUND[0], TP_NOT_FOUND[1])
    if talent_pool.domain_id != user.domain_id:
        raise ForbiddenError(TP_FORBIDDEN_1[0], TP_FORBIDDEN_1[1])
    if not TalentPoolGroup.query.filter_by(talent_pool_id=talent_pool_id, user_group_id=user.user_group_id):
        raise ForbiddenError(TP_FORBIDDEN_2[0], TP_FORBIDDEN_2[1])

    if not TalentPoolCandidate.query.filter_by(candidate_id=candidate_id, talent_pool_id=talent_pool_id).first():
        db.session.add(TalentPoolCandidate(candidate_id=candidate_id, talent_pool_id=talent_pool_id))

    return talent_pool_id


def _add_or_update_addresses(addresses, user_id, is_updating, existing_data, candidate_id):
    """
    - Duplicate dict(s) will be removed
    - The first address will be set as default if none of the addresses is set as the default address
    """
    # Remove duplicates
    addresses = remove_duplicates(addresses)

    # Aggregate formatted & validated address data
    validated_addresses_data = []

    # Check if any of the addresses is set as the default address
    addresses_have_default = [isinstance(address.get('is_default'), bool) for address in addresses]

    for index, address in enumerate(addresses):
        zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
        city = (address.get('city') or '').strip()
        iso3166_subdivision = (address.get('iso3166_subdivision') or '').upper()

        address_dict = dict(
            address_line_1=address.get('address_line_1'),
            address_line_2=address.get('address_line_2'),
            zip_code=zip_code,
            state=address.get('state'),
            city=city,
            iso3166_subdivision=iso3166_subdivision,
            iso3166_country=(address.get('iso3166_country') or '').upper(),
            po_box=address.get('po_box'),
            is_default=index == 0 if not addresses_have_default else address.get('is_default'),
            coordinates=get_coordinates(zipcode=zip_code, city=city, state=iso3166_subdivision)
        )

        # Remove empty data from address dict
        address_dict = purge_dict(address_dict)

        # Prevent adding empty records
        if not address_dict:
            continue

        validated_addresses_data.append(address_dict)

    return validated_addresses_data


def _add_or_update_custom_fields(custom_fields, user):
    """
    - Duplicate dict(s) will be removed
    - Custom field ID(s) must be recognized and must belong to user's domain
    """
    # Remove duplicate data
    custom_fields = remove_duplicates(custom_fields)

    # Custom field IDs must belong to candidate's domain
    custom_field_ids = [custom_field['custom_field_id'] for custom_field in custom_fields]
    if not db.session.cquery(CustomField).filter(CustomField.id.in_(custom_field_ids),
                                                 CustomField.domain_id != user.domain_id).count() == 0:
        raise ForbiddenError(FORBIDDEN_CUSTOM_FIELDS[0], FORBIDDEN_CUSTOM_FIELDS[1])

    # TODO: track updates
    return map(purge_dict, custom_fields)


def _add_or_update_educations(educations, is_updating, user_id, candidate_id, existing_data):
    """
    - Duplicate dict(s) will be removed
    -
    """
    # Remove duplicate data
    education_items = None
    for i, education in enumerate(educations):
        if education.items() == education_items:
            del educations[i]
        else:
            education_items = education.items()

    # Aggregate formatted & validated education data
    validated_education_data = []

    for index, education in enumerate(educations):
        education_dict = dict(
            school_name=education.get('school_name'),
            school_type=education.get('school_type'),
            city=education.get('city'),
            iso3166_country=(education.get('iso3166_country') or '').upper(),
            iso3166_subdivision=(education.get('iso3166_subdivision') or '').upper(),
            state=(education.get('state') or '').upper(),
            is_current=education.get('is_current')
        )

        # Remove empty data
        education_dict = purge_dict(education_dict)

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
                degree_dict = dict(
                    start_year=degree.get('start_year'),
                    start_month=degree.get('start_month'),
                    end_year=degree.get('end_year'),
                    end_month=degree.get('end_month'),
                    gpa=str(degree['gpa']) if degree.get('gpa') else None,
                    title=degree.get('title'),
                    concentration=degree.get('concentration'),
                    comments=degree.get('comments')
                )

                # Remove empty data
                degree_dict = purge_dict(degree_dict)
                print("degree_dict: {}".format(degree_dict))

                # Prevent adding empty records
                if not degree_dict:
                    continue

                checked_degree_data.append(degree_dict)

            # Aggregate degree data to the corresponding education data
            validated_education_data[index]['degrees'] = checked_degree_data

    print("validated_education_data: {}".format(validated_education_data))
    return validated_education_data


def _add_or_update_emails(emails, is_updating, user_id, existing_data, candidate_id):
    """
    Function will normalize, validate, and return email objects for adding or updating candidate's emails
    If intend is to update, all changes will be tracked
    """
    # Remove duplicates
    emails = remove_duplicates(emails)

    # Aggregate formatted & validated email data
    validated_emails_data = []

    # Check if any of the emails is set as the default email
    emails_have_default = [isinstance(email.get('is_default'), bool) for email in emails]

    for i, email in enumerate(emails):

        # Normalize email address
        # Ensure email address is properly formatted
        # If email address is empty/null, process the next email object
        email_address = (email.get('address') or '').strip().lower()
        if email_address:
            if not is_valid_email(email_address):
                raise InvalidUsage(INVALID_EMAIL[0], INVALID_EMAIL[1])
        elif not email_address:
            continue

        # Set email's label to 'Other' if it doesn't match any of the predefined email labels
        label = (email.get('label') or '').lower()
        if not label or label not in ('Primary', 'Home', 'Work', 'Other'):
            label = 'Primary'

        label = label.title()

        # First email will be set as default if no other email is set as default
        default = i == 0 if not any(emails_have_default) else email.get('is_default')

        email_dict = dict(label=label, address=email_address, is_default=default)

        validated_emails_data.append(email_dict)

    return validated_emails_data


def _add_or_update_experiences(experiences, is_updating, user_id, candidate_id, existing_data):
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

        # Prevent adding empty records
        if not experience_dict:
            continue

        # TODO: accumulate total months experience for candidate

        validated_experiences_data.append(experience_dict)

    return validated_experiences_data


def _add_or_update_military_services(military_services, is_updating, user_id, candidate_id, existing_data):
    # Remove duplicates
    military_services = remove_duplicates(military_services)

    # Aggregate formatted & validated military services' data
    validated_military_services_data = []

    for index, service in enumerate(military_services):
        service_dict = dict(
            iso3166_country=(service.get('iso3166_country') or '').upper(),
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

        # Prevent adding empty records
        if not service_dict:
            continue

        validated_military_services_data.append(service_dict)

    return validated_military_services_data


def _add_or_update_notes(notes, user_id, is_updating, candidate_id, existing_data):
    # Remove duplicates
    notes = remove_duplicates(notes)

    # Aggregate formatted & validated notes' data
    validated_notes_data = []

    for index, note in enumerate(notes):
        note_dict = dict(
            owner_id=user_id,
            title=note.get('title'),
            comments=note['comments']
        )

        # Remove empty data
        note_dict = purge_dict(note_dict)

        # Prevent adding empty records
        if not note_dict:
            continue

        validated_notes_data.append(note_dict)

    return validated_notes_data


def _add_or_update_phones(phones, is_updating, user_id, candidate_id, existing_data):
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
        phone_label = 'Mobile' if (not phones_have_label and index == 0) else clean(phone.get('label'))

        # Phone number must contain at least 7 digits
        # http://stackoverflow.com/questions/14894899/what-is-the-minimum-length-of-a-valid-international-phone-number
        value = clean(phone.get('value'))
        number = re.sub('\D', '', value)
        if len(number) < 7:
            # TODO: for now, we will just need to log this but do not raise an exception
            logger.info("Phone number ({}) must be at least 7 digits".format(value))

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

        # Prevent adding empty records
        if not phone_dict:
            continue

        # Save data
        validated_phones_data.append(phone_dict)

    return validated_phones_data


def _add_or_update_photos(photos, is_updating, user_id, candidate_id, existing_data):
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

        validated_photos_data.append(photo_dict)

    return validated_photos_data


def _add_or_update_preferred_locations(preferred_locations, is_updating, user_id, candidate_id, existing_data):
    # Remove duplicates
    preferred_locations = remove_duplicates(preferred_locations)

    # Aggregate formatted & validated preferred locations' data
    validated_preferred_locations_data = []

    for index, preferred_location in enumerate(preferred_locations):
        preferred_location_dict = dict(
            iso3166_country=clean(preferred_location.get('iso3166_country')).upper(),
            iso3166_subdivision=clean(preferred_location.get('iso3166_subdivision')).upper(),
            state=clean(preferred_location.get('state')),
            city=clean(preferred_location.get('city')),
            zip_code=sanitize_zip_code(preferred_location.get('zip_code'))
        )

        # Remove empty data
        preferred_location_dict = purge_dict(preferred_location_dict, strip=False)

        # Prevent adding empty records
        if not preferred_location_dict:
            continue

        validated_preferred_locations_data.append(preferred_location_dict)

    return validated_preferred_locations_data


def _add_or_update_references(references, is_updating, user_id, candidate_id, existing_data):
    # Remove duplicate data
    references = remove_duplicates(references)

    # Aggregate formatted & validated references' data
    validated_references_data = []

    for index, reference in enumerate(references):
        reference_dict = dict(
            reference_name=reference.get('person_name'),
            position_title=reference.get('position_title'),
            comments=reference.get('comments')
        )

        # Remove empty data
        reference_dict = purge_dict(reference_dict)

        # Prevent adding empty records
        if not reference_dict:
            continue

        validated_references_data.append(reference_dict)

    return validated_references_data


def _add_or_update_skills(skills, is_updating, user_id, candidate_id, existing_data):
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

        # Prevent adding empty records
        if not skill_dict:
            continue

        validated_skills_data.append(skill_dict)

    return validated_skills_data


def _add_or_update_social_networks(social_networks, is_updating, user_id, candidate_id, existing_data):
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

    return checked_social_networks_data


def _add_or_update_tags(tags, is_updating, user_id, candidate_id, existing_data):
    # Remove duplicate data
    tags = remove_duplicates(tags)

    # Aggregated formatted & validated tags' data
    validated_tags = []

    for index, tag in enumerate(tags):
        tag_dict = dict(name=tag['name'].strip())
        validated_tags.append(tag_dict)

    return validated_tags


def _add_or_update_work_preferences(work_preferences, is_updating, user_id, candidate_id, existing_data):
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
            hourly_rate=str(preference['hourly_rate']) if preference.get('hourly_rate') else None,
            salary=preference.get('salary'),
            tax_terms=preference.get('tax_terms'),
            third_party=preference.get('third_party'),
            security_clearance=preference.get('security_clearance'),
            employment_type=preference.get('employment_type')
        )
        # Remove empty data
        preference_dict = purge_dict(preference_dict)

        validated_work_preferences.append(preference_dict)

    return validated_work_preferences


# TODO: docstrings!
def collection_missing_data(existing_data, update_data):
    """
    :param existing_data:
    :param update_data:
    :return:
    """
    missing = []
    for key, value in existing_data.items():
        if isinstance(value, list):
            new_data = update_data.get(key)
            if new_data is not None:

                # Return key if list object is empty
                if not new_data:
                    missing.append(key)
                    continue

                for i, dictionary in enumerate(value):
                    old_keys = set(dictionary.keys())
                    new_keys = set(new_data[i].keys())

                    differences = old_keys.difference(new_keys)
                    if differences:
                        missing.append({key: [k for k in differences]})
    return missing


# TODO: remove in favor of collection_missing_data
def get_missing_data(existing_data, update_data, ignore=('added_time', 'user_id', 'updated_datetime')):
    """
    Function will report back any missing keys from update_data that is present in existing_data.
     - If missing key(s) belong to a dict inside of a list, the collection's name will also be reported
       to create a mapping. E.g. [ {"addresses": ["city", "address_line_1"]} ]
     - Only the collection's name/key will be returned if the entire collection is missing in update_data.
       E.g. ["addresses"]

    Example:
        >>> existing_data = {
        >>>    "first_name": "Quentin",
        >>>    "last_name": "Tarantino",
        >>>    "title": "filmmaker/director",
        >>>    "emails": [ {"address": "qtarantino@example.com", "label": "Primary"} ],
        >>>    "skills": [ {"name": "creative writing"} ],
        >>> }

        >>> update_data = {
        >>>    "first_name": "Quentin",
        >>>    "last_name": "Tarantino",
        >>>    "emails": [ {"label": "Work"} ]
        >>> }

        >>> r = get_missing_data(existing_data, update_data)
        >>> assert r == ["title", "skills", {"emails": ["address"]}]

    :type existing_data: dict
    :type update_data: dict
    :type ignore: tuple
    :param ignore: attributes that will be ignored in this function
    :rtype: list
    """
    missing = []
    for key in existing_data:
        if key not in ignore and key not in update_data:
            missing.append(key)

        existing_d = existing_data.get(key)
        if isinstance(existing_d, list):
            update_d = update_data.get(key)
            if update_d is not None:
                old_keys, new_keys = set(), set()
                for i, dictionary in enumerate(existing_d):
                    old_keys = set(dictionary.keys())
                    new_keys = set(update_d[i].keys())

                differences = old_keys.difference(new_keys)
                if differences:
                    missing.append({key: [k for k in differences]})

    return missing


def purge(dictionary, keep_empty_string=True):
    """
    :type dictionary: dict
    :type keep_empty_string: bool
    :rtype: dict
    """

    def _clean(v):
        return v.strip() if isinstance(v, (str, unicode)) else v

    if keep_empty_string:
        return {k: _clean(v) for k, v in dictionary.items() if v is not None}
