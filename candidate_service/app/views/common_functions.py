
from candidate_service.common.models.user import User
from candidate_service.candidate_app import db, logger
from candidate_service.common.models.candidate import (
    Candidate, EmailLabel, CandidateEmail, CandidatePhone, PhoneLabel, CandidateSource,
    CandidateWorkPreference, CandidatePreferredLocation, CandidateAddress,
    CandidateExperience, CandidateEducation, CandidateEducationDegree,
    CandidateSkill, CandidateMilitaryService, CandidateCustomField,CandidateSubscription,
    CandidateSocialNetwork, SocialNetwork, CandidateTextComment, CandidateEducationDegreeBullet
)
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.email_marketing import (EmailCampaign, EmailCampaignSend)
from candidate_service.common.models.misc import (Country, AreaOfInterest, CustomField, Clasification)
from sqlalchemy import and_, or_
from flask import current_app
from datetime import datetime


def users_in_domain(domain_id):
        """Returns all the users for provided domain id, Uses cache
        params: domain_id: Domain id
        returns: database users in given domain
        """
        user_domain = db.session.query(User).filter_by(User.domain_id == domain_id)
        return user_domain


def domain_id_from_user_id(user_id):
    """
    :type   user_id:  int
    :return domain_id
    """
    user = db.session.query(User).get(user_id)
    if not user:
        logger.error('domain_id_from_user_id: Tried to find the domain ID of the user: %s',
                     user_id)
        return None
    if not user.domain_id:
        logger.error('domain_id_from_user_id: user.domain_id was None!', user_id)
        return None

    return user.domain_id


def get_geo_coordinates(location):
    """Google location (lat/lon) service."""
    import requests
    url = 'http://maps.google.com/maps/api/geocode/json'
    r = requests.get(url, params=dict(address=location, sensor='false'))
    try:
        geo_data = r.json()
    except Exception:
        geo_data = r.json

    results = geo_data.get('results')
    if results:
        location = results[0].get('geometry', {}).get('location', {})

        lat = location.get('lat')
        lng = location.get('lng')
    else:
        lat, lng = None, None

    return lat, lng


def get_coordinates(zipcode=None, city=None, state=None, address_line_1=None, location=None):
    """

    :param location: if provided, overrides all other inputs
    :return: string of "lat,lon" in degrees, or None if nothing found
    """
    coordinates = None

    location = location or "%s%s%s%s" % (
        address_line_1 + ", " if address_line_1 else "",
        city + ", " if city else "",
        state + ", " if state else "",
        zipcode or ""
    )
    latitude, longitude = get_geo_coordinates(location)
    if latitude and longitude:
        coordinates = "%s,%s" % (latitude, longitude)

    return coordinates


def get_geo_coordinates_bounding(address, distance):
    """
    Using google maps api get coordinates, get coordinates, and bounding box with top left and bottom right coordinates
    :return: coordinates and bounding box coordinates
    """
    from geo_location import GeoLocation
    lat, lng = get_geo_coordinates(address)
    if lat and lng:
        # get bounding box based on location coordinates and distance given
        loc = GeoLocation.from_degrees(lat, lng)
        sw_loc, ne_loc = loc.bounding_locations(distance)
        # cloud search requires top left and bottom right coordinates
        north_west = ne_loc.deg_lat, sw_loc.deg_lon
        south_east = sw_loc.deg_lat, ne_loc.deg_lon
        return {'top_left':north_west, 'bottom_right': south_east, 'point':(lat, lng)}
    return False


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


def get_fullname_from_name_fields(first_name, middle_name, last_name):
    full_name = ''
    if first_name:
        full_name = '%s ' % first_name
    if middle_name:
        full_name = '%s%s ' % (full_name, middle_name)
    if last_name:
        full_name = '%s%s' % (full_name, last_name)

    return full_name


