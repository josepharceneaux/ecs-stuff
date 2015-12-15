"""Main resume parsing logic & functions."""

from cStringIO import StringIO
from os.path import basename
from os.path import splitext
from time import sleep
from time import time
import base64
import string
import datetime
import re
import json

import phonenumbers
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import process_pdf
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfparser import PDFDocument
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from xhtml2pdf import pisa
import requests
from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup as bs4
import magic
from flask import current_app
from OauthClient import OAuthClient
from resume_service.resume_parsing_app.views.optic_parse_lib import parse_optic_json, fetch_optic_response

# from talent_dice_client import parse_resume_with_bg


def parse_resume(file_obj, filename_str):
    """Primary resume parsing function.

    Args:
        file_obj: an s3 file object.
        filename_str: the file's name
        is_test_parser: debugging/test mode Bool.

    Returns:
        Dictionary containing error message or candidate data.

    """
    current_app.logger.info("Beginning parse_resume(%s)", filename_str)
    file_ext = basename(splitext(filename_str.lower())[-1]) if filename_str else ""

    if not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)

    image_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx',
                     '.pcx', '.jp2', '.jpc', '.jb2', '.djvu', '.djv']
    doc_formats = ['.pdf', '.doc', '.docx', '.rtf', '.txt']

    if file_ext not in image_formats and file_ext not in doc_formats:
        current_app.logger.error('file_ext {} not in image_formats and file_ext not in doc_formats'.format(file_ext))
        return dict(error='file_ext not in image_formats and file_ext not in doc_formats')

    # Find out if the file is an image
    is_resume_image = False
    if file_ext in image_formats:
        if file_ext == '.pdf':
            start_time = time()
            text = convert_pdf_to_text(file_obj)
            current_app.logger.info("Benchmark: convert_pdf_to_text(%s) took %ss", filename_str, time() - start_time)
            if not text.strip():
                # pdf is possibly an image
                is_resume_image = True
        else:
            is_resume_image = True
        final_file_ext = '.pdf'

    file_obj.seek(0)
    if is_resume_image:
        # If file is an image, OCR it
        start_time = time()
        doc_content = ocr_image(file_obj)
        current_app.logger.info("Benchmark: ocr_image(%s) took %ss", filename_str, time() - start_time)
    else:
        """
        BurningGlass doesn't work when the file's MIME type is text/html, even if the file is a .doc file.
        (Apparently HTML files that have a .doc extension are also valid doc files, that can be opened/edited in
        MS Word/LibreOffice/etc.)
        So, we have to convert the file into PDF using xhtml2pdf.
        """
        start_time = time()
        doc_content = file_obj.read()
        mime_type = magic.from_buffer(doc_content, mime=True)
        current_app.logger.info("Benchmark: Reading file_obj and magic.from_buffer(%s) took %ss", filename_str, time() - start_time)
        final_file_ext = file_ext

        if mime_type == 'text/html':
            start_time = time()
            file_obj = StringIO()
            try:
                create_pdf_status = pisa.CreatePDF(doc_content, file_obj)
                if create_pdf_status.err:
                    current_app.logger.error('PDF create error: {}'.format(create_pdf_status.err))
                    return None
            except:
                current_app.logger.error('parse_resume: Couldn\'t convert text/html file \'{}\' to PDF'.format(
                    filename_str))
                return None
            file_obj.seek(0)
            doc_content = file_obj.read()
            final_file_ext = '.pdf'
            current_app.logger.info("Benchmark: pisa.CreatePDF(%s) and reading file took %ss", filename_str,
                                    time() - start_time)

    if not doc_content:
        current_app.logger.error('parse_resume: No doc_content')
        return {}

    encoded_resume = base64.b64encode(doc_content)
    start_time = time()
    # Original Parsing via Dice API
    # bg_response_dict = parse_resume_with_bg(filename_str + final_file_ext, encoded_resume)
    optic_response = fetch_optic_response(encoded_resume)
    current_app.logger.info("Benchmark: parse_resume_with_bg(%s) took %ss", filename_str + final_file_ext,
                            time() - start_time)
    if optic_response:
        # candidate_data = parse_xml_into_candidate_dict(bg_response_dict)
        candidate_data = parse_optic_json(optic_response)
        # consider returning raw value
        # candidate_data['dice_api_response'] = bg_response_dict
        return candidate_data
    else:
        return dict(error='No XML text')


