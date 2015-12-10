# Standared Library
import datetime
import re
import string
# Third Party
from bs4 import BeautifulSoup as bs4
# from dateutil.parser import parse
# from OauthClient import OAuthClient
import phonenumbers
import requests

def fetch_optic_response(resume):
    URL = 'http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume'
    oauth = OAuthClient(url='http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume',
                        method='POST', consumerKey='osman',
                        consumerSecret='aRFKEc3AJdR9zogE@M9Sis%QjZPxA5Oy',
                        token='Utility',
                        tokenSecret='Q5JuWpaMLUi=yveieiNKNWxqqOvHLNJ$',
                        signatureMethod='HMAC-SHA1',
                        oauthVersion='1.0')
    AUTH = oauth.get_authorizationString()
    HEADERS = {
      'Accept': 'application/xml',
      'content-type': 'application/xml',
      'Authorization': AUTH,
    }
    DATA = {
        'binaryData': resume,
        'instanceType': 'TM',
        'locale': 'en_us'
    }
    r = requests.post(URL, headers=HEADERS, json=DATA)
    optic_response = json.loads(r.content)['responseData']['ResDoc']
    return optic_response

def parse_optic_json(resume_xml):
    name = parse_candidate_name(resume_json['resume']['contact'])
    emails = parse_candidate_emails(resume_json['resume']['contact'])
    phones = parse_candidate_phones(resume_json['resume']['contact'])
    work_experiences = parse_candidate_experience(resume_json['resume']['experience']['job'])
    if resume_json['resume'].get('education'):
        educations = parse_candidate_educations(resume_json['resume']['education'])
    else:
        educations = []
    skills = parse_candidate_skills()
    addresses = parse_candidate_addresses(resume_json['resume']['contact'][0])
    candidate = dict(
        full_name=name,
        emails=emails,
        phones=phones, # list
        work_experiences=work_experiences, # list
        educations=educations, # list
        skills=skills, # list
        addresses=addresses # list
    )
    return candidate


def parse_candidate_name(bs_contact_xml_list):
    """
    Parses a name from a list of contact tags found in a BGXML response
    :param bs_contact_xml_list: bs4.element.Tag
    :return: string: formatted name string using title()
    """
    givenname = None
    surname = None
    for contact in bs_contact_xml_list:
        # If a name is already parsed we do not want to reassign it. This is to protect against
        # multiple parsed givennames/surnames
        if not givenname:
            givenname = _tag_text(contact, 'givenname')
        if not surname:
            surname = _tag_text(contact, 'surname')
    first_name = givenname.title() if givenname else 'Unknown'
    last_name = surname.title() if givenname else 'Unknown'
    return {'first_name': first_name, 'last_name': last_name}


def parse_candidate_emails(bs_contact_xml_list):
    output = []
    for contact in bs_contact_xml_list:
        emails = contact.findAll('email')
        for e in emails:
            email = e.text.strip()
            output.append({'address': email})
    return output


def parse_candidate_phones(bs_contact_xml_list):
    output = []
    for contact in bs_contact_xml_list:
        phones = contact.findAll('phone')
        #TODO: look into adding a type using p.attrs['type']
        for p in phones:
            raw_phone = p.text.strip()
            formatted_phone = canonicalize_phonenumber(raw_phone)
            if formatted_phone:
                output.append({'value': formatted_phone})
    return output


def parse_candidate_experiences(bs_experience_xml_list):
    # for experiences in rawxml.findAll('experience'):
    output = []
    for experiences in bs_experience_xml_list:
        jobs = experiences.findAll('job')
        for employement_index, employement in enumerate(jobs):

            organization = _tag_text(employement, 'employer')
            # If it's 5 or less letters, keep the given capitalization, because it may be an acronym.
            if organization and len(organization) > 5:
                organization = string.capwords(organization)

            # Position title
            position_title = _tag_text(employement, 'title')

            # Start date
            experience_start_date = get_date_from_date_tag(employement, 'start')

            is_current_job = 0

            # End date
            experience_end_date = get_date_from_date_tag(employement, 'end')

            try:
                today_date = datetime.date.today().isoformat()
                is_current_job = 1 if today_date == experience_end_date else 0
            except ValueError:
                pass
                # current_app.logger.error("parse_xml: Received exception getting date for candidate end_date %s",
                #                          experience_end_date)

            # Company's address
            company_address = employement.find('address')
            company_city = _tag_text(company_address, 'city', capwords=True)
            # company_state = _tag_text(company_address, 'state')
            company_country = 'United States'

            # Check if an experience already exists
            existing_experience_list_order = is_experience_already_exists(output, organization or '',
                                                                          position_title or '',
                                                                          experience_start_date,
                                                                          experience_end_date)

            # Get experience bullets
            candidate_experience_bullets = []
            description_text = _tag_text(employement, 'description', remove_questions=True) or ''
            for i, bullet_description in enumerate(description_text.split('|')):
                # If experience already exists then append the current bullet-descriptions to already existed
                # bullet-descriptions
                if existing_experience_list_order:
                    existing_experience_description = output[existing_experience_list_order - 1][
                        'candidate_experience_bullet']
                    existing_experience_description.append(dict(
                        listOrder=len(existing_experience_description) + 1,
                        description=bullet_description + '\n'
                    ))
                else:
                    candidate_experience_bullets.append(dict(
                        text=bullet_description
                    ))

            if not existing_experience_list_order:
                output.append(dict(
                    city=company_city,
                    end_date=experience_end_date,
                    country=company_country,
                    company=organization,
                    role=position_title,
                    is_current=is_current_job,
                    start_date=experience_start_date,
                    work_experience_bullets=candidate_experience_bullets
                ))
    return output

###################################################################################################
# Utility functions.*
###################################################################################################

_newlines_regexp = re.compile(r"[\r\n]+")


def _tag_text(tag, child_tag_name, remove_questions=False, remove_extra_newlines=True, capwords=False):
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


def canonicalize_phonenumber(phonenumber):
    try:
        parsed_phonenumbers = phonenumbers.parse(str(phonenumber), region="US")
        if phonenumbers.is_valid_number_for_region(parsed_phonenumbers, 'US'):
            # Phonenumber format is : +1 (123) 456-7899
            return '+1 ' + phonenumbers.format_number(parsed_phonenumbers, phonenumbers.PhoneNumberFormat.NATIONAL)
        else:
            # current_app.logger.error(
            #     'canonicalize_phonenumber: [{}] is an invalid or non-US Phone Number'.format(phonenumber))
            return False
    except phonenumbers.NumberParseException:
        return False
    except:
        return False


# date_tag has child tag that could be one of: current, YYYY-MM, notKnown, YYYY, YYYY-MM-DD, or notApplicable (i think)
def get_date_from_date_tag(parent_tag, date_tag_name):
    date_tag = parent_tag.find(date_tag_name)
    if date_tag:
        try:
            if date_tag_name == 'end' and ('current' in date_tag.text.lower() or 'present' in date_tag.text.lower()):
                return datetime.date.isoformat()
            return date_tag['iso8601']
        except:
            return None
    return None


def is_experience_already_exists(candidate_experiences, organization, position_title, start_date, end_date):
    for i, experience in enumerate(candidate_experiences):
        if (experience['company'] or '') == organization and (experience['role'] or '') == position_title and (
                        experience['start_date'] == start_date and experience['end_date'] == end_date):
            return i + 1
    return False