# Standared Library
from collections import defaultdict
import json
# Third Party
from dateutil.parser import parse
import requests
from OauthClient import OAuthClient

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
      'Accept': 'application/json',
      'content-type': 'application/json',
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

def parse_optic_json(resume_json):
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

def parse_candidate_name(contact_list):
    formatted_name = 'Unknown'
    if type(contact_list) is not type(list()):
        contact_list = [contact_list]
    for item in contact_list:
        name_dict = item.get('name')
        if name_dict:
            # Middle initials create a list in format ['First Name', 'X']
            givenname = item['name']['givenname']
            if type(givenname) == type(list()):
                first_name = givenname[0]
            else:
                first_name = givenname
            last_name = item['name']['surname']
            formatted_name = first_name
            if last_name:
                formatted_name = '{} {}'.format(first_name, last_name)
            return formatted_name
    return formatted_name


def parse_candidate_emails(contact_list):
    raw_emails, output = [], []
    if type(contact_list) is not type(list()):
        contact_list = [contact_list]
    for item in contact_list:
        # The email key returns either list or string if present.
        emails = item.get('email')
        #use continue keyword instead of double check for emails.
        if emails and type(emails) is type(list()):
            raw_emails.extend(emails)
        # No type checking here. It is currently unicode but may change to string.
        elif emails and (type(emails) is type(unicode()) or type(emails) is type(str())):
            raw_emails.extend([emails])
    for i, email in enumerate(raw_emails):
        if i == 0:
            output.append({'address': email, 'label': 'Primary'})
        else:
            output.append({'address': email, 'label': 'Other'})
    return output


def parse_candidate_phones(contact_list):
    output = []
    if type(contact_list) is not type(list()):
        contact_list = [contact_list]
    for item in contact_list:
        # The email key returns either list or string if present.
        phones = item.get('phone')
        if phones:
            continue
        if type(phones) is not type(list()):
            phones = [phones]
        for p in phones:
            if type(p) is type(dict()):
                output.append({'value': p['#text']})
            # Some phone numbers do not get the area code parsed out properly and may just be a
            # string.
            if type(p) is type(str()) or type(p) is type(unicode()):
                output.append({'value': p})
    return output


def parse_candidate_experience(experience_json):
    return experience_json


def parse_candidate_educations(education_json):
    educations = []
    schools = education_json.get('school')
    if type(schools) is not type(list()):
        schools = [schools]
    for s in schools:
        # This creates a dict that will create keys if needed for nesting.
        education = defaultdict(lambda: defaultdict(int))
        institution_value = s.get('institution')
        # Hacky hack due to some education entries containing multiple institutions.
        if type(institution_value) is not type(list()):
            institution_value = [institution_value]
        education['school_name'] = institution_value[0]
        # Address processing.
        address_value = s.get('address')
        # Hacky hack due to some address entries containing multiple institutions.
        if type(address_value) is not type(list()):
            address_value = [address_value]
        address = address_value[0]
        education['city'] = address.get('city', {}).get('#text')
        education['state'] = address.get('state', {}).get('#text')
        education['country'] = "US, United States"
        # Degree processing.
        if 'degree' in s:
            degree = {}
            degree['type'] = s.get('degree', {}).get('#text')
            degree['title'] = s.get('major', {}).get('#text')
            degree['degree_bullets'] = []
            education['degrees'] = degree
        educations.append(education)
    return educations


def parse_candidate_skills():
    return []


def parse_candidate_addresses(contact_json):
    return [contact_json['address']]