def ocr_image(img_file_obj, export_format='pdfSearchable'):
    """Posts the image to Abby OCR API, then keeps pinging to check if it's done.
       Quits if not done in certain number of tries.

    Return:
        Image file OCR'd in desired format.
    """

    ABBY_OCR_API_AUTH_TUPLE = ('gettalent', 'lfnJdQNWyevJtg7diX7ot0je')

    # Post the image to Abby
    files = {'file': img_file_obj}
    response = requests.post('http://cloud.ocrsdk.com/processImage',
                             auth=ABBY_OCR_API_AUTH_TUPLE,
                             files=files,
                             data={'profile': 'documentConversion', 'exportFormat': export_format}
                             )
    if response.status_code != 200:
        current_app.logger.error('ABBY OCR returned non 200 response code')
        return 0

    xml = BeautifulSoup(response.text)
    current_app.logger.info("ocr_image() - Abby response to processImage: %s", response.text)

    task_id = xml.response.task['id']
    estimated_processing_time = int(xml.response.task['estimatedprocessingtime'])

    if xml.response.task['status'] != 'Queued':
        current_app.logger.error('ocr_image() - Non queued status in ABBY OCR')
        pass

    # Keep pinging Abby to get task status. Quit if tried too many times
    ocr_url = ''
    num_tries = 0
    max_num_tries = 6
    while not ocr_url:
        sleep(estimated_processing_time)

        response = requests.get('http://cloud.ocrsdk.com/getTaskStatus', params=dict(taskId=task_id),
                                auth=ABBY_OCR_API_AUTH_TUPLE)
        xml = BeautifulSoup(response.text)
        ocr_url = xml.response.task.get('resulturl')
        current_app.logger.info("ocr_image() - Abby response to getTaskStatus: %s", response.text)

        if not ocr_url:
            if num_tries > max_num_tries:
                current_app.logger.error('OCR took > {} tries to process image'.format(max_num_tries))
                raise Exception('OCR took > {} tries to process image'.format(max_num_tries))
            estimated_processing_time = 2  # If not done in originally estimated processing time, wait 2 more seconds
            num_tries += 1
            continue

    if response.status_code == requests.codes.ok:
        start_time = time()
        response = requests.get(ocr_url)
        current_app.logger.info("Benchmark: ocr_image: requests.get(%s) took %ss to download resume", ocr_url,
                                time() - start_time)
        return response.content
    else:
        return 0


def convert_pdf_to_text(pdf_file_obj):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

    fp = pdf_file_obj

    parser = PDFParser(fp)
    doc = PDFDocument()
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize('')
    if not doc.is_extractable:
        return ''

    process_pdf(rsrcmgr, device, fp)
    device.close()

    text = retstr.getvalue()
    retstr.close()
    return text


