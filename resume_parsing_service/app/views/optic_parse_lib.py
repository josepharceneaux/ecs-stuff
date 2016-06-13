"""Parsing functions for extracting specific information from Burning Glass API responses."""
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
import requests
import phonenumbers
# Module Specific
from flask import current_app
from resume_parsing_service.app import logger
from resume_parsing_service.app.views.OauthClient import OAuthClient
from resume_parsing_service.common.error_handling import ForbiddenError, InternalServerError
from resume_parsing_service.common.utils.validators import sanitize_zip_code

ISO8601_DATE_FORMAT = "%Y-%m-%d"


def fetch_optic_response(resume, filename_str):
    """
    Takes in an encoded resume file and returns a bs4 'soup-able' format
    (utf-decode and html escape).
    :param str resume: a base64 encoded resume file.
    :return: str unescaped: an html unquoted, utf-decoded string that represents the Burning Glass
                            XML.
    """
    start_time = time()
    BG_URL = current_app.config['BG_URL']
    oauth = OAuthClient(url=BG_URL,
                        method='POST', consumerKey='osman',
                        consumerSecret='aRFKEc3AJdR9zogE@M9Sis%QjZPxA5Oy',
                        token='Utility',
                        tokenSecret='Q5JuWpaMLUi=yveieiNKNWxqqOvHLNJ$',
                        signatureMethod='HMAC-SHA1',
                        oauthVersion='1.0')
    AUTH = oauth.get_authorizationString()
    HEADERS = {
        'accept': 'application/xml',
        'content-type': 'application/json',
        'Authorization': AUTH,
    }
    DATA = {
        'binaryData': resume,
        'instanceType': 'TM',
        'locale': 'en_us'
    }
    r = requests.post(BG_URL, headers=HEADERS, json=DATA)

    if r.status_code != requests.codes.ok:
        # Since this error is displayed to the user we may want to obfuscate it a bit and log more
        # developer friendly messages. "Error processing this resume. The development team has been
        # notified of this issue" type of message.
        raise ForbiddenError('Error connecting to BG instance.')

    try:
        html_parser = HTMLParser.HTMLParser()
        unquoted = urllib2.unquote(r.content).decode('utf8')
        unescaped = html_parser.unescape(unquoted)

    except Exception:
        logger.exception('Error translating BG response.')
        raise InternalServerError('Error decoding parsed resume text.')

    logger.info(
        "Benchmark: fetch_optic_response({}) took {}s".format(filename_str,
                                                              time() - start_time)
    )
    return unescaped


