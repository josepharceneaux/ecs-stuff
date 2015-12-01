
from candidate_service.common.models.user import User
from candidate_service.candidate_app import db, logger
from candidate_service.common.models.candidate import (
    Candidate, CandidateEmail, CandidatePhone, CandidateSource,
    CandidateWorkPreference, CandidatePreferredLocation, CandidateAddress,
    CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField, CandidateSubscriptionPreference,
    CandidateSocialNetwork, SocialNetwork, CandidateTextComment, CandidateEducationDegreeBullet, ClassificationType,
    CandidateExperienceBullet)
from candidate_service.app.views.geo_coordinates import *
from candidate_service.common.models.misc import Country
from datetime import datetime
from sqlalchemy import and_, or_


def users_in_domain(domain_id):
        """ Returns all the users for provided domain id, Uses cache
        params: domain_id: Domain id
        returns: database users in given domain
        :param domain_id
        """
        user_domain = db.session.query(User).filter_by(User.domain_id == domain_id)
        return user_domain


def get_name_fields_from_name(formatted_name):
    """
    Get the name fields from formatted name
    :param formatted_name:
    :return:
    """
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


def get_fullname_from_name_fields(first_name, middle_name, last_name):
    """
    Get the full name from first_name, middle_name, last_name
    :param first_name:
    :param middle_name:
    :param last_name:
    :return:
    """
    full_name = ''
    if first_name:
        full_name = '%s ' % first_name
    if middle_name:
        full_name = '%s%s ' % (full_name, middle_name)
    if last_name:
        full_name = '%s%s' % (full_name, last_name)

    return full_name