# def parse_xml_into_candidate_dict(json_text):
#     rawxml = bs4(json_text['rawXML'], 'lxml')
#
#     first_name, middle_name, last_name = "Unknown", "", "Unknown"
#     if json_text['contact']:
#         first_name = json_text['contact'][0].get('firstName', '')
#         middle_name = json_text['contact'][0].get('middleName', '')
#         last_name = json_text['contact'][0].get('lastName', '')
#
#     formatted_name = ''
#     if first_name and last_name:
#         formatted_name = first_name + " " + (middle_name + " " if middle_name else "") + last_name
#
#     candidate = dict(
#         full_name=formatted_name or "Unknown",
#         emails=[],
#         phones=[],
#         work_experiences=[],
#         educations=[],
#         skills=[],
#         addresses=[]
#     )
#
#     # Phones
#     candidate_phones = candidate['phones']
#     home_phone = mobile_phone = email_to_parse = alternate_email = ""
#
#     if json_text['contact']:
#         home_phone = json_text['contact'][0].get('phone', 0)
#         mobile_phone = json_text['contact'][0].get('mobile', 0)
#         email_to_parse = json_text['contact'][0].get('email')
#         alternate_email = json_text['contact'][0].get('alternate_email', '')
#
#     if home_phone:
#         canonicalized_phonenumber = canonicalize_phonenumber(home_phone)
#         if canonicalized_phonenumber:
#             candidate_phones.append({'value': canonicalized_phonenumber, 'label': 'home'})
#
#     if mobile_phone:
#         canonicalized_phonenumber = canonicalize_phonenumber(mobile_phone)
#         if canonicalized_phonenumber:
#             candidate_phones.append({'value': canonicalized_phonenumber, 'label': 'mobile'})
#
#     # Emails
#     candidate_emails = candidate['emails']
#
#     if str(email_to_parse) == 'None':
#         email_to_parse = ''
#
#     email = re.findall(r'[\w\.-]+@[\w\.-]+', email_to_parse)
#     if email:
#         candidate_emails.append({'address': email[0], 'label': 'Primary'})
#
#     if alternate_email:
#         candidate_emails.append({'address': email, 'label': 'Other'})
#
#     # TODO: if you cant get the email, try parsing it from the resume text
#
#     # Addresses
#     street_address = city = state = country = zipcode = ""
#     candidate_addresses = candidate['addresses']
#     if json_text['contact']:
#         street_address = json_text['contact'][0].get('street', '')
#         city = json_text['contact'][0].get('city', '')
#         state = json_text['contact'][0].get('state', '')
#         country = json_text['contact'][0].get('country', '')
#         zipcode = json_text['contact'][0].get('postalCode', '')
#
#     zipcode = sanitize_zip_code(zipcode)
#
#     lat_lon = get_coordinates(zipcode, city, state)
#
#     candidate_addresses.append(dict(
#         city=city,
#         country=country,
#         state=state,
#         po_box='',
#         address_line_1=street_address,
#         address_line_2='',
#         zip_code=zipcode,
#         latitude=lat_lon[0],
#         longitude=lat_lon[1]
#     ))
#
#     # Resume experience
#     candidate_experiences = candidate['work_experiences']
#     for experiences in rawxml.findAll('experience'):
#         jobs = experiences.findAll('job')
#         for employement_index, employement in enumerate(jobs):
#
#             organization = _tag_text(employement, 'employer')
#             # If it's 5 or less letters, keep the given capitalization, because it may be an acronym.
#             if organization and len(organization) > 5:
#                 organization = string.capwords(organization)
#
#             # Position title
#             position_title = _tag_text(employement, 'title')
#
#             # Start date
#             experience_start_date = get_date_from_date_tag(employement, 'start')
#
#             is_current_job = 0
#
#             # End date
#             experience_end_date = get_date_from_date_tag(employement, 'end')
#
#             try:
#                 today_date = datetime.date.today().isoformat()
#                 is_current_job = 1 if today_date == experience_end_date else 0
#             except ValueError:
#                 current_app.logger.error("parse_xml: Received exception getting date for candidate end_date %s",
#                                          experience_end_date)
#
#             # Company's address
#             company_address = employement.find('address')
#             company_city = _tag_text(company_address, 'city', capwords=True)
#             # company_state = _tag_text(company_address, 'state')
#             company_country = 'United States'
#
#             # Check if an experience already exists
#             existing_experience_list_order = is_experience_already_exists(candidate_experiences, organization or '',
#                                                                           position_title or '',
#                                                                           experience_start_date,
#                                                                           experience_end_date)
#
#             # Get experience bullets
#             candidate_experience_bullets = []
#             description_text = _tag_text(employement, 'description', remove_questions=True) or ''
#             for i, bullet_description in enumerate(description_text.split('|')):
#                 # If experience already exists then append the current bullet-descriptions to already existed
#                 # bullet-descriptions
#                 if existing_experience_list_order:
#                     existing_experience_description = candidate_experiences[existing_experience_list_order - 1][
#                         'candidate_experience_bullet']
#                     existing_experience_description.append(dict(
#                         listOrder=len(existing_experience_description) + 1,
#                         description=bullet_description + '\n'
#                     ))
#                 else:
#                     candidate_experience_bullets.append(dict(
#                         text=bullet_description
#                     ))
#
#             if not existing_experience_list_order:
#                 candidate_experiences.append(dict(
#                     city=company_city,
#                     end_date=experience_end_date,
#                     country=company_country,
#                     company=organization,
#                     role=position_title,
#                     is_current=is_current_job,
#                     start_date=experience_start_date,
#                     work_experience_bullets=candidate_experience_bullets
#                 ))
#
#     # Education
#     candidate_educations = candidate['educations']
#     for qualification in rawxml.findAll('education'):
#         for school_index, school in enumerate(qualification.findAll('school')):
#             school_name = _tag_text(school, 'institution')
#             school_address = school.find('address')
#             school_city = _tag_text(school_address, 'city', capwords=True)
#             school_state = _tag_text(school_address, 'state')
#             country = 'United States'
#
#             education_start_date = get_date_from_date_tag(school, 'start')
#             education_end_date = None
#             end_date = get_date_from_date_tag(school, 'end')
#             completion_date = get_date_from_date_tag(school, 'completiondate')
#
#             if completion_date:
#                 education_end_date = completion_date
#             elif end_date:
#                 education_end_date = end_date
#
#             # GPA data no longer used in educations dict.
#             # Save for later or elimate this and gpa_num_and_denom?
#             # gpa_num, gpa_denom = gpa_num_and_denom(school, 'gpa')
#             candidate_educations.append(dict(
#                 school_name=school_name,
#                 city=school_city,
#                 state=school_state,
#                 country=country,
#                 # TODO explore start/end parsing options since tenure at school and
#                 # EducationDegrees can have start/endtimes.
#                 # graduation_date=education_end_date,
#                 degrees=[
#                     {
#                         'type': _tag_text(school, 'degree'),
#                         'title': _tag_text(school, 'major'),
#                         'degree_bullets': []
#                     }
#                 ],
#             ))
#
#     # Skills
#     candidate_skills = candidate['skills']
#     candidate_skill_text = rawxml.findAll('canonskill')
#     if candidate_skill_text:
#         for candidate_skill_tag in candidate_skill_text:
#             stripped_tag = ' '.join(candidate_skill_tag.variant.getText().split())
#             if stripped_tag:
#                 candidate_skills.append(dict(
#                     months_used=candidate_skill_tag.get('experience', '').strip(),
#                     last_used_date=candidate_skill_tag.get('lastused', '').strip(),
#                     name=stripped_tag
#                 ))
#
#     candidate['summary'] = json_text.get('summary', '')
#     return candidate