def parse_optic_xml(resume_xml_unicode):
    """
    Takes in a Burning Glass XML tree in string format and returns a candidate JSON object.
    :param str resume_xml_unicode: An XML tree represented in unicode format. It is a slightly
                                  processed response from the Burning Glass API.
    :return dict candidate: Results of various parsing functions on the input xml string.
    """
    contact_xml_list = bs4(resume_xml_unicode, 'lxml').findAll('contact')
    experience_xml_list = bs4(resume_xml_unicode, 'lxml').findAll('experience')
    educations_xml_list = bs4(resume_xml_unicode, 'lxml').findAll('education')
    skill_xml_list = bs4(resume_xml_unicode, 'lxml').findAll('canonskill')
    references_xml = bs4(resume_xml_unicode, 'lxml').findAll('references')
    name = parse_candidate_name(contact_xml_list)
    emails = parse_candidate_emails(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    work_experiences = parse_candidate_experiences(experience_xml_list)
    educations = parse_candidate_educations(educations_xml_list)
    skills = parse_candidate_skills(skill_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    references = parse_candidate_reference(references_xml)
    candidate = dict(
        first_name=name['first_name'],
        last_name=name['last_name'],
        emails=emails,
        phones=phones,
        work_experiences=work_experiences,
        educations=educations,
        skills=skills,
        addresses=addresses,
        talent_pool_ids={'add': None},
        references=references
    )
    return candidate


def parse_candidate_name(bs_contact_xml_list):
    """
    Parses a name from a list of contact tags found in a BGXML response.
    :param bs4.element.Tag bs_contact_xml_list:
    :return dict: Formatted name strings using title() in a dictionary.
    """

    givenname = None
    surname = None

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

    first_name = givenname or 'Unknown'
    last_name = surname or 'Unknown'

    return {'first_name': first_name, 'last_name': last_name}


def parse_candidate_emails(bs_contact_xml_list):
    """
    Parses an email list from a list of contact tags found in a BGXML response.
    :param bs4.element.Tag bs_contact_xml_list:
    :return list output: List of dicts containing email data.
    """
    output = []
    for contact in bs_contact_xml_list:
        emails = contact.findAll('email')
        for e in emails:
            email = e.text.strip()
            output.append({'address': email})
    return output


def parse_candidate_phones(bs_contact_xml_list):
    """
    Parses a phone list from a list of contact tags found in a BGXML response.
    :param bs4.element.Tag bs_contact_xml_list:
    :return list output: List of dicts containing phone data.
    """
    output = []

    for contact in bs_contact_xml_list:
        phones = contact.findAll('phone')

        for p in phones:
            # TODO: look into adding a type using p.attrs['type']
            raw_phone = p.text.strip()

            # JSON_SCHEMA for candidates phone is max:20
            # This fixes issues with numbers like '1-123-45            67'
            if raw_phone and len(raw_phone) > 20:
                raw_phone = " ".join(raw_phone.split())

            if raw_phone and len(raw_phone) <= 20:

                try:
                    unused_validated_phone = phonenumbers.parse(raw_phone, region='US')
                    output.append({'value': raw_phone})

                except UnicodeEncodeError:
                    logger.error('Issue parsing phonenumber: {}'.format(raw_phone))

    return output


def parse_candidate_experiences(bg_experience_xml_list):
    """
    Parses an experience list from a list of experience tags found in a BGXML response.
    :param bs4.element.Tag bg_experience_xml_list:
    :return list output: List of dicts containing experience data.
    """
    # TODO investigate is current not picking up current jobs.
    output = []
    for experiences in bg_experience_xml_list:
        jobs = experiences.findAll('job')
        for employement in jobs:
            organization = _tag_text(employement, 'employer')
            # If it's 5 or less chars, keep the given capitalization, because it may be an acronym.
            # TODO revisit this logic. `Many XYZ Services` companies are becoming Xyz Services.
            if organization and len(organization) > 5:
                organization = string.capwords(organization)
            # Position title
            position_title = _tag_text(employement, 'title')
            # Start date
            start_date_str = get_date_from_date_tag(employement, 'start')
            start_month, start_year = None, None
            if start_date_str:
                start_datetime = datetime.datetime.strptime(start_date_str, ISO8601_DATE_FORMAT)
                start_year = start_datetime.year
                start_month = start_datetime.month

            is_current_job = False
            # End date
            end_date_str = get_date_from_date_tag(employement, 'end')
            end_month, end_year = None, None
            if end_date_str:
                end_datetime = datetime.datetime.strptime(end_date_str, ISO8601_DATE_FORMAT)
                end_month = end_datetime.month
                end_year = end_datetime.year

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
            company_country = 'United States'
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
                    bullets=candidate_experience_bullets,
                    city=company_city,
                    country=company_country,
                    end_month=end_month,
                    end_year=end_year,
                    is_current=is_current_job,
                    organization=organization,
                    position=position_title,
                    start_month=start_month,
                    start_year=start_year,
                    state=company_state,
                ))
    return output


