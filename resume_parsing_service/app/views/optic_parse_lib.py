"""Parsing functions for extracting specific information from Burning Glass API responses."""
# pylint: disable=wrong-import-position, fixme, import-error
__author__ = 'erik@getTalent.com'
# Standard Library
from time import time
import datetime
import HTMLParser
import re
import string
import sys
import unicodedata
import urllib2
# Third Party
from bs4 import BeautifulSoup as bs4
from contracts import contract
import requests
import phonenumbers
import pycountry
# Module Specific
from flask import current_app
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.app.views.OauthClient import OAuthClient
from resume_parsing_service.common.error_handling import ForbiddenError, InternalServerError
from resume_parsing_service.common.utils.validators import sanitize_zip_code
from resume_parsing_service.common.utils.handy_functions import normalize_value

ISO8601_DATE_FORMAT = "%Y-%m-%d"


@contract
def fetch_optic_response(resume, filename_str):
    """
    Takes in an encoded resume file and returns a bs4 'soup-able' format
    (utf-decode and html escape).
    :param str resume: a base64 encoded resume file.
    :return: HTML unquoted, utf-decoded string that represents the Burning Glass XML.
    :rtype: unicode
    """
    start_time = time()
    bg_url = current_app.config['BG_URL']
    oauth = OAuthClient(url=bg_url,
                        method='POST', consumerKey='StevePeck',
                        consumerSecret=current_app.config['CONSUMER_SECRET'],
                        token='Utility',
                        tokenSecret=current_app.config['TOKEN_SECRET'],
                        signatureMethod='HMAC-SHA1',
                        oauthVersion='1.0')
    auth = oauth.get_authorizationString()
    headers = {
        'accept': 'application/xml',
        'content-type': 'application/json',
        'Authorization': auth,
    }
    data = {
        'binaryData': resume,
        'instanceType': 'XRAY',
        'locale': 'en_us'
    }
    bg_response = requests.post(bg_url, headers=headers, json=data)

    if bg_response.status_code != requests.codes.ok:
        raise ForbiddenError(
            error_message=error_constants.BG_UNAVAILABLE['message'],
            error_code=error_constants.BG_UNAVAILABLE['code']
        )

    try:
        html_parser = HTMLParser.HTMLParser()
        unquoted = urllib2.unquote(bg_response.content).decode('utf8')
        unescaped = html_parser.unescape(unquoted)

    except Exception:
        logger.exception('Error translating BG response.')
        raise InternalServerError(
            error_message=error_constants.ERROR_DECODING_TEXT['message'],
            error_code=error_constants.ERROR_DECODING_TEXT['code']
        )

    logger.info(
        "Benchmark: fetch_optic_response({}) took {}s".format(filename_str,
                                                              time() - start_time)
    )
    return unescaped


@contract
def parse_optic_xml(resume_xml_text):
    """
    Takes in a Burning Glass XML tree in string format and returns a candidate JSON object.
    :param string resume_xml_text: An XML tree represented in unicode format. It is a slightly
                                   processed response from the Burning Glass API.
    :return: Results of various parsing functions on the input xml string.
    :rtype: dict
    """
    contact_xml_list = bs4(resume_xml_text, 'lxml').findAll('contact')
    experience_xml_list = bs4(resume_xml_text, 'lxml').findAll('experience')
    educations_xml_list = bs4(resume_xml_text, 'lxml').findAll('education')
    skill_xml_list = bs4(resume_xml_text, 'lxml').findAll('canonskill')
    summary_xml_list = bs4(resume_xml_text, 'lxml').findAll('summary')
    references_xml = bs4(resume_xml_text, 'lxml').findAll('references')
    emails = parse_candidate_emails(contact_xml_list)
    first_name, last_name = parse_candidate_name(contact_xml_list)
    references = parse_candidate_reference(references_xml)

    if emails and not first_name:
        first_name = emails[0].get('address')
        last_name = None

    return dict(
        first_name=first_name,
        last_name=last_name,
        emails=emails,
        phones=parse_candidate_phones(contact_xml_list),
        work_experiences=parse_candidate_experiences(experience_xml_list),
        educations=parse_candidate_educations(educations_xml_list),
        skills=parse_candidate_skills(skill_xml_list),
        addresses=parse_candidate_addresses(contact_xml_list),
        talent_pool_ids={'add': None},
        references=references,
        summary=parse_candidate_summary(summary_xml_list)
    )