def create_candidate_from_params(
        owner_user_id,
        candidate_id=None,
        first_name=None,
        middle_name=None,
        last_name=None,
        formatted_name=None,
        status_id=None,
        added_time=None,
        objective=None,
        summary=None,
        domain_can_read=1,
        domain_can_write=1,
        source_product_id=2,
        email=None,
        dice_social_profile_id=None,
        dice_profile_id=None,
        update_if_email_exists=True,
        phone=None,
        current_company=None,
        current_title=None,
        candidate_experience_dicts=None,
        candidate_text_comment=None,
        source_id=None,
        city=None,
        state=None,
        zip_code=None,
        latitude=None,
        longitude=None,
        country_id=1,
        interest_id=None,
        interest_info=None,
        university=None,
        major=None,
        degree=None,
        university_start_year=None,
        university_start_month=None,
        graduation_year=None,
        graduation_month=None,
        military_branch=None,
        military_status=None,
        military_grade=None,
        military_to_date=None,
        area_of_interest_ids=None,
        custom_fields_dict=None,
        subscription_preference_frequency_id=None,
        job_alert_subscription_preference_frequency_id=None,
        # -1 means "Never", None means "don't change"  # TODO should really make another frequency called Never
        social_networks=None,
        candidate_skill_dicts=None,
        do_index_deltas=True,
        do_db_commit=True,
        update_if_exists=True,
        import_from_socialcv=True,
        work_preference=None,
        preferred_locations=None
):
    """
    If you want to update the candidate, pass in the candidate_id.  Or, pass in the email address and
    make sure update_if_email_exists=True. OR - pass in a dice_social_profile_id and dice_profile_id of an existing candidate
    in the domain.

    Otherwise, a new candidate will be created.

    :type owner_user_id: int
    :type candidate_id: None | int
    :type first_name: None | basestring
    :type middle_name: None | basestring
    :type last_name: None | basestring
    :type formatted_name: None | basestring
    :type added_time: None | datetime.datetime
    :type objective: None | basestring
    :type summary: None | basestring
    :type domain_can_read: int
    :type domain_can_write: int
    :type phone: None | basestring | list[basestring] | list[{str: str}]
    :type email: None | basestring | list[basestring]

    :type interest_id: None | str | int | list[int]
    :type area_of_interest_ids: list[int] | None

    :param custom_fields_dict: custom_field_id -> value
    :type custom_fields_dict: dict[int, str] | None

    :param candidate_experience_dicts: dicts of organization, position, startMonth, startYear, endMonth, endYear, isCurrent
    :type candidate_experience_dicts: None | list[dict[basestring, int | basestring | list]]

    :param social_networks: socialNetworkId -> socialProfileUrl
    :type social_networks: None | dict[integer, basestring]

    :param candidate_skill_dicts: List of dicts of description, addedTime, totalMonths, and lastUsed. All except description are optional.
    :type candidate_skill_dicts: None | list[dict[basestring, basestring | integer | datetime.date]]

    :rtype: dict[basestring, int]
    :return: dict of candidate info
    """
    import datetime
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
    # TODO eventually deprecate the current_company and current_title inputs, and only use candidate_experience_dicts
    if (current_company or current_title) and not candidate_experience_dicts:
        candidate_experience_dicts = [dict(organization=current_company, position=current_title)]
    elif (not current_company or not current_title) and candidate_experience_dicts:
        current_company = candidate_experience_dicts[0].get('organization')
        current_title = candidate_experience_dicts[0].get('position')

    # Check if candidate already exists via id or email
    is_update = False

    domain_id = domain_id_from_user_id(owner_user_id)

    if candidate_id:
        is_update = True
    elif dice_social_profile_id or dice_profile_id or (email and update_if_email_exists):
        # Is this an existing candidate?
        candidate = None
        # Check for existing Dice social profile ID and Dice profile ID
        if dice_social_profile_id:
            candidate = db.session.query(Candidate).join(User).filter(
                Candidate.dice_social_profile_id == dice_social_profile_id, Candidate.user_id == User.id,
            User.domain_id == domain_id).first()

        elif dice_profile_id:
            candidate = db.session.query(Candidate).join(User).filter(
                Candidate.dice_profile_id == dice_profile_id,
                User.domain_id == domain_id
            ).first()

        # If candidate still not found, check for existing email address, if specified
        if not candidate and email and update_if_email_exists:
            if isinstance(email[0], dict):
                email = email[0].get('address')
            candidate = db.session.query(CandidateEmail).join(User).filter(
                CandidateEmail.address.in_(email),
                CandidateEmail.candidate_id == candidate_id,
                User.domain_id == domain_id
            ).first()

        # If candidate found, this is an update
        if candidate:
            candidate_id = candidate.id
            is_update = True

    # If source_id has not been specified, set it to the domain's 'Unassigned' candidate_source
    if not source_id:
        unassigned_candidate_source = get_or_create_unassigned_candidate_source(domain_id)
        source_id = unassigned_candidate_source.id
    # Create the candidate if it doesn't exist
    if not is_update:
        candidate_id = db.session.add(Candidate(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            added_time=added_time,
            formatted_name=formatted_name,
            candidate_status_id=1,
            user_id=owner_user_id,
            domain_can_write=domain_can_write,
            domain_can_read=domain_can_read,
            dice_profile_id=dice_profile_id,
            dice_social_profile_id=dice_social_profile_id,
            source_product_id=source_product_id,
            source_id=source_id,
            objective=objective,
            summary=summary
        ))
    logger.info("create_candidate_from_params: candidate_id=%s, is_update=%s", candidate_id, is_update)

    # Update firstName, middleName, lastName, formattedName
    if is_update and formatted_name:
        db.session.query(Candidate).filter_by(candidate_id=candidate_id).update(
            dict(first_name=first_name, middle_name=middle_name, last_name=last_name, formatted_name=formatted_name))
        db.session.commit()
    # Update objective/summary if necessary
    if (objective or summary) and is_update:
        db.session.query(Candidate).filter_by(id=candidate_id).update(dict(objective=objective, summary=summary))
        db.session.commit()
    # Make candidate's email/phone
    if email:
        for i, address in enumerate(email):
            existing_email_addresses = [row.address for row in db.session.query(CandidateEmail).filter_by(
                candidate_id=candidate_id)] if is_update else []
            if address and (address not in existing_email_addresses):
                is_default = i == 0 and not existing_email_addresses
                db.session.add(CandidateEmail(address=address, candidate_id=candidate_id,
                                              is_default=is_default, email_label_id=1))

    if phone:
        for i, number in enumerate(phone):
            # Converting number into canonical form
            number = canonicalize_phonenumber(number)

            existing_phone_numbers = [row.value for row in
                                      db.session.query(CandidatePhone).fiter_by(candidate_id == candidate_id)] \
                if is_update else []
            if number and (number not in existing_phone_numbers):
                is_default = i == 0 and not existing_phone_numbers
                db.session.add(CandidatePhone(value=number, candidate_id=candidate_id,
                                              is_default=is_default, phone_label_id=1))

    # If it's an update and the candidate's diceProfileId or diceSocialProfileId weren't previously set, then set them.
    if is_update and (dice_social_profile_id or dice_profile_id):
        candidate = db.session.query(Candidate).get(candidate_id)
        if dice_social_profile_id and (dice_social_profile_id != candidate.diceSocialProfileId):
            candidate.update_record(dice_social_profile_id=dice_social_profile_id)
        if dice_profile_id and (dice_profile_id != candidate.diceProfileId):
            candidate.update_record(dice_profile_id=dice_profile_id)

    # Experience
    if candidate_experience_dicts:
        expected_candidate_experience_dict_keys = ('organization', 'position', 'startYear', 'startMonth', 'endYear',
                                                   'endMonth', 'isCurrent', 'candidate_experience_bullets')
        if is_update:
            existing_candidate_experiences = db.session.query(CandidateExperience).filter_by(candidate_id=candidate_id)
        else:
            existing_candidate_experiences = db.session.query(CandidateExperience).all().as_dict()
        #existing_candidate_experiences = db(db.candidate_experience.candidateId == candidate_id).select() if is_update else Rows()
        current_candidate_experience_id = None
        for candidate_experience_dict in candidate_experience_dicts:

            # Dict key name validation
            if not candidate_experience_dict.get('organization') and not candidate_experience_dict.get('position'):
                logger.error("create_candidate_from_params(%s): Got candidate_experience_dict without organization or "
                             "position: %s",
                             candidate_id, candidate_experience_dict)
                continue
            if any(filter(lambda key: key not in expected_candidate_experience_dict_keys, candidate_experience_dict.keys())):
                logger.error("create_candidate_from_params(%s): Got unknown keys in candidate_experience_dict: %s",
                             candidate_id, candidate_experience_dict)

            # Make sure the start/end month/year are all integers
            try:
                start_year = int(candidate_experience_dict.get('startYear')) if \
                    candidate_experience_dict.get('startYear') else None
                start_month = int(candidate_experience_dict.get('startMonth')) if \
                    candidate_experience_dict.get('startMonth') else None
                end_year = int(candidate_experience_dict.get('endYear')) if \
                    candidate_experience_dict.get('endYear') else None
                end_month = int(candidate_experience_dict.get('endMonth')) if \
                    candidate_experience_dict.get('endMonth') else None
                is_current = 1 if candidate_experience_dict.get('isCurrent') else 0
            except Exception:
                logger.exception("create_candidate_from_params(%s): Error parsing the start/end month/year from "
                                 "the candidate_experience_dict: %s", candidate_id, candidate_experience_dict)
                continue

            # TODO come up with a more intelligent way of detecting duplicate candidate_experiences.
            # Currently we're only checking to see if the below
            # fields match, but we can be smarter about it w/ some common sense

            # Search for a duplicate candidate_experience, and don't add it if it's already there
            matching_candidate_experience = existing_candidate_experiences.any(
                lambda re_row: (re_row.organization == candidate_experience_dict.get('organization')) and
                               (re_row.position == candidate_experience_dict.get('position')) and
                               (re_row.startYear == start_year) and
                               (re_row.startMonth == start_month) and
                               (re_row.endYear == end_year) and
                               (re_row.endMonth == end_month)).first()
            if not matching_candidate_experience:
                candidate_experience_id = db.session.add(CandidateExperience(candidate_id=candidate_id,
                                                                             organization=candidate_experience_dict.get('organization'),
                                                                             position=candidate_experience_dict.get('position'),
                                                                             start_year=start_year,
                                                                             start_month=start_month,
                                                                             end_year=end_year,
                                                                             end_month=end_month,
                                                                             is_current=is_current))
                if is_current:
                    current_candidate_experience_id = is_current

                # Insert the candidate_experience_bullets
                if candidate_experience_dict.get('candidate_experience_bullets'):
                    for i, candidate_experience_bullet_dict in enumerate(candidate_experience_dict[
                                                                             'candidate_experience_bullets']):
                        # Dict validation
                        if any(filter(lambda key: key != 'description', candidate_experience_bullet_dict.keys())):
                            logger.error("create_candidate_from_params(%s): "
                                         "Got unknown keys in candidate_experience_bullet_dict: %s",
                                         candidate_id, candidate_experience_bullet_dict)
                        # Insert the candidate_experience_bullet
                        db.candidate_experience_bullet.insert(candidateExperienceId=candidate_experience_id,
                                                              listOrder=i + 1,
                                                              description=candidate_experience_bullet_dict.get(
                                                                  'description'))

        # Set isCurrent to 0 for all candidate_experiences (of this resume), except the current one
        if current_candidate_experience_id:
            db.session.query(CandidateExperience).filter(candidate_id == candidate_id,
                                                         CandidateExperience.id != current_candidate_experience_id).\
                update({"isCurrent": 0})

    # Text comments
    if len(candidate_text_comment):
        if isinstance(candidate_text_comment, basestring):
            existing_candidate_text_comments = [row.comment for row in
                                                db.session.query(CandidateTextComment).filter_by(
                                                    candidate_id == candidate_id)] if is_update else []
            if candidate_text_comment not in existing_candidate_text_comments:
                db.session.add(CandidateTextComment(candidate_id=candidate_id, list_order=0 if
                existing_candidate_text_comments else 1, comment=candidate_text_comment))

        else:
            # just insert them for now, no need to update
            for comment in candidate_text_comment:
                db.session.add(CandidateTextComment(candidate_id=candidate_id, list_order=0, comment=comment))
    # Address
    if city or state or zip_code:
        existing_address_tuples = [(row.city, row.state, row.zipCode) for row in
                                   db.session.query(CandidateAddress).filter_by(
                                       candidate_id=candidate_id)]if is_update else []
        if (city, state, zip_code) not in existing_address_tuples:

            lat_lon = get_coordinates(zip_code, city, state) if (not latitude or not longitude) else "%s,%s" % (latitude, longitude)

            # Validate US zip codes
            zip_code = sanitize_zip_code(zip_code)
            db.session.add(CandidateAddress(candidate_id=candidate_id,
                                            city=city,
                                            state=state,
                                            zip_code=zip_code,
                                            country_id=country_id,
                                            coordinates=lat_lon,
                                            is_default=0 if existing_address_tuples else 1))

    elif latitude and longitude:  # If only lat & lon provided, do reverse geolocation
        # TODO reverse-geolocate this and set other fields in candidate_address
        existing_addresses = db.session.query(CandidateAddress).filter_by(candidate_id == candidate_id)
        lat_lon_str = "%s,%s" % (latitude, longitude)
        matching_address = existing_addresses.filter(CandidateAddress.coordinates == lat_lon_str).first()
        if not matching_address:
            db.session.add(CandidateAddress(coordinates=lat_lon_str, candidate_id=candidate_id))

    # Education fields
    from datetime import datetime
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

    if university:
        from datetime import datetime
        # Find existing candidate_education (university) id, if any
        candidate_education_id = None
        if is_update:
            existing_candidate_educations = db.session.query(CandidateEducation).filter_by(candidate_id == candidate_id)
            if existing_candidate_educations:
                existing_candidate_education = existing_candidate_educations.filter(
                    CandidateEducation.school_name == university).first()
                candidate_education_id = existing_candidate_education.id if existing_candidate_education else None
        else:
            existing_candidate_educations = []

        # Insert new university, unless it already exists
        if not candidate_education_id:
            candidate_education_id = db.session.add(CandidateEducation(candidate_id=candidate_id,
                                                                       list_order=1 if not existing_candidate_educations
                                                                       else len(existing_candidate_educations) + 1,
                                                                       schoolName=university,
                                                                       countryId=country_id))

        # Insert new degree, unless it already exists
        classification_type = classification_type_code_to_classification_type(degree) or {}
        classification_type_id = classification_type.get('id')
        classification_type_description = classification_type.get('description')

        candidate_education_degree_id = None
        if is_update:
            existing_candidate_education_degrees = db.session.query(CandidateEducationDegree).filter_by(
                candidate_education_id == candidate_education_id)
            existing_candidate_education_degree = existing_candidate_education_degrees.filter(and_(
                CandidateEducationDegree.degree_type == degree,
                CandidateEducationDegree.classification_type_id == classification_type_id)).first()

            # If degree's start/end dates are different, update them
            if existing_candidate_education_degree and (graduation_year or graduation_month or university_start_month
                                                        or university_start_year):
                existing_candidate_education_degree.update_record(
                    end_time=datetime(year=graduation_year, month=graduation_month, day=1) if
                    graduation_year and graduation_month else None,
                    start_time=datetime(year=university_start_year, month=university_start_month, day=1) if
                    university_start_year and university_start_month else None)
            candidate_education_degree_id = existing_candidate_education_degree.id if \
                existing_candidate_education_degree else None
        else:
            existing_candidate_education_degrees = []

        if not candidate_education_degree_id:
            candidate_education_degree_id = db.session.add(CandidateEducationDegree(
                candidate_education_id=candidate_education_id,
                degree_type=degree,
                degree_title=classification_type_description,
                list_order=1 if not existing_candidate_education_degrees else
                len(existing_candidate_education_degrees) + 1,
                end_time=datetime(year=graduation_year, month=graduation_month, day=1) if graduation_year and
                                                                                          graduation_month else None,
                start_time=datetime(year=university_start_year, month=university_start_month, day=1) if
                university_start_year and university_start_month else None,
                classification_type_id=classification_type_id))

        # Insert new degree bullet, unless already exists
        if is_update:
            existing_candidate_education_degree_bullets = db.session.add(CandidateEducationDegreeBullet).filter_by(
                candidate_education_degree_id == candidate_education_degree_id)
            existing_candidate_education_degree_bullet = existing_candidate_education_degree_bullets.filter(
                CandidateEducationDegreeBullet.concentration_type == major).first()
            candidate_education_degree_bullet_id = existing_candidate_education_degree_bullet.id if \
                existing_candidate_education_degree_bullet else None
        else:
            existing_candidate_education_degree_bullets = []
            candidate_education_degree_bullet_id = None

        if not candidate_education_degree_bullet_id:
            db.session.add(CandidateEducationDegreeBullet(
                candidate_education_degree_id=candidate_education_degree_id,
                list_order=1 if not existing_candidate_education_degree_bullets else
                len(existing_candidate_education_degree_bullets) + 1,
                concentration_type=major))

    elif graduation_month or graduation_year:  # If no university name provided, but graduation date provided
        # TODO make the create/update logic behind the education fields smarter
        if is_update:
            # Currently, this looks for an existing candidate_education_degree that's missing a graduation year & month,
            # and updates that.
            existing_candidate_education_degrees = db.session.query(CandidateEducationDegree).join(CandidateEducation).\
                filter(and_(CandidateEducationDegree.candidate_education_id == CandidateEducation.id,
                            CandidateEducation.candidate_id == candidate_id)).all()
            candidate_education_degree_without_graduation = existing_candidate_education_degrees.filter(
                CandidateEducationDegree.end_time is None).first()
            if candidate_education_degree_without_graduation:
                candidate_education_degree_without_graduation.update_record(
                    end_time=datetime(year=graduation_year, month=graduation_month, day=1) if
                    graduation_year and graduation_month else None)
        else:
            # Create new candidate_education and candidate_education_degree
            candidate_education_id = db.session.add(CandidateEducation(candidate_id=candidate_id,
                                                                       list_order=1, country_id=country_id))

            # Insert new degree, unless it already exists
            classification_type = classification_type_code_to_classification_type(degree)
            classification_type_id = classification_type.get('id')
            classification_type_description = classification_type.get('description')

            db.session.add(CandidateEducationDegree(
                candidate_education_id=candidate_education_id,
                degree_type=degree,
                degree_title=classification_type_description,
                list_order=1,
                end_time=datetime(year=graduation_year, month=graduation_month, day=1) if graduation_year and
                                                                                          graduation_month else None,
                start_time=datetime(year=university_start_year, month=university_start_month, day=1) if
                university_start_year and university_start_month else None,
                classification_type_id=classification_type_id))

    # Candidate Interest
    if interest_id:
        interest_id = "%d" % interest_id if isinstance(interest_id, int) else interest_id
        interest_ids = [interest_id] if isinstance(interest_id, basestring) else interest_id
        for interest_id in interest_ids:
            candidate_area_of_interest_set = db.session.query(CandidateAreaOfInterest).filter(
                and_(CandidateAreaOfInterest.area_of_interest_id == interest_id,
                     CandidateAreaOfInterest.candidate_id == candidate_id))

            existing_candidate_area_of_interest = candidate_area_of_interest_set.first()
            # If updating notes (additional notes), only update record. otherwise create
            if existing_candidate_area_of_interest and existing_candidate_area_of_interest.additionalNotes != interest_info:
                candidate_area_of_interest_set.update({"additionalNotes": interest_info})
            elif not existing_candidate_area_of_interest:
                try:
                    db.session.add(CandidateAreaOfInterest(area_of_interest_id=interest_id,
                                                           additional_notes=interest_info,
                                                           candidate_id=candidate_id))
                except Exception:
                    logger.exception("Error inserting candidate_area_of_interest. aoi ID=%s, candidateId=%s", interest_id, candidate_id)

    # Military service
    if military_branch or military_grade or military_status or military_to_date:
        # key on candidateId and branch
        existing_candidate_military_service = db.session.query(CandidateMilitaryService).filter(and_(
            CandidateMilitaryService.candidate_id == candidate_id,
            CandidateMilitaryService.branch == military_branch)).first()
        if is_update and existing_candidate_military_service:
            existing_fields_tuple = (existing_candidate_military_service.serviceStatus,
                                     existing_candidate_military_service.highestGrade,
                                     existing_candidate_military_service.toDate)
            if existing_fields_tuple != (military_status, military_grade,
                                         military_to_date):  # if updating military information of same branch...
                existing_candidate_military_service.update_record(service_status=military_status,
                                                                  highest_grade=military_grade, to_date=military_to_date)

        else:  # if creating new military record...
            db.session.add(CandidateMilitaryService(candidate_id=candidate_id,
                                                    country_id=country_id,
                                                    service_status=military_status,
                                                    highest_grade=military_grade,
                                                    branch=military_branch,
                                                    to_date=military_to_date))

    # Custom fields
    if custom_fields_dict:
        current_custom_fields = db.session.query(CandidateCustomField).filter_by(candidate_id == candidate_id) if \
            is_update else []
        add_candidate_custom_fields(candidate_id, current_candidate_custom_fields=current_custom_fields,
                                    candidate_custom_fields_dict=custom_fields_dict)

    # Areas of interest
    if area_of_interest_ids:
        from candidate_service.modules.talent_area_of_interest import add_aoi_to_candidate
        add_aoi_to_candidate(candidate_id, area_of_interest_ids)

    # Normal/Job Alert subscription preference
    if subscription_preference_frequency_id:
        normal_subscription_pref = get_subscription_preference(candidate_id)

        # Create/update normal subscription preference
        if subscription_preference_frequency_id:
            if subscription_preference_frequency_id < 0:
                subscription_preference_frequency_id = None
            if not normal_subscription_pref:  # If unsubscribing...
                db.session.add(CandidateSubscription(candidate_id=candidate_id,
                                                     frequency_id=subscription_preference_frequency_id))
            else:
                normal_subscription_pref.update_record(frequencyId=subscription_preference_frequency_id)

    # Social networks
    if social_networks:
        for social_network_id, social_profile_url in social_networks.items():
            if not social_network_id or not social_profile_url:
                logger.warn("create_candidate_from_params(%s): social_network_id=%s, social_profile_url=%s",
                            candidate_id, social_network_id, social_profile_url)
                continue

            # Update the profile URL if candidate already has a profile in this social network.
            # Or, create a new one
            existing_candidate_social_network = db.session.query(CandidateSocialNetwork).filter(and_(
                CandidateSocialNetwork.social_network_id == social_network_id,
                CandidateSocialNetwork.candidate_id == candidate_id
            )).first() if is_update else None
            if existing_candidate_social_network:
                existing_candidate_social_network.update({"social_profile_url": social_profile_url})
            else:
                db.session.add(CandidateSocialNetwork(social_network_id=social_network_id,
                                                      social_profile_url=social_profile_url,
                                                      candidate_id=candidate_id))

    # Skills
    if candidate_skill_dicts:
        expected_candidate_skill_dict_keys = ('description', 'totalMonths', 'lastUsed')

        # Get all existing skills of candidate so we can dedup
        if is_update:
            existing_candidate_skills = db.session.query(CandidateSkill).filter_by(candidate_id == candidate_id)
        else:
            existing_candidate_skills = db.session.query(CandidateSkill).all()
        next_list_order = len(existing_candidate_skills) + 1

        for candidate_skill_dict in candidate_skill_dicts:
            # Dict validation
            if not candidate_skill_dict.get('description'):
                logger.error("create_candidate_from_params: candidate_skill_dict did not have description: %s", candidate_skill_dict)
                continue
            if any(filter(lambda key: key not in expected_candidate_skill_dict_keys, candidate_skill_dict.keys())):
                logger.error("create_candidate_from_params(%s): Got unknown keys in candidate_skill_dict: %s",
                             candidate_id, candidate_skill_dict)

            # Update the existing skill, if it exists
            existing_skill = existing_candidate_skills.filter(
                CandidateSkill.description == candidate_skill_dict['description']).first()
            if existing_skill:
                existing_skill.update(dict(description=candidate_skill_dict['description'],
                                           total_months=candidate_skill_dict.get('totalMonths') or
                                           existing_skill.total_months,
                                           last_used=candidate_skill_dict.get('lastUsed') or existing_skill.last_used))
            else:
                # Create new skill
                db.session.add(CandidateSkill(candidate_id=candidate_id,
                                              list_order=next_list_order,
                                              description=candidate_skill_dict['description'],
                                              total_months=candidate_skill_dict.get('totalMonths'),
                                              last_used=candidate_skill_dict.get('lastUsed')))
            # Increment list order
            next_list_order += 1

    # work preferences
    if work_preference:
        existing_work_preference = db.session.query(CandidateWorkPreference).filter_by(candidate_id=candidate_id).first()
        if existing_work_preference:
            existing_work_preference.update(dict(relocate=work_preference.get(
                                                    'relocate') or work_preference.get("willing_to_relocate"),
                                                 authorization=work_preference['authorization'],
                                                 telecommute=work_preference['telecommute'],
                                                 travel_percentage=work_preference.get(
                                                    'travel') or work_preference.get('travel_percentage'),
                                                 hourly_rate=work_preference['hourly_rate'],
                                                 salary=work_preference['salary'],
                                                 tax_terms=work_preference.get(
                                                    'tax_terms') or work_preference.get('employment_type'),
                                                 security_clearance=work_preference['security_clearance'],
                                                 third_party=work_preference['third_party']))
        else:
            db.session.add(CandidateWorkPreference(candidateId=candidate_id,
                                                   relocate=work_preference.get(
                                                       'relocate') or work_preference.get("willing_to_relocate"),
                                                   authorization=work_preference['authorization'],
                                                   telecommute=work_preference['telecommute'],
                                                   travel_percentage=work_preference.get(
                                                       'travel') or work_preference.get('travel_percentage'),
                                                   hourly_rate=work_preference['hourly_rate'],
                                                   salary=work_preference['salary'],
                                                   tax_terms=work_preference.get(
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

    # If the user is a Dice user, use the SocialCV API to get more data about the candidate
    if import_from_socialcv and email:
        owner_user = db.session.query(User).get(owner_user_id)
        if owner_user.diceUserId:
            queue_task("merge_candidate_data_from_socialcv",
                       function_vars=dict(candidate_email=email, owner_user_id=owner_user_id))

    if do_db_commit:
        db.session.commit()

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
            # Phonenumber format is : +1 (123) 456-7899
            return '+1 ' + phonenumbers.format_number(parsed_phonenumbers, phonenumbers.PhoneNumberFormat.NATIONAL)
        else:
            logger.error("canonicalize_phonenumber: [%s] is an invalid or non-US Phone Number", phonenumber)
            return False
    except phonenumbers.NumberParseException:
        logger.info("canonicalize_phonenumber: [%s] is an invalid or non-US Phone Number", phonenumber)
        return False
    except:
        logger.info("canonicalize_phonenumber: [%s] is an invalid or non-US Phone Number", phonenumber)
        return False


def get_or_create_unassigned_candidate_source(domain_id):
    unassigned_candidate_source = db.session.query(CandidateSource).filter(
        CandidateSource.description == 'Unassigned', CandidateSource.domain_id == domain_id)
    if unassigned_candidate_source:
        return unassigned_candidate_source
    else:
        db.session.add(CandidateSource(description='Unassigned', domain_id=domain_id))
        unassigned_candidate_source = db.session.query(CandidateSource).filter(
        CandidateSource.description == 'Unassigned', CandidateSource.domain_id == domain_id)
        return db.candidate_source(unassigned_candidate_source)


def sanitize_zip_code(zip_code):
    # Folowing expression will validate US zip codes e.g 12345 and 12345-6789
    zip_code = str(zip_code)
    zip_code = ''.join(filter(lambda character: character not in ' -', zip_code))  # Dashed and Space filtered Zip Code
    if zip_code and not ''.join(filter(lambda character: not character.isdigit(), zip_code)):
        zip_code = zip_code.zfill(5) if len(zip_code) <= 5 else zip_code.zfill(9) if len(zip_code) <= 9 else ''
        if zip_code:
            return (zip_code[:5] + ' ' + zip_code[5:]).strip()
    logger.info("[%s] is not a valid US Zip Code", zip_code)
    return None


def classification_type_code_to_classification_type(code):
    code_hash = db.session.query(Clasification).all().as_dist('code')
    return code_hash.get(code) or code_hash.get('UNSPECIFIED')


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
    """
    email_prefs = db.session.query(CandidateSubscription).filter_by(candidate_id == candidate_id)
    non_custom_pref = email_prefs.filter(and_(CandidateSubscription.frequency_id,
                                              CandidateSubscription.frequency_id < 7)).first()
    null_pref = email_prefs.filter(CandidateSubscription.frequency_id).first()
    custom_pref = email_prefs.filter(and_(CandidateSubscription.frequency_id,
                                          CandidateSubscription.frequency_id == 7)).first()
    if non_custom_pref:
        all_other_prefs = email_prefs.filter(CandidateSubscription.id != non_custom_pref.id)
        all_other_prefs_ids = [cs_id for cs_id in all_other_prefs]
        logger.info("get_subscription_preference: Deleting non-custom prefs for candidate %s: %s",
                    candidate_id, all_other_prefs_ids)
        for cs_id in all_other_prefs_ids:
            cs_row = db.session.query(CandidateSubscription).filter_by(id=cs_id)
            cs_row.delete()
        return non_custom_pref
    elif null_pref:
        non_null_prefs = email_prefs.filter(CandidateSubscription.id != null_pref.id)
        non_null_prefs_id = [cs_id for cs_id in non_null_prefs]
        logger.info("get_subscription_preference: Deleting non-null prefs for candidate %s: %s", candidate_id, non_null_prefs_id)
        for cs_id in non_null_prefs_id:
            cs_row = db.session.query(CandidateSubscription).filter_by(id=cs_id)
            cs_row.delete()
        return null_pref
    elif custom_pref:
        email_prefs_ids = [cs_id for cs_id in email_prefs]
        logger.info("get_subscription_preference: Deleting all prefs for candidate %s: %s", candidate_id, email_prefs_ids)
        for cs_id in email_prefs_ids:
            cs_row = db.session.query(CandidateSubscription).filter_by(id=cs_id)
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


def queue_task(function_name, function_vars, timeout_seconds=3600 * 24 * 14, task_name=None):
    return schedule_task(function_name, function_vars, start_time=datetime.datetime.utcnow(),
                         stop_time=None, period=0, repeats=1, timeout_seconds=timeout_seconds)


def schedule_task(function_name, function_vars, start_time, stop_time, period,
                  repeats, timeout_seconds=3600 * 24 * 14):
    scheduler = current_app.scheduler
    scheduler_task_row = scheduler.queue_task(function_name,
                                              task_name=function_name,
                                              pvars=function_vars,
                                              timeout=timeout_seconds,
                                              start_time=start_time,
                                              stop_time=stop_time,
                                              period=period,
                                              repeats=repeats)
    if scheduler_task_row.errors:
        logger.error("Error scheduling task %s with vars %s: %s", function_name, function_vars, scheduler_task_row.errors)

    return scheduler_task_row.id