def create_candidate_from_params(owner_user, candidate_id=None, first_name=None, middle_name=None, last_name=None,
                                 formatted_name=None, status_id=1, added_time=None, objective=None, summary=None,
                                 domain_can_read=1, domain_can_write=1, email=None, dice_social_profile_id=None,
                                 dice_profile_id=None, phone=None, current_company=None, current_title=None,
                                 candidate_experience_dicts=None, candidate_text_comment=None, source_id=None,
                                 city=None, state=None, zip_code=None, latitude=None, longitude=None, country_id=1,
                                 university=None, major=None, degree=None, university_start_year=None,
                                 university_start_month=None, graduation_year=None, graduation_month=None,
                                 military_branch=None, military_status=None, military_grade=None, military_to_date=None,
                                 area_of_interest_ids=None, custom_fields_dict=None,
                                 subscription_preference_frequency_id=None, social_networks=None,
                                 candidate_skill_dicts=None, do_index_deltas=True, do_db_commit=True,
                                 work_preference=None, preferred_locations=None, resume_id=None):
    """
    A new candidate will be created.

    :type owner_user_id: int
    :type candidate_id: None | int
    :type first_name: None | basestring
    :type middle_name: None | basestring
    :type last_name: None | basestring
    :param formatted_name: Combination of first_name and last_name
    :type status_id: | int
    :type added_time: None | datetime.datetime
    :type objective: None | basestring
    :type summary: None | basestring
    :type domain_can_read: int
    :type domain_can_write: int
    :type phone: None | basestring | list[basestring] | list[{str: str}]
    :type current_company: None | basestring
    :type current_title: None | basestring
    :type email: None | basestring | list[basestring]
    :type dice_social_profile_id: None | basestring
    :type dice_profile_id: None | basestring
    :type area_of_interest_ids: list[int] | None
    :type source_id: int
    :type do_db_commit: bool
    :type do_index_deltas: bool
    :type country_id: int
    :type zip_code: int
    :type resume_id: int
    :type subscription_preference_frequency_id: int
    :type latitude: None | basestring
    :type longitude: None | basestring

    :type city: None | basestring
    :type state: None | basestring
    :type university: None | basestring
    :type major: None | basestring
    :type degree: None | basestring
    :type graduation_year: None | datetime.datetime
    :type graduation_month: None | datetime.datetime
    :type university_start_month: None | datetime.datetime
    :type university_start_year: None | datetime.datetime
    :type military_to_date: None | datetime.datetime
    :type military_branch: None | basestring
    :type military_grade: None | basestring
    :type military_status: None | basestring
    :type preferred_locations: None | list[basestring] | list[{str: str}]
    :type work_preference: None | dict

    :param custom_fields_dict: custom_field_id -> value
    :type custom_fields_dict: dict[int, str] | None

    :param candidate_experience_dicts: dicts of organization, position, startMonth, startYear, endMonth, endYear, isCurrent
    :type candidate_experience_dicts: None | list[dict[basestring, int | basestring | list]]
    :type candidate_text_comment: None | basestring | list[basestring] | list[{str: str}]

    :param social_networks: socialNetworkId -> socialProfileUrl

    :param candidate_skill_dicts: List of dicts of description, addedTime, totalMonths, and lastUsed. All except description are optional.
    :type candidate_skill_dicts: None | list[dict[basestring, basestring | integer | datetime.date]]

    :rtype: dict[basestring, int]
    :return: dict of candidate info

    """
    owner_user_id = owner_user.id
    domain_id = owner_user.domain_id

    # Format inputs
    email = [email] if isinstance(email, basestring) else email
    phone = [phone] if isinstance(phone, basestring) else phone
    added_time = added_time or datetime.datetime.now()

    # Figure first name, last name etc. from inputs. this is needed thx to stupid formattedName field
    if first_name or last_name or middle_name or formatted_name:
        if (first_name or last_name) and not formatted_name:
            # If first_name and last_name given but not formatted_name, guess it
            formatted_name = get_fullname_from_name_fields(first_name, middle_name, last_name)
        elif formatted_name and (not first_name or not last_name):
            # Otherwise, guess formatted_name from the other fields
            first_name, middle_name, last_name = get_name_fields_from_name(formatted_name)

    # Set current_company and current_title based on candidate_experience_dicts, and vice versa.
    if (current_company or current_title) and not candidate_experience_dicts:
        candidate_experience_dicts = [dict(organization=current_company, position=current_title)]

    # If source_id has not been specified, set it to the domain's 'Unassigned' candidate_source
    if not source_id:
        unassigned_candidate_source = get_or_create_unassigned_candidate_source(domain_id)
        source_id = unassigned_candidate_source.id

    # Add Candidate to db
    candidate = Candidate(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        formatted_name=formatted_name,
        added_time=added_time,
        candidate_status_id=status_id,
        user_id=owner_user_id,
        domain_can_read=domain_can_read,
        domain_can_write=domain_can_write,
        dice_profile_id=dice_profile_id,
        dice_social_profile_id=dice_social_profile_id,
        source_id=source_id,
        objective=objective,
        summary=summary
    )
    db.session.add(candidate)
    db.session.commit()
    candidate_id = candidate.id
    logger.info("create_candidate_from_params: candidate_id=%s", candidate_id)

    # Make candidate's email
    if email:
        for i, address in enumerate(email):
            if address:
                is_default = i == 0
                db.session.add(CandidateEmail(address=address, candidate_id=candidate_id,
                                              is_default=is_default, email_label_id=1))
    # Add candidate phone
    if phone:
        for i, number in enumerate(phone):
            # Converting number into canonical form
            number = canonicalize_phonenumber(number)

            if number:
                is_default = i == 0
                db.session.add(CandidatePhone(value=number, candidate_id=candidate_id,
                                              is_default=is_default, phone_label_id=1))

    # Add Candidate's work experience(s)
    if candidate_experience_dicts:
        for work_experience in candidate_experience_dicts:
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
            db.session.commit()

            experience_id = experience.id
            experience_bullets = work_experience.get('work_experience_bullets')
            if isinstance(experience_bullets, list):
                for experience_bullet in experience_bullets:
                    list_order = experience_bullet.get('list_order', 1)
                    description = experience_bullet.get('description')
                    db.session.add(CandidateExperienceBullet(
                        candidate_experience_id=experience_id,
                        list_order=list_order,
                        description=description,
                        added_time=added_time
                    ))

    # Add Text comments
    if candidate_text_comment:
        if isinstance(candidate_text_comment, basestring):
            db.session.add(CandidateTextComment(candidate_id=candidate_id, list_order=1, comment=candidate_text_comment))
        else:
            # just insert them for now, no need to update
            for comment in candidate_text_comment:
                db.session.add(CandidateTextComment(candidate_id=candidate_id, list_order=0, comment=comment))

    # Add Address
    if city or state or zip_code:
        lat_lon = get_coordinates(zip_code, city, state) if (not latitude or not longitude) else "%s,%s" % (latitude, longitude)
        # Validate US zip codes
        zip_code = sanitize_zip_code(zip_code)
        db.session.add(CandidateAddress(resume_id=candidate_id,  # TODO: this is to be removed once all tables have been added & migrated
                                        candidate_id=candidate_id,
                                        city=city,
                                        state=state,
                                        zip_code=zip_code,
                                        country_id=country_id,
                                        coordinates=lat_lon,
                                        is_default=1))
    # If only lat & lon provided, do reverse geolocation
    elif latitude and longitude:
        lat_lon_str = "%s,%s" % (latitude, longitude)
        db.session.add(CandidateAddress(coordinates=lat_lon_str, candidate_id=candidate_id))

    # Add Education fields
    current_year = datetime.utcnow().year
    if university_start_year and ((university_start_year < current_year - 100) or (university_start_year > current_year + 50)):
        # Filter out invalid university start year
        university_start_year = None
    if graduation_year and ((graduation_year < current_year - 100) or (graduation_year > current_year + 50)):
        # Filter out invalid university end year
        graduation_year = None
    if university_start_month and (university_start_month < 1 or university_start_month > 12):
        university_start_month = 1
    if graduation_month and (graduation_month < 1 or graduation_month > 12):
        graduation_month = 1

    # Add University
    if university:
        candidate_education = CandidateEducation(candidate_id=candidate_id,
                                                 list_order=1,
                                                 school_name=university,
                                                 country_id=country_id,
                                                 resume_id=candidate_id,
                                                 added_time=added_time)
        db.session.add(candidate_education)
        db.session.flush()
        candidate_education_id = candidate_education.id

        # Insert new degree
        classification_type = classification_type_id_from_degree_type(degree)
        classification_type_id = classification_type['id']
        classification_type_description = classification_type['desc']

        # Add candidate education degree
        candidate_education_degree = CandidateEducationDegree(
                candidate_education_id=candidate_education_id,
                degree_type=degree,
                degree_title=classification_type_description,
                list_order=1,
                end_time=datetime(year=graduation_year, month=graduation_month, day=1) if graduation_year and
                graduation_month else None,
                start_time=datetime(year=university_start_year, month=university_start_month, day=1) if
                university_start_year and university_start_month else None,
                classification_type_id=classification_type_id, added_time=added_time)
        db.session.add(candidate_education_degree)
        db.session.flush()
        candidate_education_degree_id = candidate_education_degree.id

        # Insert new degree bullet
        db.session.add(CandidateEducationDegreeBullet(candidate_education_degree_id=candidate_education_degree_id,
                                                      list_order=1, concentration_type=major))
        db.session.flush()
    # If no university name provided, but graduation date provided
    elif graduation_month or graduation_year:
            # Create new candidate_education and candidate_education_degree
            candidate_education = CandidateEducation(candidate_id=candidate_id, list_order=1, country_id=country_id)
            db.session.add(candidate_education)
            db.session.flush()
            candidate_education_id = candidate_education.id

            # Insert new degree
            classification_type = classification_type_id_from_degree_type(degree)
            classification_type_id = classification_type['id']
            classification_type_description = classification_type['desc']

            candidate_education_degree = CandidateEducationDegree(
                candidate_education_id=candidate_education_id,
                degree_type=degree,
                degree_title=classification_type_description,
                list_order=1,
                end_time=datetime(year=graduation_year, month=graduation_month, day=1) if graduation_year and
                                                                                          graduation_month else None,
                start_time=datetime(year=university_start_year, month=university_start_month, day=1) if
                university_start_year and university_start_month else None,
                classification_type_id=classification_type_id)
            db.session.add(candidate_education_degree)
            db.session.flush()
            candidate_education_degree_id = candidate_education_degree.id
            # Insert new degree bullet
            db.session.add(CandidateEducationDegreeBullet(candidate_education_degree_id=candidate_education_degree_id,
                                                          list_order=1, concentration_type=major, added_time=added_time))
            db.session.flush()

    # Add Military service
    if military_branch or military_grade or military_status or military_to_date:
        # creating new military record
        db.session.add(CandidateMilitaryService(candidate_id=candidate_id, country_id=country_id,
                                                service_status=military_status, highest_grade=military_grade,
                                                branch=military_branch, to_date=military_to_date, resume_id=candidate_id))
        db.session.flush()
    # Custom fields
    if custom_fields_dict:
        for custom_field_id in custom_fields_dict:
            db.session.add(CandidateCustomField(candidate_id=candidate_id, custom_field_id=custom_field_id,
                                                value=custom_fields_dict[custom_field_id], added_time=added_time))
            db.session.commit()

    # Areas of interest
    if area_of_interest_ids:
        from candidate_service.app.views.talent_areas_of_interest import add_aoi_to_candidate
        add_aoi_to_candidate(candidate_id, area_of_interest_ids)

    # Normal/Job Alert subscription preference
    if subscription_preference_frequency_id:
        db.session.add(CandidateSubscriptionPreference(candidate_id=candidate_id,
                                                       frequency_id=subscription_preference_frequency_id))

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

    # Add Candidate's skill(s)
    if candidate_skill_dicts:
        for skill in candidate_skill_dicts:
            db.session.add(CandidateSkill(
                candidate_id=candidate_id,
                list_order=skill.get('list_order', 1),
                description=skill.get('description'),
                added_time=added_time,
                total_months=skill.get('total_months'),
                last_used=skill.get('last_used'),
                resume_id=candidate_id  # todo: this is to be removed once all tables have been added & migrated
            ))
            db.session.commit()
    # work preferences
    if work_preference:
        db.session.add(CandidateWorkPreference(candidateId=candidate_id, relocate=work_preference.get(
            'relocate') or work_preference.get("willing_to_relocate"), authorization=work_preference['authorization'],
                                               telecommute=work_preference['telecommute'],
                                               travel_percentage=work_preference.get(
                                                   'travel') or work_preference.get('travel_percentage'),
                                               hourly_rate=work_preference['hourly_rate'],
                                               salary=work_preference['salary'], tax_terms=work_preference.get(
                'tax_terms') or work_preference.get('employment_type'),
                                               security_clearance=work_preference['security_clearance'],
                                               third_party=work_preference['third_party']))

        # Add preferred locations
        if preferred_locations:
            # Remove any candidate locations from before
            db.session.query(CandidatePreferredLocation).filter_by(candidate_id == candidate_id).delete()
            for loc in preferred_locations:
                db.session.add(CandidatePreferredLocation(
                    candidate_id=candidate_id,
                    address="%s %s" % (loc.get('addrOne') or loc.get('address_line_1'),
                                       loc.get('addrTwo') or loc.get('address_line_2')),
                    country_id=country_code_or_name_to_id(loc.get('country')),
                    city=fix_caps(loc.get('municipality') or loc.get('city')),
                    region=fix_caps(loc.get('region')),
                    zipcode=loc.get('zip_code')))

    # Todo: Implement, when the scheduler functionality is ready
    # # If the user is a Dice user, use the SocialCV API to get more data about the candidate
    # if import_from_socialcv and email:
    #     owner_user = db.session.query(User).get(owner_user_id)
    #     if owner_user.dice_user_id:
    #         queue_task("merge_candidate_data_from_socialcv",
    #                    function_vars=dict(candidate_email=email, owner_user_id=owner_user_id))

    # Commit all the database changes
    if do_db_commit:
        db.session.commit()

    # Upload all candidate documents to cloud_search
    if do_index_deltas:
        from talent_cloud_search import upload_candidate_documents
        upload_candidate_documents(candidate_id)

    return dict(candidate_id=candidate_id)


