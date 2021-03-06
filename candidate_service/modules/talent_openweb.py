"""
Functions related to candidate_service/candidate_app/api validations
"""

from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate, CandidateSocialNetwork, SocialNetwork
from candidate_service.common.models.user import User
from candidate_service.common.error_handling import InternalServerError, NotFoundError, UnauthorizedError
from candidate_service.candidate_app import logger
from candidate_service.common.utils.validators import format_phone_number, parse_openweb_date
from candidate_service.modules.validators import does_candidate_belong_to_users_domain
from candidate_service.common.models.talent_pools_pipelines import TalentPool
import requests, datetime

SOCIALCV_API_KEY = "c96dfb6b9344d07cee29804152f798751ae8fdee"


def query_openweb(url, type):
    """
    Function search openweb endpoint for social network url
    :param url: social-network-url: string
    :param type: email=1 or url=0
    :return: json object
    """
    try:
        if type == 0:
            openweb_response = requests.get("http://api.thesocialcv.com/v3/profile/data.json",
                                            params=dict(apiKey=SOCIALCV_API_KEY, webProfile=url))
        elif type == 1:
            openweb_response = requests.get("http://api.thesocialcv.com/v3/profile/data.json",
                                            params=dict(apiKey=SOCIALCV_API_KEY, email=url))

    except Exception as e:
        raise InternalServerError(error_message="%s" % e.message)

    if openweb_response.status_code == 404:
        if type == 0:
            openweb_crawl(url)
        return False

    if openweb_response.status_code != 200:
        raise InternalServerError(error_message="Response error")

    return openweb_response.json()


def find_in_openweb_by_email(candidate_email):
    """
    Function search openweb endpoint for email address
    :param candidate_email string
    :return: json object
    """
    openweb_response = query_openweb(candidate_email, 1)
    if openweb_response:
        return False, openweb_response
    else:
        raise NotFoundError(error_message="%s not found" % candidate_email)


def match_candidate_from_openweb(url, auth_user):
    """
    Fetches candidate profiles from openweb and compare it to local db
    :param url:
    :param auth_user:
    :return: candidate sql query
    """
    openweb_response = query_openweb(url, 0)
    urls = []
    users_in_domain = [int(domain_user.id) for domain_user in
                       db.session.query(User).filter(User.domain_id == auth_user.domain_id).all()]

    if openweb_response:
        for candidate_url in openweb_response['webProfiles']:
            urls.append(openweb_response['webProfiles'][candidate_url]['url'])

        # find if candidate exists in gT database
        candidate_query = db.session.query(Candidate).join(CandidateSocialNetwork) \
            .filter(CandidateSocialNetwork.social_profile_url.in_(urls), Candidate.user_id.in_(users_in_domain)).first()

        if candidate_query:
            return True, candidate_query
        else:
            return False, openweb_response
    else:
        # in case candidate is not found in thesocialcv, try to find the url in directly from the database
        candidate_query = db.session.query(Candidate).join(CandidateSocialNetwork) \
            .filter(CandidateSocialNetwork.social_profile_url == url, Candidate.user_id.in_(users_in_domain)).first()
        if candidate_query:
            return True, candidate_query
        else:
            raise NotFoundError(error_message="candidate not found")


def openweb_crawl(url):
    """
    Sends a request to openweb to crawl social network link that does not currently exists there
    :param url: string
    :return: None
    """
    if not isinstance(url, basestring):
        return False
    try:
        crawl_request = requests.get("http://api.thesocialcv.com/v3/profile/crawl.json", params=dict(apiKey=SOCIALCV_API_KEY, profileUrl=url), timeout=10)
        if crawl_request.status_code == 200:
            logger.info("Sending crawl request to openweb for %s" % url)
    except Exception as e:
        logger.exception("Error: %s crawling link: %s", (e, url))