@contract
def parse_candidate_name(bs_contact_xml_list):
    """
    Parses a name from a list of contact tags found in a BGXML response.
    :param bs4_ResultSet bs_contact_xml_list:
    :return: Formatted name strings using title() in a dictionary.
    :rtype: tuple
    """

    givenname = None # Placeholder for a `first_name`.
    surname = None # Placeholder for a `last_name`.

    for contact in bs_contact_xml_list:
        # If a name is already parsed we do not want to reassign it.
        if not givenname:
            givenname = _tag_text(contact, 'givenname')

        if not surname:
            surname = _tag_text(contact, 'surname')

    if givenname:
        givenname = scrub_candidate_name(givenname)

    if surname:
        surname = scrub_candidate_name(surname)

    return (givenname, surname)


@contract
def parse_candidate_emails(bs_contact_xml_list):
    """
    Parses an email list from a list of contact tags found in a BGXML response.
    :param bs4_ResultSet bs_contact_xml_list:
    :return: List of dicts containing email data.
    :rtype: list(dict)
    """
    output = []
    for contact in bs_contact_xml_list:
        emails = contact.findAll('email')
        for email in emails:
            email_addr = normalize_value(email.text)
            output.append(email_addr)

    unique_emails = set(output)
    unique_output = []

    for email in unique_emails:
        unique_output.append({'address': email})

    return unique_output


@contract
def parse_candidate_phones(bs_contact_xml_list):
    """
    Parses a phone list from a list of contact tags found in a BGXML response.
    :param bs4_ResultSet bs_contact_xml_list:
    :return: List of dicts containing phone data.
    :rtype: list(dict)
    """
    output = []

    for contact in bs_contact_xml_list:
        phones = contact.findAll('phone')

        for phone in phones:
            raw_phone = phone.text.strip()
            phone_type = phone.get('type')

            # JSON_SCHEMA for candidates phone is max:20
            # This fixes issues with numbers like '1-123-45            67'
            if raw_phone and len(raw_phone) > 20:
                raw_phone = " ".join(raw_phone.split())

            gt_phone_type = get_phone_type(phone_type)

            if raw_phone and len(raw_phone) <= 20:

                try:
                    unused_validated_phone = phonenumbers.parse(raw_phone, region='US')
                    output.append({'value': raw_phone, 'label': gt_phone_type})

                except UnicodeEncodeError:
                    logger.error('Issue parsing phonenumber: {}'.format(raw_phone))

    return output


@contract
def get_phone_type(bg_phone_type):
    """
    Provides a mapping between BurningGlass phone types to the the static values in the GT database.
    :param string | None bg_phone_type: BG phone type (if parsed from XML).
    :rtype: string
    """
    return {
        'cell': 'Mobile',
        'home': 'Home',
        'fax': 'Home Fax',
        'work': 'Work'
    }.get(bg_phone_type, 'Other')


@contract
def parse_candidate_experiences(bg_experience_xml_list):
    """
    Parses an experience list from a list of experience tags found in a BGXML response.
    :param bs4_ResultSet bg_experience_xml_list:
    :return: List of dicts containing experience data.
    :rtype: list(dict)
    """
    # TODO investigate is current not picking up current jobs.
    output = []
    for experiences in bg_experience_xml_list:
        jobs = experiences.findAll('job')
        for employement in jobs:
            start_month, start_year, end_month, end_year, start_datetime, end_datetime = (None,) * 6
            organization = _tag_text(employement, 'employer')
            # If it's 5 or less chars, keep the given capitalization, because it may be an acronym.
            # TODO revisit this logic. `Many XYZ Services` companies are becoming Xyz Services.
            if organization and len(organization) > 5:
                organization = string.capwords(organization)
            # Position title
            position_title = _tag_text(employement, 'title')
            # Start date
            start_date_str = get_date_from_date_tag(employement, 'start')

            if start_date_str:
                start_datetime = datetime.datetime.strptime(start_date_str, ISO8601_DATE_FORMAT)
                start_year = start_datetime.year
                start_month = start_datetime.month

            is_current_job = False
            # End date
            end_date_str = get_date_from_date_tag(employement, 'end')

            if end_date_str:
                end_datetime = datetime.datetime.strptime(end_date_str, ISO8601_DATE_FORMAT)
                end_month = end_datetime.month
                end_year = end_datetime.year

            # A Resume or BG may give us bad dates that get invalidated by Candidate Service.
            if (start_datetime and end_datetime) and (start_datetime > end_datetime):
                start_month, start_year, end_month, end_year = None, None, None, None

            try:
                today_date = datetime.date.today().isoformat()
                is_current_job = True if today_date == end_date_str else False
            except ValueError:
                pass
                # current_app.logger.error(
                #     "parse_xml: Received exception getting date for candidate end_date %s",
                #      end_date_str)
            # Company's address
            company_address = employement.find('address')
            company_city = _tag_text(company_address, 'city', capwords=True)
            company_state = _tag_text(company_address, 'state')
            company_country = get_country_code_from_address_tag(company_address)

            # Check if an experience already exists
            existing_experience_list_order = is_experience_already_exists(output,
                                                                          organization or '',
                                                                          position_title or '',
                                                                          start_month,
                                                                          start_year,
                                                                          end_month,
                                                                          end_year)
            # Get experience bullets
            candidate_experience_bullets = []
            description_text = _tag_text(employement, 'description', remove_questions=True) or ''
            for bullet_description in description_text.split('|'):
                # If experience already exists then append the current bullet-descriptions to
                # already existed bullet-descriptions
                if existing_experience_list_order:
                    existing_experience_description = output[existing_experience_list_order - 1][
                        'bullets']
                    existing_experience_description.append(dict(
                        description=bullet_description
                    ))
                else:
                    candidate_experience_bullets.append(dict(
                        description=bullet_description
                    ))
            if not existing_experience_list_order:
                output.append(dict(
                    position=position_title,
                    organization=organization,
                    city=company_city,
                    state=company_state,
                    country_code=company_country,
                    start_month=start_month,
                    start_year=start_year,
                    end_month=end_month,
                    end_year=end_year,
                    is_current=is_current_job,
                    bullets=candidate_experience_bullets
                ))
    return output