# Canonicalize a US phone number
def canonicalize_phonenumber(phonenumber):
    import phonenumbers
    try:
        parsed_phonenumbers = phonenumbers.parse(str(phonenumber), region="US")
        if phonenumbers.is_valid_number_for_region(parsed_phonenumbers, 'US'):
            # Phone number format is : +1 (123) 456-7899
            return '+1 ' + phonenumbers.format_number(parsed_phonenumbers, phonenumbers.PhoneNumberFormat.NATIONAL)
        else:
            logger.error("canonicalize_phonenumber: [%s] is an invalid or non-US Phone Number", phonenumber)
            return False
    except phonenumbers.NumberParseException:
        logger.info("canonicalize_phonenumber: [%s] is an invalid or non-US Phone Number", phonenumber)
        return False


def get_or_create_unassigned_candidate_source(domain_id):
    unassigned_candidate_source = db.session.query(CandidateSource).filter(
        CandidateSource.description == 'Unassigned', CandidateSource.domain_id == domain_id).first()
    if unassigned_candidate_source:
        return unassigned_candidate_source
    else:
        db.session.add(CandidateSource(description='Unassigned', domain_id=domain_id))
        unassigned_candidate_source = db.session.query(CandidateSource).filter(
            CandidateSource.description == 'Unassigned', CandidateSource.domain_id == domain_id).first()
        return unassigned_candidate_source