def convert_dice_candidate_dict_to_gt_candidate_dict(dice_candidate_dict, authed_user):
    """
    ONLY converts the dict object. Won't put in `id` fields or do anything to the DB.

    :param dice_candidate_dict: Dice/OpenWeb candidate dict
    :return: getTalent-style Candidate dict
    """

    social_profile_dict = dice_candidate_dict
    dice_profile_dict = dice_candidate_dict

    talent_pool_ids = [tid.id for tid in TalentPool.query.filter_by(domain_id=authed_user.domain_id)]

    dice_profile_contact_dict = dice_profile_dict.get('contact') or {}
    emails = [social_profile_dict.get('email') or dice_profile_contact_dict.get('email')]
    emails = filter(None, emails)

    # Get candidate's name, phone number, and address
    formatted_name = social_profile_dict.get('name') or dice_profile_contact_dict.get('formattedName')  # socialProfile name over diceProfile name

    phones = []
    social_profile_location_dict = social_profile_dict.get('location') or {}
    if dice_profile_contact_dict.get('phoneNumber'):
        phone_number = "%s%s".format(dice_profile_contact_dict.get('areaCode', ""), dice_profile_contact_dict.get('phoneNumber'))
        phone_number = format_phone_number(phone_number, country_code=social_profile_location_dict.get('country', ''))
        if phone_number:
            phones.append(phone_number)

    latitude = social_profile_location_dict.get('latitude')
    longitude = social_profile_location_dict.get('longitude')
    dice_profile_location_dict = dice_profile_contact_dict.get('location') or {}
    country_code_or_name = social_profile_location_dict.get('country')
    city = social_profile_location_dict.get('town') or dice_profile_location_dict.get('municipality')
    state = social_profile_location_dict.get('text')
    if state:
        try:
            state = state.split(',')[1]
        except IndexError:
            state = state

    zip_code = dice_profile_location_dict.get('postalCode')

    # Get candidate's social network profiles
    social_networks = []
    web_profiles_dict = social_profile_dict.get('webProfiles') or {}

    if web_profiles_dict:
        social_networks_names = []
        for social_network_name, info_dict in web_profiles_dict.items():
            social_networks_names.append(social_network_name)
        all_social_networks = db.session.query(SocialNetwork.id, SocialNetwork.name).filter(SocialNetwork.name.in_(social_networks_names)).all()

        for social_network_name, info_dict in web_profiles_dict.items():
            social_network_row = filter(lambda sn_row: sn_row.name.lower() == social_network_name.lower(), all_social_networks)

            # If no matching social_network found, we create a new social network
            if len(social_network_row):
                social_network_id = social_network_row[0][0]
            else:
                logger.warn("Unknown social network from import_dice_candidates: %s. info_dict=%s. ", social_network_name, info_dict)
                from urlparse import urlparse

                parsed_obj = urlparse(url=info_dict.get('url'))
                social_network_homepage = "%s://%s" % (parsed_obj.scheme, parsed_obj.netloc)
                new_social_network = SocialNetwork(name=social_network_name, url=social_network_homepage)
                db.session.add(new_social_network)
                db.session.commit()
                social_network_id = new_social_network.id
                logger.info("Auto-created social_network, id=%s, homepage=%s", social_network_id, social_network_homepage)

            social_networks.append({'profile_url': info_dict.get('url'), 'name': social_network_name})

    # Get CandidateExperience objects from OpenWeb and Dice dicts

    work_experiences = []
    social_profile_dict_experience = social_profile_dict.get('experience') or {}
    history_dicts = social_profile_dict_experience.get('history') or []
    start_year = None
    start_month = 1
    end_year = None
    end_month = 1
    for i, history_dict in enumerate(history_dicts):
        # Parse startedAt and endedAt
        start_date_obj = parse_openweb_date(history_dict.get('startedAt'))
        if start_date_obj:
            start_year = start_date_obj.year or None
            start_month = start_date_obj.month or 1
        end_date_obj = parse_openweb_date(history_dict.get('endedAt'))
        if end_date_obj:
            end_year = end_date_obj.year or None
            end_month = end_date_obj.month or 1

        # Parse out candidate_experience_bullets.
        candidate_experience_bullets = []
        if history_dict.get('description'):
            candidate_experience_bullets.append(dict(description=history_dict.get('description')))

        work_experiences.append(dict(organization=history_dict.get('company'),
                                     position=history_dict.get('jobTitle'),
                                     start_year=start_year,
                                     end_year=end_year,
                                     start_month=start_month,
                                     end_month=end_month,
                                     is_current=i == 0,  # Assume the very first element is the current one
                                     bullets=candidate_experience_bullets))

        start_year, start_month, end_year, end_month = None, None, None, None
        
    employment_history_list = dice_profile_dict.get('employmentHistoryList') or []
    for i, employment_dict in enumerate(employment_history_list):
        # Parse out candidate_experience_bullets.
        candidate_experience_bullets = []
        if employment_dict.get('description'):
            # using TalentCore._split_description
            candidate_experience_bullets.append(dict(text=employment_dict['description']))

        start_year = int(employment_dict.get('startYear')) or None
        start_month = int(employment_dict.get('startMonth', 1)) or 1
        end_year = int(employment_dict.get('endYear')) or None
        end_month = int(employment_dict.get('endMonth', 1)) or 1

        work_experiences.append(dict(organization=history_dict.get('company'),
                                     position=history_dict.get('jobTitle'),
                                     start_year=start_year,
                                     end_year=end_year,
                                     start_month=start_month,
                                     end_month=end_month,
                                     bullets=candidate_experience_bullets))

    # Skills
    skills = []  # Array of CandidateSkill objects
    social_profile_dict_skills = social_profile_dict.get('skills') or {}
    for skill_name, months_experience in social_profile_dict_skills.iteritems():
        skills.append(dict(name=skill_name, months_used=months_experience if months_experience > 0 else None))
    if dice_profile_dict and dice_profile_dict.get('skillList'):
        for skill_dict in dice_profile_dict['skillList']:

            # Try to parse out 'years'. Sometimes it can be -1
            try:
                years = int(skill_dict['years'])
                if years < 0:
                    years = None
            except (KeyError, ValueError):
                years = None

            # Try to convert 'lastUsed' to date object (it's a year)
            try:
                from datetime import date

                year = int(skill_dict['lastUsed'])
                last_used = date(year=year, month=1, day=1) if (year <= (date.today().year + 1)) else None  # In case year is 2050 or some shit
            except (KeyError, ValueError):
                last_used = None

            # Add skill
            skills.append(dict(name=skill_dict.get('name'),
                               months_used=years * 12 if years else None,
                               last_used=last_used.isoformat()))

    # Interests (an array of strings), a text comment
    candidate_text_comment = None
    interests_array = social_profile_dict.get('interests')
    if interests_array:
        candidate_text_comment = "Interests: %s" % (', '.join([interest.strip() for interest in interests_array]))

    text_comments = [{
        'comment': candidate_text_comment,
        'created_at_datetime': datetime.datetime.utcnow().isoformat(),
    }]

    # Preferred Locations
    preferred_locations = dice_profile_dict.get('preferredLocationList', [])
    preferred_locations = [{'address_line_1': loc.get('addrOne'),
                            'address_line_2': loc.get('addrTwo'),
                            'zip_code': loc.get("postalCode"),
                            'city': loc.get('municipality'),  # I know, municipality is different than city, but for API consistency's sake we're putting city
                            'region': loc.get('region'),
                            'country': loc.get('country')} for loc in preferred_locations]

    # Work preferences
    dice_work_preference = dice_profile_dict.get('completedStatus', dict()).get('workDetails')
    work_preferences = dict()
    if 'true' in [str(dice_work_preference).lower()]:
        work_preferences["authorization"] = str(dice_profile_dict.get('desiredEmployment', dict()).get('workAuthorization'))
        work_preferences["employment_type"] = str(dice_profile_dict.get('desiredEmployment', dict()).get('type'))
        work_preferences["security_clearance"] = True if 'true' in [str(dice_profile_dict.get('desiredEmployment', dict()).get('securityClearance')).lower()] else False
        work_preferences["willing_to_relocate"] = True if 'true' in [str(dice_profile_dict.get('willingToRelocate')).lower()] else False
        work_preferences["travel_percentage"] = int(dice_profile_dict['willingToTravel'].split()[0]) if dice_profile_dict.get('willingToTravel', '').split() else None
        work_preferences["telecommute"] = True if 'true' in [str(dice_profile_dict.get('willingToTelecommute')).lower()] else False
        work_preferences["third_party"] = True if 'true' in [str(dice_profile_dict.get('thirdParty')).lower()] else False

    # Education
    universities_list = social_profile_dict.get('education') or []  # 'education' is a list of universities
    dice_profile_dict_education_list = dice_profile_dict.get('educationList') or []
    universities_list.extend([education_dict.get('institution') for education_dict in dice_profile_dict_education_list])
    universities_list = filter(None, universities_list)  # Remove empty university names
    educations = [{'school_name': university_name,
                   'city': None,
                   'state': None,
                   'country': None} for university_name in universities_list]

    image_url = social_profile_dict.get('imageUrl', '')

    # Addresses
    addresses = [{
        'address_line_1': None,
        'address_line_2': None,
        'city': city,
        'state': state,
        'zip_code': zip_code,
        'country': country_code_or_name,
        'is_default': True,
    }]

    gt_candidate_dict = {
        'full_name': formatted_name,
        'emails': [{'address': email} for email in emails],
        'phones': [{'value': phone} for phone in phones],
        'addresses': addresses,
        'preferred_locations': preferred_locations,
        'work_preference': work_preferences,
        'work_experiences': work_experiences,
        'educations': educations,
        'social_networks': social_networks,
        # 'military_services': candidate_military_services,
        'skills': skills,
        # 'text_comments': text_comments,
        'openweb_id': social_profile_dict.get('id'),
        'dice_profile_id': dice_profile_dict.get('id'),
        'talent_pool_ids': {"add": talent_pool_ids},
        'image_url': image_url
    }

    return gt_candidate_dict