@contract
def parse_candidate_educations(bg_educations_xml_list):
    """
    Parses an education list from a list of education tags found in a BGXML response.
    :param bs4_ResultSet bg_educations_xml_list:
    :return: List of dicts containing education data.
    :rtype: list(dict)
    """
    edu_date_format = '%Y-%m-%d'
    start_month, start_year, end_month, end_year, start_dt, end_dt = None, None, None, None, None, None
    output = []
    for education in bg_educations_xml_list:
        for school in education.findAll('school'):
            school_name = _tag_text(school, 'institution')
            school_address = school.find('address')
            school_city = _tag_text(school_address, 'city', capwords=True)
            school_state = _tag_text(school_address, 'state')
            country = get_country_code_from_address_tag(school_address)

            start_date = get_date_from_date_tag(school, 'start')
            end_date = get_date_from_date_tag(school, 'end')
            completion_date = get_date_from_date_tag(school, 'completiondate')

            if completion_date:
                end_date = completion_date

            if start_date:
                start_dt = datetime.datetime.strptime(start_date, edu_date_format)
                start_month = start_dt.month
                start_year = start_dt.year

            if end_date:
                end_dt = datetime.datetime.strptime(end_date, edu_date_format)
                end_month = end_dt.month
                end_year = end_dt.year

            # A Resume or BG may give us bad dates that get invalidated by Candidate Service.
            if (start_dt and end_dt) and (start_dt > end_dt):
                start_month, start_year, end_month, end_year = None, None, None, None

            degree_tag = school.find('degree')
            degree_type = degree_tag.get('name') if degree_tag else None
            gpa_tag = school.find('gpa')
            gpa_value = float(gpa_tag.get('value')) if gpa_tag else None

            output.append(dict(
                school_name=school_name,
                city=school_city,
                state=school_state,
                country_code=country,
                degrees=[
                    {
                        'type': degree_type,
                        'title': _tag_text(school, 'degree'),
                        'start_year': start_year,
                        'start_month': start_month,
                        'end_year': end_year,
                        'end_month': end_month,
                        'gpa_num': gpa_value,
                        'bullets': [
                            {
                                'major': _tag_text(school, 'major'),
                                'comments': _tag_text(school, 'honors')
                            }
                        ]
                    }
                ],
            ))
    return output


@contract
def parse_candidate_skills(bg_skills_xml_list):
    """
    Parses a skill list from a list of skill tags found in a BGXML response.
    :param bs4_ResultSet bg_skills_xml_list:
    :return: List of dicts containing skill data.
    :rtype: list(dict)
    """
    skills_parsed = {}
    output = []

    for skill in bg_skills_xml_list:
        name = skill.get('name')
        skill_text = skill.text.strip()

        start_days = skill.get('start')
        end_days = skill.get('end')
        months_used = None
        last_used_date = None

        parsed_name = name or skill_text
        processed_skill = {'name': parsed_name, 'last_used_date': None, 'months_used': None}

        if start_days and end_days:
            """
            BurningGlass skill start and end dates come in the format of 6 digit whole numbers.
            Example:
                730000 through 730274

            This is assumed to be days since January 1st, 1
            Example: 730274 days since this date is 2000-06-04 and a tag with that number for the
                       end date will say '2000'
            """
            months_used = (int(end_days) - int(start_days)) / 30
            last_used_date = datetime.datetime(year=1, month=1, day=1) + datetime.timedelta(days=int(end_days))

        if last_used_date:
            processed_skill['last_used_date'] = last_used_date.strftime(ISO8601_DATE_FORMAT)

        if months_used and months_used > 0: # Rarely a skill will have an end before the start.
            processed_skill['months_used'] = int(months_used)

        if processed_skill['name'] not in skills_parsed:
            output.append(processed_skill)
            skills_parsed[processed_skill['name']] = True

    return output