def sanitize_zip_code(zip_code):
    # Following expression will validate US zip codes e.g 12345 and 12345-6789
    zip_code = str(zip_code)
    zip_code = ''.join(filter(lambda character: character not in ' -', zip_code))  # Dashed and Space filtered Zip Code
    if zip_code and not ''.join(filter(lambda character: not character.isdigit(), zip_code)):
        zip_code = zip_code.zfill(5) if len(zip_code) <= 5 else zip_code.zfill(9) if len(zip_code) <= 9 else ''
        if zip_code:
            return (zip_code[:5] + ' ' + zip_code[5:]).strip()
    logger.info("[%s] is not a valid US Zip Code", zip_code)
    return None


def classification_type_id_from_degree_type(degree_type):
    """
    Function will return classification_type ID of the classification_type that matches
    with degree_type. E.g. degree_type = 'Masters' => classification_type_id: 5
    :param degree_type
    :return:    classification_type_id or None
    """
    matching_classification_type_id = None
    matching_classification_type_description = None
    if degree_type:
        all_classification_types = db.session.query(ClassificationType).all()
        matching_classification_type_id = next((row.id for row in all_classification_types
                                                if row.code.lower() == degree_type.lower()), None)
        matching_classification_type_description = next((row.description for row in all_classification_types
                                                         if row.code.lower() == degree_type.lower()), None)
    return dict(id=matching_classification_type_id, desc=matching_classification_type_description)