# # Gets text of tag, or tag.child_tag if child_tag_name supplied.
# # This function also converts to utf-8 since BeautifulSoup always returns Unicode strings
# def _tag_text(tag, child_tag_name, remove_questions=False, remove_extra_newlines=True, capwords=False):
#     if not tag:
#         return None
#     if child_tag_name == 'description':
#         parent_of_text = tag.findAll(child_tag_name) if child_tag_name else tag
#     else:
#         parent_of_text = tag.find(child_tag_name) if child_tag_name else tag
#     if parent_of_text:
#         text = None
#         if child_tag_name != 'description' and parent_of_text.text:
#             text = parent_of_text.string.strip()
#         elif child_tag_name == 'description':
#             text = ''
#             for description in parent_of_text:
#                 text += description.string.strip() + "|"
#             text = text[:-1]
#         if text:
#             if remove_questions:
#                 text = text.replace("?", "")
#             if remove_extra_newlines:
#                 text = _newlines_regexp.sub(" ", text)
#             if capwords:
#                 text = string.capwords(text)
#             text = text.encode('utf-8')
#             return bs4(text, 'lxml').text
#     return None
#
#
# # date_tag has child tag that could be one of: current, YYYY-MM, notKnown, YYYY, YYYY-MM-DD, or notApplicable (i think)
# def get_date_from_date_tag(parent_tag, date_tag_name):
#     date_tag = parent_tag.find(date_tag_name)
#     if date_tag:
#         try:
#             if date_tag_name == 'end' and ('current' in date_tag.text.lower() or 'present' in date_tag.text.lower()):
#                 return datetime.date.isoformat()
#             return date_tag['iso8601']
#         except:
#             return None
#     return None
#
#
# def is_experience_already_exists(candidate_experiences, organization, position_title, start_date, end_date):
#     for i, experience in enumerate(candidate_experiences):
#         if (experience['company'] or '') == organization and (experience['role'] or '') == position_title and (
#                         experience['start_date'] == start_date and experience['end_date'] == end_date):
#             return i + 1
#     return False
#
#
# def gpa_num_and_denom(parent_tag, gpa_tag_name):
#     gpa_num, gpa_denom = None, None
#     gpa_tag = parent_tag.find(gpa_tag_name)
#     if gpa_tag:
#         gpa_num = gpa_tag['value'] or ''
#         gpa_denom = gpa_tag['max'] or ''
#         if gpa_num and gpa_denom:
#             gpa_num = float(gpa_num.replace(',', '.'))
#             gpa_denom = float(gpa_denom.replace(',', '.'))
#     return gpa_num, gpa_denom
#
#
# _newlines_regexp = re.compile(r"[\r\n]+")
#
#
# def canonicalize_phonenumber(phonenumber):
#     try:
#         parsed_phonenumbers = phonenumbers.parse(str(phonenumber), region="US")
#         if phonenumbers.is_valid_number_for_region(parsed_phonenumbers, 'US'):
#             # Phonenumber format is : +1 (123) 456-7899
#             return '+1 ' + phonenumbers.format_number(parsed_phonenumbers, phonenumbers.PhoneNumberFormat.NATIONAL)
#         else:
#             current_app.logger.error(
#                 'canonicalize_phonenumber: [{}] is an invalid or non-US Phone Number'.format(phonenumber))
#             return False
#     except phonenumbers.NumberParseException:
#         return False
#     except:
#         return False
#
#
# def sanitize_zip_code(zip_code):
#     # Folowing expression will validate US zip codes e.g 12345 and 12345-6789
#     zip_code = str(zip_code)
#     zip_code = ''.join(filter(lambda character: character not in ' -', zip_code))  # Dashed and Space filtered Zip Code
#     if zip_code and not ''.join(filter(lambda character: not character.isdigit(), zip_code)):
#         zip_code = zip_code.zfill(5) if len(zip_code) <= 5 else zip_code.zfill(9) if len(zip_code) <= 9 else ''
#         if zip_code:
#             return (zip_code[:5] + ' ' + zip_code[5:]).strip()
#     return None
#
#
# def get_coordinates(zipcode=None, city=None, state=None, address_line_1=None, location=None):
#     """
#
#     :param location: if provided, overrides all other inputs
#     :return: string of "lat,lon" in degrees, or None if nothing found
#     """
#     coordinates = (None, None)
#
#     from GoogleGeoSearch import get_geocoordinates
#     location = location or "%s%s%s%s" % (
#         address_line_1 + ", " if address_line_1 else "",
#         city + ", " if city else "",
#         state + ", " if state else "",
#         zipcode or ""
#     )
#     latitude, longitude = get_geocoordinates(location)
#     if latitude and longitude:
#         coordinates = (str(latitude), str(longitude))
#
#     return coordinates