@contract
def parse_candidate_addresses(bg_xml_list):
    """
    Parses an address list from a list of contact tags found in a BGXML response.
    :param bs4_ResultSet bg_xml_list:
    :return: List of dicts containing address data.
    :rtype: list(dict)
    """
    output = []
    for address in bg_xml_list:
        output.append({
            'address_line_1': _tag_text(address, 'street'),
            'city': address.get('inferred-city', '').title() or _tag_text(address, 'city'),
            'state': address.get('inferred-state', '').title() or _tag_text(address, 'state'),
            'country_code': get_country_code_from_address_tag(address),
            'zip_code': sanitize_zip_code(_tag_text(address, 'postalcode'))
        })
    return output


@contract
def parse_candidate_reference(xml_references_list):
    """
    :param bs4_ResultSet xml_references_list:
    :rtype: string | None
    """
    reference_comments = []
    comment_string = None
    for references in xml_references_list:
        reference_comments.append(references.text.strip())
    if reference_comments:
        comment_string = ' '.join(reference_comments)
    return comment_string


@contract
def parse_candidate_summary(xml_summary_tags):
    """
    :param bs4_ResultSet xml_summary_tags:
    :rtype: string | None
    """
    summary = ''
    for summary_tag in xml_summary_tags:
        summary += summary_tag.text.strip()

    return summary


###################################################################################################
# Utility functions.*
###################################################################################################

NEWLINES_REGEXP = re.compile(r"[\r\n]+")


def _tag_text(tag, child_tag_name, remove_questions=False, remove_extra_newlines=True,
              capwords=False):
    if not tag:
        return None
    if child_tag_name == 'description':
        parent_of_text = tag.findAll(child_tag_name) if child_tag_name else tag
    else:
        parent_of_text = tag.find(child_tag_name) if child_tag_name else tag
    if parent_of_text:
        text = None
        if child_tag_name != 'description' and parent_of_text.text:
            text = parent_of_text.string.strip()
        elif child_tag_name == 'description':
            text = ''
            for description in parent_of_text:
                text += description.string.strip() + "|"
            text = text[:-1]
        if text:
            if remove_questions:
                text = text.replace("?", "")
            if remove_extra_newlines:
                text = NEWLINES_REGEXP.sub(" ", text)
            if capwords:
                text = string.capwords(text)
            text = text.encode('utf-8')
            return bs4(text, 'lxml').text
    return None


def get_date_from_date_tag(parent_tag, date_tag_name):
    """Parses date value from bs4.soup"""
    date_tag = parent_tag.find(date_tag_name) or {}
    return date_tag.get('iso8601')


def is_experience_already_exists(candidate_experiences, organization, position_title, start_month,
                                 start_year, end_month, end_year):
    """Logic for checking an experience has been parsed twice due to BG error"""
    for i, experience in enumerate(candidate_experiences):
        if (experience['organization'] or '') == organization and \
           (experience['position'] or '') == position_title and \
           (experience['start_month'] == start_month and
            experience['start_year'] == start_year and
            experience['end_month'] == end_month and
            experience['end_year'] == end_year):

            return i + 1
    return False


def scrub_candidate_name(name_unicode):
    """
    Takes a string and formats it to gT candidate spec. Names should have no punctuation, be at most
    35 characters, and be in the 'string.title()' format.

    This uses StackOverflow Answer:
    http://stackoverflow.com/questions/11066400/
    which is reinforced here:
    http://stackoverflow.com/questions/20529449/

    String version located:
    http://stackoverflow.com/questions/265960/

    :param unicode name_unicode:
    :return unicode:
    """

    translate_table = dict.fromkeys(i for i in xrange(sys.maxunicode)
                                    if unicodedata.category(unichr(i)).startswith('P'))

    name_unicode = name_unicode[:35]
    name_unicode = name_unicode.translate(translate_table)
    name_unicode = name_unicode.title()

    return name_unicode


def get_country_code_from_address_tag(address):
    """
    Gets a country code from an address tag.
    """
    if address:
        country_tag = address.find('country')

        if country_tag and country_tag.get('iso3'):
            company_country_i3 = pycountry.countries.get(alpha3=country_tag.get('iso3'))
            return company_country_i3.alpha2

    return None