def add_candidate_custom_fields(candidate_id, candidate_custom_fields_dict, current_candidate_custom_fields=None,
                                replace=False):
    """
    :param candidate_id:
    :type candidate_custom_fields_dict: dict[int, str | list]
    :param current_candidate_custom_fields:
    :param replace: If replace=True, will delete all candidate_custom_fields in current_candidate_custom_fields but not in
    candidate_custom_fields_dict
    """
    for custom_field_id, value_array_or_string in candidate_custom_fields_dict.iteritems():
        # Value could be array or string
        value_array = [value_array_or_string] if isinstance(value_array_or_string, basestring) else \
            value_array_or_string

        for value in value_array:
            # Add custom field name/value pair only if the candidate is new,
            # or if the key/value doesn't already exist in the DB
            filtered_custom_fields = current_candidate_custom_fields.filter(and_(
                CandidateCustomField.custom_field_id == custom_field_id,
                CandidateCustomField.value == value)).first()
            if not filtered_custom_fields:
                db.session.add(CandidateCustomField(candidate_id=candidate_id,custom_field_id=custom_field_id,
                                                    value=value))
    # Delete old custom fields if necessary
    if replace:
        candidate_custom_field_ids_to_delete = []
        for current_candidate_custom_field in current_candidate_custom_fields:
            value_array_or_string = candidate_custom_fields_dict.get(current_candidate_custom_field.customFieldId)

            # If new custom field dict doesn't even have the customFieldId as the old one,
            # remove the old candidate_custom_field
            if not value_array_or_string:
                candidate_custom_field_ids_to_delete.append(current_candidate_custom_field.id)
            else:
                # If new custom field dict has the same customFieldId but not the same values,
                # remove the old candidate_custom_field

                # value_array is array of new custom field values,
                # so we want to delete the current_candidate_custom_field if it's not in value_array
                value_array = [value_array_or_string] if isinstance(value_array_or_string,
                                                                    basestring) else value_array_or_string
                value_array = filter(None, value_array)

                if current_candidate_custom_field.value not in value_array:
                    candidate_custom_field_ids_to_delete.append(current_candidate_custom_field.id)
        for cf_id in candidate_custom_field_ids_to_delete:
            cf_row = db.session.query(CandidateCustomField).filter_by(id=cf_id)
            cf_row.delete()