def parse_candidate_educations(bg_educations_xml_list):
    """
    Parses an education list from a list of education tags found in a BGXML response.
    :param bs4.element.Tag bg_educations_xml_list:
    :return list output: List of dicts containing education data.
    """
    output = []
    for education in bg_educations_xml_list:
        for school in education.findAll('school'):
            school_name = _tag_text(school, 'institution')
            school_address = school.find('address')
            school_city = _tag_text(school_address, 'city', capwords=True)
            school_state = _tag_text(school_address, 'state')
            country = 'United States'

            # education_start_date = get_date_from_date_tag(school, 'start')
            # education_end_date = None
            # end_date = get_date_from_date_tag(school, 'end')
            # completion_date = get_date_from_date_tag(school, 'completiondate')
            #
            # if completion_date:
            #     education_end_date = completion_date
            # elif end_date:
            #     education_end_date = end_date

            # GPA data no longer used in educations dict.
            # Save for later or elimate this and gpa_num_and_denom?
            # gpa_num, gpa_denom = gpa_num_and_denom(school, 'gpa')
            output.append(dict(
                school_name=school_name,
                city=school_city,
                state=school_state,
                country=country,
                degrees=[
                    {
                        'type': _tag_text(school, 'degree'),
                        'title': _tag_text(school, 'major'),
                        'bullets': []
                    }
                ],
            ))
    return output


def parse_candidate_skills(bg_skills_xml_list):
    """
    Parses a skill list from a list of skill tags found in a BGXML response.
    :param bs4.element.Tag bg_skills_xml_list:
    :return list output: List of dicts containing skill data.
    """
    skills_parsed = {}
    output = []

    for skill in bg_skills_xml_list:
        name = skill.get('name')
        skill_text = skill.text.strip()
        start_days = skill.get('start')
        end_days = skill.get('end')
        months_used = None
        parsed_name = name or skill_text
        processed_skill = {'name': parsed_name}

        if start_days and end_days:
            months_used = (int(end_days) - int(start_days)) / 30

        if months_used:
            processed_skill['months_used'] = int(months_used)

        if processed_skill['name'] not in skills_parsed:
            output.append(processed_skill)
            skills_parsed[processed_skill['name']] = True

    return output


def parse_candidate_addresses(bg_xml_list):
    """
    Parses an address list from a list of contact tags found in a BGXML response.
    :param bs4.element.Tag bg_xml_list:
    :return list output: List of dicts containing address data.
    """
    output = []
    for address in bg_xml_list:
        output.append({
            'address_line_1': _tag_text(address, 'street'),
            'city': address.get('inferred-city', '').title() or _tag_text(address, 'city'),
            'state': address.get('inferred-state', '').title() or _tag_text(address, 'state'),
            'country': address.get('inferred-country', '').title() or 'US',
            'zip_code': sanitize_zip_code(_tag_text(address, 'postalcode'))
        })
    return output


def parse_candidate_reference(xml_references_list):
    """
    :param bs4.element.Tag xml_references_list:
    :return: str | None
    """
    reference_comments = []
    comment_string = None
    for references in xml_references_list:
        reference_comments.append(references.text.strip())
    if reference_comments:
        comment_string = ' '.join(reference_comments)
    return comment_string


###################################################################################################
# Utility functions.*
###################################################################################################

_newlines_regexp = re.compile(r"[\r\n]+")


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
                text = _newlines_regexp.sub(" ", text)
            if capwords:
                text = string.capwords(text)
            text = text.encode('utf-8')
            return bs4(text, 'lxml').text
    return None


# date_tag has child tag that could be one of: current, YYYY-MM, notKnown, YYYY, YYYY-MM-DD, or
# notApplicable (I think)
def get_date_from_date_tag(parent_tag, date_tag_name):
    """Parses date value from bs4.soup"""
    date_tag = parent_tag.find(date_tag_name)
    if date_tag:
        try:
            if date_tag_name == 'end' and ('current' in date_tag.text.lower() or
                                           'present' in date_tag.text.lower()):
                return datetime.date.isoformat()
            return date_tag['iso8601']
        except Exception:
            return None
    return None


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
