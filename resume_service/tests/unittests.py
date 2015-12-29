__author__='erik@gettalent.com'
# Standard Library
import random
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
# Dependencies
from resume_service.common.utils.handy_functions import random_word
from resume_service.common.redis_conn import redis_client
# Modules being tested.
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_addresses
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_educations
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_emails
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_experiences
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_name
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_phones
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_candidate_skills
from resume_service.resume_parsing_app.views.batch_lib import add_file_names_to_queue

EDUCATIONS_KEYS = ('city', 'degrees', 'state', 'country', 'school_name')
WORK_EXPERIENCES_KEYS = ('city', 'state', 'end_date', 'country', 'company', 'role', 'is_current',
                         'start_date', 'work_experience_bullets')
ADDRESS_KEYS = ('city', 'country', 'state', 'address_line_1', 'zip_code')

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
#     # This PDF currently does not get its email/phone parsed out of the footer.
#     # This PDF currently parses out the wrong education count
    {'tree_name': PDF_14, 'name': 'Jose Chavez', 'email_len': 0, 'phone_len': 0, 'education_len': 2,
     'experience_len': 4, 'skills_len': 36, 'addresses_len': 1}
]


def test_name_parsing_with_xml():
    """Basic name parsing test."""
    for j in XML_MAPS:
        resume = j['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        if contact_xml_list:
            name = parse_candidate_name(contact_xml_list)
            assert name['first_name'] == j['name'].split()[0]
            assert name['last_name'] == j['name'].split()[1]


def test_email_parsing_with_xml():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the 'address' key (only needed key for candidate creation).
    """
    for j in XML_MAPS:
        resume = j['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        emails = parse_candidate_emails(contact_xml_list)
        assert len(emails)== j['email_len']
        for e in emails:
            assert 'address' in e


def test_phone_parsing_from_xml():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the 'value' key.
    """
    for j in XML_MAPS:
        resume = j['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        phones = parse_candidate_phones(contact_xml_list)
        assert len(phones)== j['phone_len']
        for p in phones:
            assert 'value' in p


def test_experience_parsing_from_xml():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the correct keys.
    """
    for j in XML_MAPS:
        resume = j['tree_name']
        experience_xml_list = bs4(resume, 'lxml').findAll('experience')
        experiences = parse_candidate_experiences(experience_xml_list)
        assert len(experiences) == j['experience_len']
        for e in experiences:
            assert all(k in e for k in WORK_EXPERIENCES_KEYS if e)


def test_education_parsing_from_xml():
    """
        Tests parsing function using the JSON response to avoid un-needed API calls
        1. Test proper count.
        2. Test that each item has the correct education keys.
    """
    for j in XML_MAPS:
        resume = j['tree_name']
        educations_xml_list = bs4(resume, 'lxml').findAll('education')
        educations = parse_candidate_educations(educations_xml_list)
        # Verify Expected Length
        assert len(educations) == j['education_len']
        # Very each dict in list has proper keys
        for e in educations:
            assert all(k in e for k in EDUCATIONS_KEYS if e)


def test_skill_parsing_from_xml():
    for j in XML_MAPS:
        resume = j['tree_name']
        skill_xml_list= bs4(resume, 'lxml').findAll('canonskill')
        skills = parse_candidate_skills(skill_xml_list)
        assert len(skills) == j['skills_len']
        for s in skills:
            assert 'name' in s


def test_address_parsing_from_xml():
    for j in XML_MAPS:
        resume = j['tree_name']
        contact_xml_list = bs4(resume, 'lxml').findAll('contact')
        addresses = parse_candidate_addresses(contact_xml_list)
        assert len(addresses) == j['addresses_len']
        for a in addresses:
            assert all(k in a for k in ADDRESS_KEYS if a)


def test_626_experience_parsing():
    experience_xml_list_a = bs4(GET_626a, 'lxml').findAll('experience')
    experiences_a = parse_candidate_experiences(experience_xml_list_a)
    experience_xml_list_b = bs4(GET_626b, 'lxml').findAll('experience')
    experiences_b = parse_candidate_experiences(experience_xml_list_b)
    for e in experiences_a:
        assert all(k in e for k in WORK_EXPERIENCES_KEYS if e)
    for e in experiences_b:
        assert all(k in e for k in WORK_EXPERIENCES_KEYS if e)

def test_add_single_item_to_batch_queue():
    user_id = random_word(6)
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    response = add_file_names_to_queue(['file1'], user_id)
    redis_client.expire(queue_string, 20)
    assert response == '{} - Size: {}'.format(queue_string, 1)

def test_add_multiple_items_to_batch_queue():
    user_id = random_word(6)
    file_count = random.randrange(1, 100)
    filenames = ['file{}'.format(i) for i in xrange(file_count)]
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    response = add_file_names_to_queue(filenames, user_id)
    redis_client.expire(queue_string, 20)
    assert response == '{} - Size: {}'.format(queue_string, file_count)
