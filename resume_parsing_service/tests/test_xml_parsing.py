# -*- coding: utf-8 -*-
"""Unit tests for formatting and accuracy for offline testing."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position
from base64 import b64encode
# Third party.
from bs4 import BeautifulSoup as bs4
from jsonschema import validate, FormatChecker
# JSON outputs.
from .resume_xml import DOCX
from .resume_xml import DUPED_EXPERIENCE
from .resume_xml import GET_1301
from .resume_xml import GET_626a
from .resume_xml import GET_626b
from .resume_xml import GET_642
from .resume_xml import GET_646
from .resume_xml import PDF
from .resume_xml import PDF_13
from .resume_xml import PDF_14
from .resume_xml import SQUARE_BULLETS
from .resume_xml import REFERENCE_XML
# Modules being tested.
from resume_parsing_service.app import app
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_addresses
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_educations
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_emails
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_experiences
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_name
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_phones
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_skills
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_reference
from resume_parsing_service.app.views.optic_parse_lib import is_experience_already_exists
from resume_parsing_service.app.views.optic_parse_lib import trunc_text
from resume_parsing_service.app.views.utils import extra_skills_parsing
# JSON Schemas
from json_schemas import (EMAIL_SCHEMA, PHONE_SCHEMA, EXPERIENCE_SCHEMA, EDU_SCHEMA,\
                          SKILL_SCHEMA, ADDRESS_SCHEMA)
# XML Combinations:
import edu_combinations
import contact_combinations
import job_combinations
import skill_combinations


DOCX_ADDRESS = {'city': u'Lansdale', 'state': u'Pennsylvania', 'country_code': None, 'zip_code': '19446',
                'address_line_1': u'466 Tailor Way'}
GET_642_ADDRESS = {'city': u'Liberty Township', 'state': u'OH', 'country_code': None,
                   'zip_code': '45011', 'address_line_1': u'6507 Hughes Ridge Lane'}
GET_646_ADDRESS = {'city': u'Solana Beach', 'state': u'CA', 'country_code': None, 'zip_code': '92075',
                  'address_line_1': u'930 Via Di Salerno Unit 119'}
GET_626a_ADDRESS = {'city': u'Portland', 'state': u'Oregon', 'country_code': None, 'zip_code': '97211',
                    'address_line_1': u'1602 NE Junior St.'}
GET_626b_ADDRESS = {'city': u'Portland', 'state': u'OR', 'country_code': None, 'zip_code': '97212',
                    'address_line_1': u'4014 NE Failing Street'}
PDF_ADDRESS = {'city': u'St. Petersburg', 'state': u'FL', 'country_code': None, 'zip_code': '33713-5855',
               'address_line_1': u'2462 13 th Avenue North #6-101'}

XML_MAPS = [
    # The resume below has 6 experience but BG incorrectly returns 7.
    # The resume below has 1 address but BG incorrectly returns 2.
    {'tree_name': DOCX, 'name': 'Veena Nithoo', 'email_len': 0, 'phone_len': 1, 'education_len': 1,
     'experience_len': 7, 'skills_len': 47, 'addresses_len': 2},
    # The resume below has 12 experience but BG incorrectly returns 13.
    # The resume below has 1 address but BG incorrectly returns 2.
    {'tree_name': GET_642, 'name': 'Bobby Breland', 'email_len': 1, 'phone_len': 2,
     'education_len': 1, 'experience_len': 13, 'skills_len': 71, 'addresses_len': 2},
    # The resume below has 2 addresses but BG incorrectly returns 1.
    {'tree_name': GET_646, 'name': 'Patrick Kaldawy', 'email_len': 3, 'phone_len': 6,
     'education_len': 2, 'experience_len': 4, 'skills_len': 35, 'addresses_len': 1},
    {'tree_name': PDF, 'name': 'Mark Greene', 'email_len': 1, 'phone_len': 1, 'education_len': 1,
     'experience_len': 11, 'skills_len': 17, 'addresses_len': 1},
    {'tree_name': PDF_13, 'name': 'Bruce Parkey', 'email_len': 1, 'phone_len': 1,
     'education_len': 1, 'experience_len': 3, 'skills_len': 24, 'addresses_len': 1},
    # This PDF currently does not get its email/phone parsed out of the footer.
    # This PDF currently parses out the wrong education count.
    {'tree_name': PDF_14, 'name': 'Jose Chavez', 'email_len': 0, 'phone_len': 0, 'education_len': 2,
     'experience_len': 4, 'skills_len': 32, 'addresses_len': 1}
]


def test_name_parsing():
    """Basic name parsing test."""
    for xml in XML_MAPS:
        resume = xml['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        if contact_xml_list:
            first, last = parse_candidate_name(contact_xml_list)
            assert first == xml['name'].split()[0]
            assert last == xml['name'].split()[1]


def test_email_parsing():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the 'address' key (only needed key for candidate creation).
    """
    for xml in XML_MAPS:
        resume = xml['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        emails = parse_candidate_emails(contact_xml_list)
        assert len(emails) == xml['email_len']
        for email in emails:
            assert validate(email, EMAIL_SCHEMA, format_checker=FormatChecker()) is None


def test_phone_parsing():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the 'value' key.
    """
    for xml in XML_MAPS:
        resume = xml['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        phones = parse_candidate_phones(contact_xml_list)
        assert len(phones) == xml['phone_len']
        for phone in phones:
            assert validate(phone, PHONE_SCHEMA, format_checker=FormatChecker()) is None


def test_experience_parsing():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the correct keys.
    """
    for xml in XML_MAPS:
        resume = xml['tree_name']
        experience_xml_list = bs4(resume, 'lxml').findAll('experience')
        experiences = parse_candidate_experiences(experience_xml_list)
        assert len(experiences) == xml['experience_len']
        for experience in experiences:
            assert validate(experience, EXPERIENCE_SCHEMA, format_checker=FormatChecker()) is None
    # Tests against specific KeyError reported in JIRA (GET-626)
    xml_experiences_a = bs4(GET_626a, 'lxml').findAll('experience')
    processed_experiences_a = parse_candidate_experiences(xml_experiences_a)
    xml_experiences_b = bs4(GET_626b, 'lxml').findAll('experience')
    processed_experiences_b = parse_candidate_experiences(xml_experiences_b)
    for experience in processed_experiences_a:
        assert validate(experience, EXPERIENCE_SCHEMA, format_checker=FormatChecker()) is None
    for experience in processed_experiences_b:
        assert validate(experience, EXPERIENCE_SCHEMA, format_checker=FormatChecker()) is None


def test_dupe_experience_bullets():
    experience_xml_list = bs4(DUPED_EXPERIENCE, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1


def test_experience_exists_detects_dupe():
    exp1 = {
        'organization': 'Starbucks',
        'position': 'Coffee Master',
        'start_month': 6,
        'start_year': 2005,
        'end_month': 8,
        'end_year': 2012
    }
    exp2 = {
        'organization': 'Aeria Games',
        'position': 'Asst. Product Manager',
        'start_month': 8,
        'start_year': 2012,
        'end_month': 6,
        'end_year': 2013
    }
    exp3 = {
        'organization': 'Astreya Partners',
        'position': 'Jr. Python Developer',
        'start_month': 7,
        'start_year': 2013,
        'end_month': 6,
        'end_year': 2015
    }
    experiences = [exp1, exp2]
    assert is_experience_already_exists(experiences, exp2)
    assert is_experience_already_exists(experiences, exp3) is False


def test_experience_exists_concats():
    exp1 = {
        'organization': 'Starbucks',
        'position': 'Coffee Master',
        'start_month': 6,
        'start_year': 2005,
        'end_month': 8,
        'end_year': 2012,
        'bullets': ['Made a whole bunch of coffee']
    }
    exp2 = {
        'organization': 'Starbucks',
        'position': 'Coffee Master',
        'start_month': 6,
        'start_year': 2005,
        'end_month': 8,
        'end_year': 2012,
        'bullets': ['Made a whole bunch of frappaccinos']
    }

    experiences = [exp1]
    list_order = is_experience_already_exists(experiences, exp2)
    assert list_order is 0  # http://stackoverflow.com/a/306353


def test_education_parsing():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the correct education keys.
    """
    for xml in XML_MAPS:
        resume = xml['tree_name']
        educations_xml_list = bs4(resume, 'lxml').findAll('education')
        educations = parse_candidate_educations(educations_xml_list)
        # Verify Expected Length
        assert len(educations) == xml['education_len']
        # Very each dict in list has proper keys
        for education in educations:
            assert validate(education, EDU_SCHEMA, format_checker=FormatChecker()) is None


def test_skill_parsing():
    """Tests skills are parsed and formatted properly."""
    for xml in XML_MAPS:
        resume = xml['tree_name']
        skill_xml_list = bs4(resume, 'lxml').findAll('canonskill')
        skills = parse_candidate_skills(skill_xml_list)
        assert len(skills) == xml['skills_len']
        for skill in skills:
            assert validate(skill, SKILL_SCHEMA) is None


def test_skills_duplicates():
    soup = bs4(GET_1301, 'lxml')
    skill_xml_list = soup.findAll('canonskill')
    skills = parse_candidate_skills(skill_xml_list)
    skills_set = set()
    for skill in skills:
        skills_set.add(skill['name'])
    assert len(skills) == len(skills_set)


def test_extra_skill_parsing():
    for resume_xml in (DOCX, DUPED_EXPERIENCE, GET_1301, GET_626a, GET_626b, GET_642, GET_646, PDF,
                       PDF_13, PDF_14):
        encoded_soup_text = b64encode(bs4(resume_xml, 'lxml').getText().encode('utf8', 'replace'))
        with app.app_context():
            extra_skills = extra_skills_parsing(encoded_soup_text)
            assert(extra_skills)


def test_address_parsing():
    """Tests addresses are parsed and formatted properly"""
    for xml in XML_MAPS:
        resume = xml['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        addresses = parse_candidate_addresses(contact_xml_list)
        assert len(addresses) == xml['addresses_len']
        for address in addresses:
            assert validate(address, ADDRESS_SCHEMA, format_checker=FormatChecker()) is None


def test_docx_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(DOCX, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert DOCX_ADDRESS in addresses
    assert first == 'Veena'
    assert last == 'Nithoo'
    assert {'value': u'+12154120817', 'label': 'Other'} in phones
    # Experience parsing.
    experience_xml_list = bs4(DOCX, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    exp1 = next((org for org in experiences if org["organization"] == u'Merck & Co, Inc'), None)
    exp2 = next((org for org in experiences if org["organization"] == u'Infomc Inc'), None)
    exp3 = next((org for org in experiences if org["organization"] == u'Datakinetics Inc'), None)
    exp4 = next((org for org in experiences if org["organization"] == u'Harel Mallac, Mcs Development Ltd'), None)
    exp5 = next((org for org in experiences if org["organization"] == u'Gt Management Ltd'), None)
    assert None not in [exp1, exp2, exp3, exp4, exp5]
    assert exp1['start_month'] == 10
    assert exp1['start_year'] == 2000
    assert exp1['position'] == u'Application Services Analyst'
    assert exp2['start_month'] == 9
    assert exp2['start_year'] == 1999
    assert exp2['end_month'] == 6
    assert exp2['end_year'] == 2000
    assert exp2['position'] == u'Analyst Programmer'
    assert exp3['start_month'] == 1
    assert exp3['start_year'] == 1998
    assert exp3['end_month'] == 8
    assert exp3['end_year'] == 1999
    assert exp3['position'] == u'Analyst Programmer'
    assert exp4['start_month'] == 3
    assert exp4['start_year'] == 1996
    assert exp4['end_month'] == 5
    assert exp4['end_year'] == 1997
    assert exp4['position'] == u'Analyst Programmer'
    assert exp5['start_month'] == 9
    assert exp5['start_year'] == 1993
    assert exp5['end_month'] == 9
    assert exp5['end_year'] == 1994
    assert exp5['position'] == u'Analyst Programmer'
    # Education Parsing.
    educations_xml_list = bs4(DOCX, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'South Bank University'), None)
    assert edu1
    assert edu1['city'] == u'London'
    assert {
                'start_month': None, 'end_month': 7, 'start_year': None,
                'bullets': [{'major': u'Computing Studies', 'comments': None}], 'title': u'B.Sc',
                'gpa_num': None, 'end_year': 1995, 'type': 'Bachelor of Science'} in edu1['degrees']


def test_g642_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_642, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert first == u'Bobby'
    assert last == u'Breland'
    assert {'value': u'+15137595877', 'label': 'Home'} in phones
    assert {'value': u'+15134773784', 'label': 'Mobile'} in phones
    assert GET_642_ADDRESS in addresses
    # Experience parsing.
    experience_xml_list = bs4(GET_642, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    exp1 = next((org for org in experiences if org["organization"] == u'Pivotalthought Llc'), None)
    exp2 = next((org for org in experiences if org["organization"] == u'Gxs, Inc'), None)
    exp3 = next((org for org in experiences if org["organization"] == u'Sun Microsystems'), None)
    exp4 = next((org for org in experiences if org["organization"] == u'First Consulting Group'), None)
    exp5 = next((org for org in experiences if org["organization"] == u'Computer Sciences Corporation Consulting Group'), None)
    exp6 = next((org for org in experiences if org["organization"] == u'Seebeyond Technology Corporation'), None)
    exp7 = next((org for org in experiences if org["organization"] == u'Collaborex, Inc'), None)
    # exp8 = next((org for org in experiences if org["organization"] == u'Origin Technology in Business'), None)
    exp8 = next((org for org in experiences if org["organization"] == u'Origin Technology'), None)
    exp9 = next((org for org in experiences if org["organization"] == u'R.w. Johnson Pri'), None)
    exp10 = next((org for org in experiences if org["organization"] == u'Taratec Development Corporation'), None)
    exp11 = next((org for org in experiences if org["organization"] == u'H. B. Zachry'), None)
    exp12 = next((org for org in experiences if org["organization"] == u'Triple I'), None)
    assert None not in [exp1, exp2, exp3, exp4, exp5, exp6, exp7, exp8, exp9, exp10, exp11, exp12]
    assert exp1['start_month'] == 1
    assert exp1['start_year'] == 2010
    # assert exp1['city'] == u'Liberty Township'
    assert exp1['city'] == u'Liberty'
    assert exp2['start_month'] == 8
    assert exp2['start_year'] == 2008
    assert exp2['end_month'] == 1
    assert exp2['end_year'] == 2010
    assert exp2['city'] == u'Gaithersburg'
    assert exp3['start_month'] == 3
    assert exp3['start_year'] == 2006
    assert exp3['end_month'] == 7
    assert exp3['end_year'] == 2008
    assert exp3['city'] == u'Santa Clara'
    assert exp4['start_month'] == 11
    assert exp4['start_year'] == 2005
    assert exp4['end_month'] == 3
    assert exp4['end_year'] == 2006
    assert exp4['city'] == u'Long Beach'
    assert exp5['start_month'] == 2
    assert exp5['start_year'] == 2003
    assert exp5['end_month'] == 11
    assert exp5['end_year'] == 2005
    assert exp5['city'] == u'Waltham'
    assert exp6['start_month'] == 3
    assert exp6['start_year'] == 2001
    assert exp6['end_month'] == 2
    assert exp6['end_year'] == 2003
    assert exp6['city'] == u'Monrovia'
    assert exp7['start_month'] == 4
    assert exp7['start_year'] == 2000
    assert exp7['end_month'] == 3
    assert exp7['end_year'] == 2001
    assert exp7['city'] == u'Fairfax'
    assert exp8['start_month'] == 2
    assert exp8['start_year'] == 1998
    assert exp8['end_month'] == 4
    assert exp8['end_year'] == 2000
    assert exp8['city'] == u'Cincinnati'
    assert exp9['start_month'] == 5
    assert exp9['start_year'] == 1995
    assert exp9['end_month'] == 2
    assert exp9['end_year'] == 1998
    assert exp9['city'] == u'Raritan'
    assert exp10['start_month'] == 12
    assert exp10['start_year'] == 1991
    assert exp10['end_month'] == 5
    assert exp10['end_year'] == 1995
    assert exp10['city'] == u'Bridgewater'
    assert exp11['start_month'] == 4
    assert exp11['start_year'] == 1991
    assert exp11['end_month'] == 12
    assert exp11['end_year'] == 1991
    assert exp11['city'] == u'San Antonio'
    assert exp12['start_month'] == 6
    assert exp12['start_year'] == 1989
    assert exp12['end_month'] == 4
    assert exp12['end_year'] == 1991
    assert exp12['city'] == u'Deepwater'
    # Educations.
    educations_xml_list = bs4(GET_642, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'Northeast Louisiana University'), None)
    assert edu1
    assert {'start_month': None, 'end_month': 12, 'start_year': None,
            'bullets': [{'major': u'Computer Science', 'comments': None}], 'title': u'B.S',
            'gpa_num': None, 'end_year': 1988, 'type': 'Bachelor of Science'} in edu1['degrees']


def test_g646_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_646, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert first == 'Patrick'
    assert last == 'Kaldawy'
    assert GET_646_ADDRESS in addresses
    assert {'value': u'+18583531111', 'label': 'Home'} in phones
    assert {'value': u'+18583532222', 'label': 'Mobile'} in phones
    assert {'value': u'+18583535555', 'label': 'Work'} in phones
    assert {'value': u'+18583533333', 'label': 'Work'} in phones
    assert {'value': u'+18583534444', 'label': 'Home Fax'} in phones
    assert {'value': u'+96170345340', 'label': 'Mobile'} in phones
    # Experience parsing.
    experience_xml_list = bs4(GET_646, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    # Name is currently not grabbed.
    # exp1 = next((org for org in experiences if org["organization"] == u'Technical Difference'), None)
    exp2 = next((org for org in experiences if org["organization"] == u'Convergence Inc. Llc'), None)
    exp3 = next((org for org in experiences if org["organization"] == u'Avalon Digital Marketing Systems, Inc'), None)
    # The following returns the org name without the division in parens.
    # exp4 = next((org for org in experiences if org["organization"] == u'Avalon Digital Marketing Systems, Inc (European Division'), None)
    # assert None not in [exp1, exp2, exp3, exp4]
    assert None not in [exp2, exp3]
    assert exp2['start_month'] == 3
    assert exp2['start_year'] == 2004
    assert exp2['end_month'] == 9
    assert exp2['end_year'] == 2004
    assert exp3['start_year'] == 2002
    assert exp3['end_year'] == 2003
    # Educations.
    educations_xml_list = bs4(GET_646, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    # edu1 = next((edu for edu in educations if edu["school_name"] == u'California State University, Chico'), None)
    # assert edu1
    edu2 = next((edu for edu in educations if edu["school_name"] == u'Butte College'), None)
    assert edu2
    assert {'start_month': 1, 'end_month': 1, 'start_year': 1995,
            'bullets': [{'major': None, 'comments': None}], 'title': u'A.A', 'gpa_num': None,
            'end_year': 1996, 'type': 'Associate of Arts'} in edu2['degrees']


def test_g626a_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_626a, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    # assert contact_xml['first_name'] == 'Yetunde'
    # assert contact_xml['last_name'] == 'Laniran'
    assert GET_626a_ADDRESS in addresses
    assert {'value': u'+15033330350', 'label': 'Other'} in phones
    # Experience parsing.
    experience_xml_list = bs4(GET_626a, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    exp1 = next((org for org in experiences if org["organization"] == u'Census Bureau'), None)
    assert exp1
    assert exp1['start_month'] == 9
    assert exp1['start_year'] == 2009
    assert exp1['city'] == u'Bothell'
    assert exp1['state'] == u'WA'
    assert exp1['position'] == u'Partnership Specialist'
    exp2 = next((org for org in experiences if org['organization'] == u'Nw Facility Maintenance'), None)
    assert exp2
    assert exp2['position'] == u'Network Admin/Project Coordinator'
    assert exp2['start_month'] == 1
    assert exp2['start_year'] == 2007
    assert exp2['end_month'] == 9
    assert exp2['end_year'] == 2009
    assert exp2['city'] == u'Portland'
    assert exp2['state'] == u'OR'
    # exp3 = next((org for org in experiences if org['organization'] == u'Via Training'), None)
    exp4 = next((org for org in experiences if org['organization'] == u'Oregon Catholic Press'), None)
    assert exp4
    assert exp4['position'] == u'Project Manager/ Computer Support Specialist'
    assert exp4['start_month'] == 9
    assert exp4['start_year'] == 2001
    assert exp4['end_month'] == 12
    assert exp4['end_year'] == 2006
    assert exp4['city'] == u'Portland'
    assert exp4['state'] == u'OR'
    exp5 = next((org for org in experiences if org["organization"] == u'Teksystems'), None)
    assert exp5
    assert exp5['position'] == u'Computer Support Specialist'
    assert exp5['start_month'] == 7
    assert exp5['start_year'] == 2000
    assert exp5['end_month'] == 7
    assert exp5['end_year'] == 2001
    assert exp5['city'] == u'Portland'
    assert exp5['state'] == u'OR'
    exp6 = next((org for org in experiences if org["organization"] == u'Manpower'), None)
    assert exp6
    assert exp6['position'] == u'Computer Support Specialist'
    assert exp6['start_month'] == 9
    assert exp6['start_year'] == 1999
    assert exp6['end_month'] == 7
    assert exp6['end_year'] == 2000
    assert exp6['city'] == u'Portland'
    assert exp6['state'] == u'OR'
    exp7 = next((org for org in experiences if org["organization"] == u'Portland Youth Builders'), None)
    assert exp7
    assert exp7['position'] == u'Computer Instructor/Support Specialist'
    assert exp7['start_month'] == 4
    assert exp7['start_year'] == 1999
    assert exp7['end_month'] == 9
    assert exp7['end_year'] == 1999
    assert exp7['city'] == u'Portland'
    assert exp7['state'] == u'OR'
    exp8 = next((org for org in experiences if org["organization"] == u'University Of Oregon'), None)
    assert exp8
    # assert exp8['position'] == u'Instructor- Linguistics'
    assert exp8['start_month'] == 12
    assert exp8['start_year'] == 1998
    assert exp8['end_month'] == 3
    assert exp8['end_year'] == 1999
    exp9 = next((org for org in experiences if org["organization"] == u'Portland State University'), None)
    assert exp9
    # assert exp9['position'] == u'Instructor - Language and Culture'
    assert exp9['start_month'] == 7
    assert exp9['start_year'] == 1998
    assert exp9['end_month'] == 8
    assert exp9['end_year'] == 1998
    # exp10 = next((org for org in experiences if org["organization"] == u'Oregon Graduate Institute'), None)
    exp11 = next((org for org in experiences if org["organization"] == u'University Of North Carolina'), None)
    assert exp11
    # assert exp11['position'] == u'Research Associcate - Linguistics'
    assert exp11['start_month'] == 1
    assert exp11['start_year'] == 1995
    assert exp11['end_month'] == 6
    assert exp11['end_year'] == 1997
    # Educations.
    educations_xml_list = bs4(GET_626a, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'University of Phoenix'), None)
    assert edu1
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'Information Systems/Management', 'comments': None}],
            'title': u'Masters', 'gpa_num': None, 'end_year': 2007, 'type': "Master's"} in edu1['degrees']
    edu2 = next((edu for edu in educations if edu["school_name"] == u'Heald College'), None)
    assert edu2
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'Computer Technology', 'comments': None}],
            'title': u'Diploma', 'gpa_num': None, 'end_year': 1999, 'type': 'Diploma'} in edu2['degrees']
    # edu3 = next((edu for edu in educations if edu["school_name"] == u'Cornell University'), None)
    edu4 = next((edu for edu in educations if edu["school_name"] == u'Cornell University'), None)
    assert edu4
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'Linguistics', 'comments': None}],
            'title': u'Master of Arts Degree', 'gpa_num': None, 'end_year': 1988,
            'type': "Master's"} in edu4['degrees']
    edu5 = next((edu for edu in educations if edu["school_name"] == u'University of Ibadan'), None)
    assert edu5
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'Linguistics', 'comments': None}],
            'title': u'Bachelor of Arts Degree', 'gpa_num': None, 'end_year': 1979,
            'type': "Bachelor's"} in edu5['degrees']


def test_g626b_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_626b, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert first == 'Kate'
    assert last == 'Begonia'
    assert GET_626b_ADDRESS in addresses
    # assert {'value': u'503.493.1548'} in phones
    # Experience parsing.
    experience_xml_list = bs4(GET_626b, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    # Below does not parse positions after , in Director
    # exp1 = next((org for org in experiences if (
    #     org["organization"] == u'Sage Software' and
    #     org['position'] == u'Director, Digital Marketing Communications')), None)
    # exp2 = next((org for org in experiences if (
    #     org["organization"] == u'Sage Software' and
    #     org['position'] == u'Director, Creative Services')), None)
    # The below is for a self employed consulting job.
    # exp3 = next((org for org in experiences if org["organization"] == u'None'), None)
    # exp4 = next((org for org in experiences if (
    #     org["organization"] == u'Oracle Corporation' and
    #     org['position'] == u'Senior Director, Branding')), None)
    # exp5 = next((org for org in experiences if (
    #     org["organization"] == u'Oracle Corporation' and
    #     org['position'] == u'Senior Director, Global Advertising')), None)
    # exp6 = next((org for org in experiences if (
    #     org["organization"] == u'Oracle Corporation' and
    #     org['position'] == u'Director, Global Advertising and Direct Marketing Programs')), None)
    # exp7 = next((org for org in experiences if (
    #     org["organization"] == u'Oracle Corporation' and
    #     org['position'] == u'Senior Advertising Manager, Domestic Advertising')), None)
    # exp8 = next((org for org in experiences if (
    #     org["organization"] == u'Oracle Corporation' and
    #     org['position'] == u'Marketing Manager, Industry Solutions Marketing')), None)
    # Educations.
    educations_xml_list = bs4(GET_626b, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'San Francisco State University'), None)
    assert edu1
    assert {'start_month': None, 'end_month': None, 'start_year': None,
            'bullets': [{'major': u'Humanities', 'comments': None}], 'title': u'Bachelor of Arts',
            'gpa_num': None, 'end_year': None, 'type': "Bachelor's"} in edu1['degrees']


def test_pdf_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(PDF, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert first == 'Mark'
    assert last == 'Greene'
    assert PDF_ADDRESS in addresses
    assert {'value': u'+17275651234', 'label': 'Other'} in phones
    experience_xml_list = bs4(PDF, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    # exp1 = next((org for org in experiences if (
    #     org["organization"] == u'SmartSource' and
    #     org['position'] == u'Technical Support')), None)
    # exp2 = next((org for org in experiences if (
    #     org["organization"] == u'Aerotek, Bank of America' and
    #     org['position'] == u'Mortgage Affiliate Services')), None)
    # TODO: look into raw (JCIII &amp; Associates)
    # exp3 = next((org for org in experiences if (
    #     org["organization"] == u'JCIII & Associates' and
    #     org['position'] == u'Document Reviewer')), None)
    exp4 = next((org for org in experiences if (
        org["organization"] == u'CHASE' and
        org['position'] == u'Sr. Loan Processor')), None)
    assert exp4
    assert exp4['start_month'] == 5
    assert exp4['start_year'] == 2012
    assert exp4['end_month'] == 10
    assert exp4['end_year'] == 2012
    assert exp4['city'] == u'Tampa'
    assert exp4['state'] == u'FL'
    exp5 = next((org for org in experiences if (
        org["organization"] == u'CHASE' and
        org['position'] == u'Business Analyst/Loss Mitigation Specialist')), None)
    assert exp5
    assert exp5['start_month'] == 7
    assert exp5['start_year'] == 2010
    assert exp5['end_month'] == 5
    assert exp5['end_year'] == 2012
    assert exp5['city'] == u'Tampa'
    assert exp5['state'] == u'FL'
    exp6 = next((org for org in experiences if (
        org["organization"] == u'Computer Generated Solutions' and
        org['position'] == u'Team Lead')), None)
    assert exp6
    assert exp6['start_month'] == 12
    assert exp6['start_year'] == 2007
    assert exp6['end_month'] == 12
    assert exp6['end_year'] == 2008
    assert exp6['city'] == u'Tampa'
    assert exp6['state'] == u'FL'
    exp7 = next((org for org in experiences if (
        org["organization"] == u'Computer Generated Solutions' and
        org['position'] == u'Desktop Support Agent')), None)
    assert exp7
    assert exp7['start_month'] == 9
    assert exp7['start_year'] == 2006
    assert exp7['end_month'] == 2
    assert exp7['end_year'] == 2007
    assert exp7['city'] == u'Tampa'
    assert exp7['state'] == u'FL'
    exp6 = next((org for org in experiences if (
        org["organization"] == u'Advanced System Design' and
        org['position'] == u'Software Analyst')), None)
    assert exp6
    assert exp6['start_month'] == 10
    assert exp6['start_year'] == 2005
    assert exp6['end_month'] == 5
    assert exp6['end_year'] == 2006
    assert exp6['city'] == u'Tallahassee'
    assert exp6['state'] == u'FL'
    exp6 = next((org for org in experiences if (
        org["organization"] == u'Bmc Solutions' and
        org['position'] == u'Desktop Deployment Technician')), None)
    assert exp6
    assert exp6['start_month'] == 7
    assert exp6['start_year'] == 2005
    assert exp6['end_month'] == 8
    assert exp6['end_year'] == 2005
    assert exp6['city'] == u'Tallahassee'
    assert exp6['state'] == u'FL'
    educations_xml_list = bs4(PDF, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'ITT Technical Institute'), None)
    assert edu1
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'Information Systems/Cyber Securities', 'comments': None}],
            'title': u'Bachelor of Science Degree', 'gpa_num': None, 'end_year': 2013,
            'type': "Bachelor's"} in edu1['degrees']


def test_pdf13_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(PDF_13, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    assert first == 'Bruce'
    assert last == 'Parkey'
    assert {'value': u'+16309302756', 'label': 'Other'} in phones
    experience_xml_list = bs4(PDF_13, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    exp1 = next((org for org in experiences if org["organization"] == u'Sagamore Apps, Inc'), None)
    assert exp1
    # assert exp1['position'] == u'Owner and Senior iOS Contract Developer'
    assert exp1['start_month'] == 1
    assert exp1['start_year'] == 2008
    assert exp1['city'] == u'Darien'
    assert exp1['state'] == u'IL'
    exp2 = next((org for org in experiences if (
        org["organization"] == u'Rapid Solutions Group' and
        org['position'] == u'Vice President and Chief Information Officer')), None)
    assert exp2
    assert exp2['start_month'] == 1
    assert exp2['start_year'] == 2003
    assert exp2['end_month'] == 1
    assert exp2['end_year'] == 2007
    assert exp2['city'] == u'Mt. Prospect'
    assert exp2['state'] == u'IL'
    exp3 = next((org for org in experiences if org["organization"] == u'Ams Direct, Inc'), None)
    assert exp3
    # assert exp3['position'] == u'Vice President Information Technology'
    assert exp3['start_month'] == 1
    assert exp3['start_year'] == 1999
    assert exp3['end_month'] == 1
    assert exp3['end_year'] == 2003
    assert exp3['city'] == u'Burr Ridge'
    assert exp3['state'] == u'IL'
    educations_xml_list = bs4(PDF_13, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'Purdue University'), None)
    assert edu1
    assert {'start_month': None, 'end_month': None, 'start_year': None,
            'bullets': [{'major': u'Information Systems', 'comments': None}],
            'title': u'Bachelor of Science', 'gpa_num': None, 'end_year': None,
            'type': "Bachelor's"} in edu1['degrees']


def test_pdf14_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(PDF_14, 'lxml').findAll('contact')
    first, last = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    experience_xml_list = bs4(PDF_14, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    for exp in experiences:
        assert len(exp['bullets']) == 1
    educations_xml_list = bs4(PDF_14, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    assert first == 'Jose'
    assert last == 'Chavez'
    # assert {'value': u'604.609.0921'} in phones
    # exp1 = next((org for org in experiences if (
    #     org["organization"] == u'Organization Committee Commonwelath Games 2010' and
    #     org['position'] == u'Games Management Systems Director')), None)
    # exp2 = next((org for org in experiences if (
    #     org["organization"] == u'Atos Origin Canada' and
    #     org['position'] == u'Core Games Systems Application Manager')), None)
    # exp3 = next((org for org in experiences if (
    #     org["organization"] == u'Design Maintenance Systems Inc.' and
    #     org['position'] == u'Software Testing Engineer/ Jr. Developer')), None)
    # exp4 = next((org for org in experiences if (
    #     org["organization"] == u'Orbital Technologies Inc.' and
    #     org['position'] == u'Software Testing Engineer')), None)
    edu1 = next((edu for edu in educations if edu["school_name"] == u'ITESO University'), None)
    assert edu1
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'Computer Systems Engineer', 'comments': None}],
            'title': u'B. Sc', 'gpa_num': None, 'end_year': 1992,
            'type': 'Bachelor of Science'} in edu1['degrees']
    # edu2 = next((edu for edu in educations if edu["school_name"] == u'ITESM University'), None)
    edu3 = next((edu for edu in educations if edu["school_name"] == u'British Columbia Institute of Technology'), None)
    assert {'start_month': None, 'end_month': 1, 'start_year': None,
            'bullets': [{'major': u'software Engineering', 'comments': None}],
            'title': u'Software Engineering Diploma', 'gpa_num': None, 'end_year': 1993,
            'type': 'Diploma'} in edu3['degrees']


def test_parsing_edu_combinations():
    xml_combos = [xml for xml in dir(edu_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(edu_combinations, combo), 'lxml').findAll('education')
        educations = parse_candidate_educations(combo_to_parse)
        for education in educations:
            assert validate(education, EDU_SCHEMA, format_checker=FormatChecker()) is None


def test_parsing_addresses():
    xml_combos = [xml for xml in dir(contact_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(contact_combinations, combo), 'lxml').findAll('contact')
        addresses = parse_candidate_addresses(combo_to_parse)
        for address in addresses:
            assert validate(address, ADDRESS_SCHEMA, format_checker=FormatChecker()) is None


def test_parsing_emails():
    xml_combos = [xml for xml in dir(contact_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(contact_combinations, combo), 'lxml').findAll('contact')
        emails = parse_candidate_emails(combo_to_parse)
        for email in emails:
            assert validate(email, EMAIL_SCHEMA, format_checker=FormatChecker()) is None


def test_parsing_names():
    xml_combos = [xml for xml in dir(contact_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(contact_combinations, combo), 'lxml').findAll('contact')
        # Below is testing that the parse_candidate_name function can handle multiple xml tree
        # structures without raising an exception. We are not concerned about the returned values as
        # it can be (string, string), (None, string), (string, None), or (None, None)
        assert parse_candidate_name(combo_to_parse)



def test_parsing_phones():
    xml_combos = [xml for xml in dir(contact_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(contact_combinations, combo), 'lxml').findAll('contact')
        phones = parse_candidate_phones(combo_to_parse)
        for phone in phones:
            assert validate(phone, PHONE_SCHEMA, format_checker=FormatChecker()) is None


def test_parsing_experiences():
    xml_combos = [xml for xml in dir(job_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(job_combinations, combo), 'lxml').findAll('experience')
        experiences = parse_candidate_experiences(combo_to_parse)
        for experience in experiences:
            assert validate(experience, EXPERIENCE_SCHEMA, format_checker=FormatChecker()) is None

def test_parsing_skills():
    xml_combos = [xml for xml in dir(skill_combinations) if "__" not in xml]
    for combo in xml_combos:
        combo_to_parse = bs4(getattr(skill_combinations, combo), 'lxml').findAll('canonskill')
        skills = parse_candidate_skills(combo_to_parse)
        for skill in skills:
            assert validate(skill, SKILL_SCHEMA, format_checker=FormatChecker()) is None


def test_reference_parsing():
    soup = bs4(REFERENCE_XML)
    references_list = soup.findAll('references')
    references = parse_candidate_reference(references_list)
    assert references == u'References\n\nDerek Framer - (408) 835-6219\nJamtry Jonas - (408) 923-7259\nJoaquín Rodrigo'


def test_parses_duplicate_emails():
    double_email = """
        <contact>
            <email>k_begonia@yahoo.com</email>
            <email>k_begonia@yahoo.com</email>
            <email>k_begonia2@yahoo.com</email>
        </contact>
    """
    soup = bs4(double_email)
    contact = soup.findAll('contact')
    parsed_emails = parse_candidate_emails(contact)
    assert len(parsed_emails) == 2


def test_phone_label_testing():
    phones_mixed = """
        <contact>
            <phone area="408" type="cell">(408) 867-5309</phone>
            <phone area="409" type="work">(409) 867-5309</phone>
            <phone area="410" type="fax">(410) 867-5309</phone>
            <phone area="411" type="home">(411) 867-5309</phone>
        </contact>
    """
    soup = bs4(phones_mixed)
    contact = soup.findAll('contact')
    parsed_phones = parse_candidate_phones(contact)
    assert len(parsed_phones) == 4
    assert any(phone['label'] == 'Mobile' for phone in parsed_phones)
    assert any(phone['label'] == 'Work' for phone in parsed_phones)
    assert any(phone['label'] == 'Home Fax' for phone in parsed_phones)
    assert any(phone['label'] == 'Home' for phone in parsed_phones)


def test_bullet_parsing():
    soup = bs4(SQUARE_BULLETS).findAll('experience')
    experiences = parse_candidate_experiences(soup)
    for experience in experiences:
        if experience['organization'] == u'Verizon Wireless':
            assert experience['bullets'][0]['description'].count('\n') == 9
        elif experience['organization'] == u'Wal-mart':
            assert experience['bullets'][0]['description'].count('\n') == 7
        if experience['organization'] == u'Jamaica Savings Bank':
            assert experience['bullets'][0]['description'].count('\n') == 2


def test_text_is_truncd():
    title = """I was was a French military and political leader who rose to prominence during the
    French Revolution and led several successful campaigns during the Revolutionary Wars. As
    Napoleon I, I was Emperor of the French from 1804 until 1814, and again in 1815. I dominated
    European and global affairs for more than a decade while leading France against a series of
    coalitions in the Napoleonic Wars."""
    assert(len(trunc_text(title, 100)) == 100)