def get_subscription_preference(candidate_id):
    """
    If there are multiple subscription preferences (due to legacy reasons),
    if any one is 1-6, keep it and delete the rest.
    Otherwise, if any one is NULL, keep it and delete the rest.
    Otherwise, if any one is 7, delete all of them.
    :param candidate_id:
    """
    email_prefs = db.session.query(CandidateSubscriptionPreference).filter_by(candidate_id == candidate_id)
    non_custom_pref = email_prefs.filter(and_(CandidateSubscriptionPreference.frequency_id,
                                              CandidateSubscriptionPreference.frequency_id < 7)).first()
    null_pref = email_prefs.filter(CandidateSubscriptionPreference.frequency_id).first()
    custom_pref = email_prefs.filter(and_(CandidateSubscriptionPreference.frequency_id,
                                          CandidateSubscriptionPreference.frequency_id == 7)).first()
    if non_custom_pref:
        all_other_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != non_custom_pref.id)
        all_other_prefs_ids = [cs_id for cs_id in all_other_prefs]
        logger.info("get_subscription_preference: Deleting non-custom prefs for candidate %s: %s",
                    candidate_id, all_other_prefs_ids)
        for cs_id in all_other_prefs_ids:
            cs_row = db.session.query(CandidateSubscriptionPreference).filter_by(id=cs_id)
            cs_row.delete()
        return non_custom_pref
    elif null_pref:
        non_null_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != null_pref.id)
        non_null_prefs_id = [cs_id for cs_id in non_null_prefs]
        logger.info("get_subscription_preference: Deleting non-null prefs for candidate %s: %s", candidate_id, non_null_prefs_id)
        for cs_id in non_null_prefs_id:
            cs_row = db.session.query(CandidateSubscriptionPreference).filter_by(id=cs_id)
            cs_row.delete()
        return null_pref
    elif custom_pref:
        email_prefs_ids = [cs_id for cs_id in email_prefs]
        logger.info("get_subscription_preference: Deleting all prefs for candidate %s: %s", candidate_id, email_prefs_ids)
        for cs_id in email_prefs_ids:
            cs_row = db.session.query(CandidateSubscriptionPreference).filter_by(id=cs_id)
            cs_row.delete()
        return None


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def country_code_or_name_to_id(code_or_name):
    """

    :param code_or_name: country code or name (or ID)
    :type code_or_name: None | str | int
    :return: The country_id
    :rtype: int | None
    """
    if not code_or_name:
        return None
    if is_number(code_or_name):
        return int(code_or_name)
    all_countries = db.session.query(Country).filter_by(Country.id > 0)
    matching_country = all_countries.filter(or_(Country.code.lower()) == code_or_name.lower(),
                                            Country.name.lower() == code_or_name.lower(), limitby=(0, 1)).first()
    if matching_country:
        return matching_country.id
    return None


def fix_caps(string):
    """

    :type string: None | str
    :return: None | str
    """

    if string and string.islower() and len(string) > 2:
        # Only process lowercase strings that have more than 2 characters.
        # Or it may be an abbreviation or the middle part of a name.
        if string.find(' ') == -1:
            # If string has no spaces, just capitalize first word
            return string.capitalize()
        else:
            # If string has spaces, capitalize every segment that has > 2 characters.
            # For example, 'oscar de la joya' -> 'Oscar de la Joya'.
            return ''.join([string_segment.capitalize() for string_segment in
                            string.split(' ') if len(string_segment) > 2])
    return string


def country_id_from_country_name_or_code(country_name_or_code):
    """
    Function will find and return ID of the country matching with country_name_or_code
    If not match is found, default return is 1 => 'United States'

    :return: Country.id
    """

    all_countries = db.session.query(Country).all()
    if country_name_or_code:
        matching_country_id = next((row.id for row in all_countries
                                    if row.code.lower() == country_name_or_code.lower()
                                    or row.name.lower() == country_name_or_code.lower()), None)
        return matching_country_id
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
