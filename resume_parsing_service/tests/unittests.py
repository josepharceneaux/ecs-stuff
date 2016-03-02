"""Unit tests for formatting and accuracy for offline testing."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position
# Third party.
from bs4 import BeautifulSoup as bs4
# JSON outputs.
from .resume_xml import DOCX
from .resume_xml import GET_626a
from .resume_xml import GET_626b
from .resume_xml import GET_642
from .resume_xml import GET_646
from .resume_xml import PDF
from .resume_xml import PDF_13
from .resume_xml import PDF_14
# Modules being tested.
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_addresses
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_educations
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_emails
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_experiences
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_name
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_phones
from resume_parsing_service.app.views.optic_parse_lib import parse_candidate_skills


EDUCATIONS_KEYS = ('city', 'country', 'degrees', 'state', 'school_name')
WORK_EXPERIENCES_KEYS = ('bullets', 'city', 'country', 'end_month', 'end_year', 'is_current',
                         'organization', 'position', 'start_month', 'start_year', 'state')
ADDRESS_KEYS = ('address_line_1', 'city', 'country', 'state', 'zip_code')

DOCX_ADDRESS = {'city': u'Lansdale', 'state': u'Pennsylvania', 'country': 'US', 'zip_code': '19446',
                'address_line_1': u'466 Tailor Way'}
GET_642_ADDRESS = {'city': u'Liberty Township', 'state': u'OH', 'country': 'US',
                   'zip_code': '45011', 'address_line_1': u'6507 Hughes Ridge Lane'}
GET_646_ADDRESS = {'city': u'Solana Beach', 'state': u'CA', 'country': 'US', 'zip_code': '92075',
                  'address_line_1': u'930 Via Di Salerno Unit 119'}
GET_626a_ADDRESS = {'city': u'Portland', 'state': u'Oregon', 'country': 'US', 'zip_code': '97211',
                    'address_line_1': u'1602 NE Junior St.'}
GET_626b_ADDRESS = {'city': u'Portland', 'state': u'OR', 'country': 'US', 'zip_code': '97212',
                    'address_line_1': u'4014 NE Failing Street'}
PDF_ADDRESS = {'city': u'St. Petersburg', 'state': u'FL', 'country': 'US', 'zip_code': '33713 5855',
               'address_line_1': u'2462 13 th Avenue North #6-101'}

XML_MAPS = [
    # The resume below has 6 experience but BG incorrectly returns 7.
    # The resume below has 1 address but BG incorrectly returns 2.
    {'tree_name': DOCX, 'name': 'Veena Nithoo', 'email_len': 0, 'phone_len': 1, 'education_len': 1,
     'experience_len': 7, 'skills_len': 48, 'addresses_len': 2},
    # The resume below has 12 experience but BG incorrectly returns 13.
    # The resume below has 1 address but BG incorrectly returns 2.
    {'tree_name': GET_642, 'name': 'Bobby Breland', 'email_len': 1, 'phone_len': 2,
     'education_len': 1, 'experience_len': 13, 'skills_len': 80, 'addresses_len': 2},
    # The resume below has 2 addresses but BG incorrectly returns 1.
    {'tree_name': GET_646, 'name': 'Patrick Kaldawy', 'email_len': 3, 'phone_len': 6,
     'education_len': 2, 'experience_len': 4, 'skills_len': 42, 'addresses_len': 1},
    {'tree_name': PDF, 'name': 'Mark Greene', 'email_len': 1, 'phone_len': 1, 'education_len': 1,
     'experience_len': 11, 'skills_len': 20, 'addresses_len': 1},
    {'tree_name': PDF_13, 'name': 'Bruce Parkey', 'email_len': 1, 'phone_len': 1,
     'education_len': 1, 'experience_len': 3, 'skills_len': 24, 'addresses_len': 1},
    # This PDF currently does not get its email/phone parsed out of the footer.
    # This PDF currently parses out the wrong education count.
    {'tree_name': PDF_14, 'name': 'Jose Chavez', 'email_len': 0, 'phone_len': 0, 'education_len': 2,
     'experience_len': 4, 'skills_len': 36, 'addresses_len': 1}
]


def test_name_parsing():
    """Basic name parsing test."""
    for xml in XML_MAPS:
        resume = xml['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        if contact_xml_list:
            name = parse_candidate_name(contact_xml_list)
            assert name['first_name'] == xml['name'].split()[0]
            assert name['last_name'] == xml['name'].split()[1]


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
            assert 'address' in email


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
            assert 'value' in phone, 'Phone dict is missing value key'


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
            # Asserts that experience contains all keys inside WORK_EXPERIENCE_KEYS
            assert all(k in experience for k in WORK_EXPERIENCES_KEYS if experience)
            # Check nested dicts in bullets
            if experience['bullets']:
                for bullet in experience['bullets']:
                    assert 'description' in bullet
    # Tests against specific KeyError reported in JIRA (GET-626)
    xml_experiences_a = bs4(GET_626a, 'lxml').findAll('experience')
    processed_experiences_a = parse_candidate_experiences(xml_experiences_a)
    xml_experiences_b = bs4(GET_626b, 'lxml').findAll('experience')
    processed_experiences_b = parse_candidate_experiences(xml_experiences_b)
    for experience_dict in processed_experiences_a:
        assert all(k in experience_dict for k in WORK_EXPERIENCES_KEYS if experience_dict)
    for experience_dict in processed_experiences_b:
        assert all(k in experience_dict for k in WORK_EXPERIENCES_KEYS if experience_dict)


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
            assert all(k in education for k in EDUCATIONS_KEYS if education)
        assert type(education['degrees'] == list())


def test_skill_parsing():
    """Tests skills are parsed and formatted properly."""
    for xml in XML_MAPS:
        resume = xml['tree_name']
        skill_xml_list = bs4(resume, 'lxml').findAll('canonskill')
        skills = parse_candidate_skills(skill_xml_list)
        assert len(skills) == xml['skills_len']
        for skill in skills:
            assert 'name' in skill


def test_address_parsing():
    """Tests addresses are parsed and formatted properly"""
    for xml in XML_MAPS:
        resume = xml['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        addresses = parse_candidate_addresses(contact_xml_list)
        assert len(addresses) == xml['addresses_len']
        for address in addresses:
            assert all(k in address for k in ADDRESS_KEYS if address)


def test_docx_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(DOCX, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert DOCX_ADDRESS in addresses
    assert contact_xml['first_name'] == 'Veena'
    assert contact_xml['last_name'] == 'Nithoo'
    assert {'value': u'(215) 412-0817'} in phones
    # Experience parsing.
    experience_xml_list = bs4(DOCX, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
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
    assert {'bullets': [], 'type': u'B.Sc', 'title': u'Computing Studies'} in edu1['degrees']


def test_g642_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_642, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert contact_xml['first_name'] == u'Bobby'
    assert contact_xml['last_name'] == u'Breland'
    assert {'value': u'513-759-5877'} in phones
    assert {'value': u'513-477-3784'} in phones
    assert GET_642_ADDRESS in addresses
    # Experience parsing.
    experience_xml_list = bs4(GET_642, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    exp1 = next((org for org in experiences if org["organization"] == u'Pivotalthought Llc'), None)
    exp2 = next((org for org in experiences if org["organization"] == u'Gxs, Inc'), None)
    exp3 = next((org for org in experiences if org["organization"] == u'Sun Microsystems'), None)
    exp4 = next((org for org in experiences if org["organization"] == u'First Consulting Group'), None)
    exp5 = next((org for org in experiences if org["organization"] == u'Computer Sciences Corporation Consulting Group'), None)
    exp6 = next((org for org in experiences if org["organization"] == u'Seebeyond Technology Corporation'), None)
    exp7 = next((org for org in experiences if org["organization"] == u'Collaborex, Inc'), None)
    # TODO: Log issue in spreadsheet.
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
    assert {'bullets': [], 'type': u'B.S', 'title': u'Computer Science'} in edu1['degrees']


def test_g646_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_646, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert contact_xml['first_name'] == 'Patrick'
    assert contact_xml['last_name'] == 'Kaldawy'
    assert GET_646_ADDRESS in addresses
    assert {'value': u'(858) 353-1111'} in phones
    assert {'value': u'(858) 353-2222'} in phones
    assert {'value': u'(858) 353-5555'} in phones
    assert {'value': u'(858) 353-3333'} in phones
    assert {'value': u'(858) 353-4444'} in phones
    assert {'value': u'+961 (70) 345-340'} in phones
    # Experience parsing.
    experience_xml_list = bs4(GET_646, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    # Name is currently not grabbed.
    # exp1 = next((org for org in experiences if org["organization"] == u'Technical Difference'), None)
    exp2 = next((org for org in experiences if org["organization"] == u'Convergence Inc. Llc'), None)
    exp3 = next((org for org in experiences if org["organization"] == u'Avalon Digital Marketing Systems, Inc'), None)
    # The following returns the org name without the division in parens.
    # exp4 = next((org for org in experiences if org["organization"] == u'Avalon Digital Marketing Systems, Inc (European Division'), None)
    # assert None not in [exp1, exp2, exp3, exp4]
    assert None not in [exp2, exp3]
    # assert exp1['start_month'] == 10
    # assert exp1['start_year'] == 2004
    assert exp2['start_month'] == 3
    assert exp2['start_year'] == 2004
    assert exp2['end_month'] == 9
    assert exp2['end_year'] == 2004
    assert exp3['start_year'] == 2002
    assert exp3['end_year'] == 2003
    # assert exp4['start_month'] == 5
    # assert exp4['start_year'] == 2001
    # assert exp4['end_month'] == 6
    # assert exp4['end_year'] == 2001
    # Educations.
    educations_xml_list = bs4(GET_646, 'lxml').findAll('education')
    educations = parse_candidate_educations(educations_xml_list)
    # edu1 = next((edu for edu in educations if edu["school_name"] == u'California State University, Chico'), None)
    # assert edu1
    edu2 = next((edu for edu in educations if edu["school_name"] == u'Butte College'), None)
    assert edu2
    assert {'bullets': [], 'type': u'A.A', 'title': None} in edu2['degrees']


def test_g626a_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_626a, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    # assert contact_xml['first_name'] == 'Yetunde'
    # assert contact_xml['last_name'] == 'Laniran'
    assert GET_626a_ADDRESS in addresses
    assert {'value': u'503.333.0350'} in phones
    # Experience parsing.
    experience_xml_list = bs4(GET_626a, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
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
    assert {'bullets': [], 'type': u'Masters', 'title': u'Information Systems/Management'} in edu1['degrees']
    edu2 = next((edu for edu in educations if edu["school_name"] == u'Heald College'), None)
    assert edu2
    assert {'bullets': [], 'type': u'Diploma', 'title': u'Computer Technology'} in edu2['degrees']
    # edu3 = next((edu for edu in educations if edu["school_name"] == u'Cornell University'), None)
    edu4 = next((edu for edu in educations if edu["school_name"] == u'Cornell University'), None)
    assert edu4
    assert {'bullets': [], 'type': u'Master of Arts Degree', 'title': u'Linguistics'} in edu4['degrees']
    edu5 = next((edu for edu in educations if edu["school_name"] == u'University of Ibadan'), None)
    assert edu5
    assert {'bullets': [], 'type': u'Bachelor of Arts Degree', 'title': u'Linguistics'} in edu5['degrees']


def test_g626b_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(GET_626b, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert contact_xml['first_name'] == 'Kate'
    assert contact_xml['last_name'] == 'Begonia'
    assert GET_626b_ADDRESS in addresses
    # assert {'value': u'503.493.1548'} in phones
    # Experience parsing.
    experience_xml_list = bs4(GET_626b, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
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
    assert {'bullets': [], 'type': u'Bachelor of Arts', 'title': u'Humanities'} in edu1['degrees']


def test_pdf_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(PDF, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert contact_xml['first_name'] == 'Mark'
    assert contact_xml['last_name'] == 'Greene'
    assert PDF_ADDRESS in addresses
    assert {'value': u'727.565.1234'} in phones
    experience_xml_list = bs4(PDF, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
    # exp1 = next((org for org in experiences if (
    #     org["organization"] == u'SmartSource' and
    #     org['position'] == u'Technical Support')), None)
    # exp2 = next((org for org in experiences if (
    #     org["organization"] == u'Bank of America' and
    #     org['position'] == u'Mortgage Affiliate Services')), None)
    # exp3 = next((org for org in experiences if (
    #     org["organization"] == u'JCIII & Associates' and
    #     org['position'] == u'Document Reviewer')), None)
    # exp4 = next((org for org in experiences if (
    #     org["organization"] == u'CHASE' and
    #     org['position'] == u'Sr. Loan Processor')), None)
    # exp5 = next((org for org in experiences if (
    #     org["organization"] == u'CHASE' and
    #     org['position'] == u'Business Analyst/Loss Mitigation Specialist')), None)
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
    assert {'bullets': [], 'type': u'Bachelor of Science Degree', 'title': u'Information Systems/Cyber Securities'} in edu1['degrees']


def test_pdf13_accuracy():
    # Contact Parsing.
    contact_xml_list = bs4(PDF_13, 'lxml').findAll('contact')
    contact_xml = parse_candidate_name(contact_xml_list)
    phones = parse_candidate_phones(contact_xml_list)
    addresses = parse_candidate_addresses(contact_xml_list)
    assert contact_xml['first_name'] == 'Bruce'
    assert contact_xml['last_name'] == 'Parkey'
    assert {'value': u'630-930-2756'} in phones
    experience_xml_list = bs4(PDF_13, 'lxml').findAll('experience')
    experiences = parse_candidate_experiences(experience_xml_list)
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
    assert {'bullets': [], 'type': u'Bachelor of Science', 'title': u'Information Systems'} in edu1['degrees']