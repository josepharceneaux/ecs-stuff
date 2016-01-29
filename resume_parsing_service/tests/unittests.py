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

XML_MAPS = [
    {'tree_name': DOCX, 'name': 'Veena Nithoo', 'email_len': 0, 'phone_len': 1, 'education_len': 1,
     'experience_len': 7, 'skills_len': 48, 'addresses_len': 2},
    # The resume below has 12 experience but BG incorrectly returns 13
    {'tree_name': GET_642, 'name': 'Bobby Breland', 'email_len': 1, 'phone_len': 2,
     'education_len': 1, 'experience_len': 13, 'skills_len': 80, 'addresses_len': 2},
    {'tree_name': GET_646, 'name': 'Patrick Kaldawy', 'email_len': 3, 'phone_len': 6,
     'education_len': 2, 'experience_len': 4, 'skills_len': 42, 'addresses_len': 1},
    {'tree_name': PDF, 'name': 'Mark Greene', 'email_len': 1, 'phone_len': 1, 'education_len': 1,
     'experience_len': 11, 'skills_len': 20, 'addresses_len': 1},
    {'tree_name': PDF_13, 'name': 'Bruce Parkey', 'email_len': 1, 'phone_len': 1,
     'education_len': 1, 'experience_len': 3, 'skills_len': 24, 'addresses_len': 1},
    # This PDF currently does not get its email/phone parsed out of the footer.
    # This PDF currently parses out the wrong education count
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


# TODO: investigate 'offline' options in talent_s3 lib
# This could be useful for debugging but requires an application context (keys in .cfg) to run.
# def test_process_batch_item_without_saving():
#     # Create a single file queue.
#     user_id = random_word(6)
#     queue_string = 'batch:{}:fp_keys'.format(user_id)
#     unused_queue_status = add_fp_keys_to_queue(['0169173d35beaf1053e79fdf1b5db864.docx'], user_id)
#     redis_client.expire(queue_string, 10)
#     # Mock a call to process/<user_id> endpoint
#     candidate_response = _process_batch_item(user_id, create_candidate=False)
#     assert 'candidate' in candidate_response
