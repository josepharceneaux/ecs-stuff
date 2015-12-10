# Standared Library
from collections import defaultdict
import string
import re
# Third Party
from dateutil.parser import parse
from bs4 import BeautifulSoup as bs4
import requests
from OauthClient import OAuthClient

# def fetch_optic_response(resume):
#     URL = 'http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume'
#     oauth = OAuthClient(url='http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume',
#                         method='POST', consumerKey='osman',
#                         consumerSecret='aRFKEc3AJdR9zogE@M9Sis%QjZPxA5Oy',
#                         token='Utility',
#                         tokenSecret='Q5JuWpaMLUi=yveieiNKNWxqqOvHLNJ$',
#                         signatureMethod='HMAC-SHA1',
#                         oauthVersion='1.0')
#     AUTH = oauth.get_authorizationString()
#     HEADERS = {
#       'Accept': 'application/json',
#       'content-type': 'application/json',
#       'Authorization': AUTH,
#     }
#     DATA = {
#         'binaryData': resume,
#         'instanceType': 'TM',
#         'locale': 'en_us'
#     }
#     r = requests.post(URL, headers=HEADERS, json=DATA)
#     optic_response = json.loads(r.content)['responseData']['ResDoc']
#     return optic_response

# def parse_optic_json(resume_xml):
#     name = parse_candidate_name(resume_json['resume']['contact'])
#     emails = parse_candidate_emails(resume_json['resume']['contact'])
#     phones = parse_candidate_phones(resume_json['resume']['contact'])
#     work_experiences = parse_candidate_experience(resume_json['resume']['experience']['job'])
#     if resume_json['resume'].get('education'):
#         educations = parse_candidate_educations(resume_json['resume']['education'])
#     else:
#         educations = []
#     skills = parse_candidate_skills()
#     addresses = parse_candidate_addresses(resume_json['resume']['contact'][0])
#     candidate = dict(
#         full_name=name,
#         emails=emails,
#         phones=phones, # list
#         work_experiences=work_experiences, # list
#         educations=educations, # list
#         skills=skills, # list
#         addresses=addresses # list
#     )
#     return candidate


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