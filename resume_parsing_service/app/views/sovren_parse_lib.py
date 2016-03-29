from collections import namedtuple
import string
import re
from bs4 import BeautifulSoup as bs4
__author__ = 'erik@getTalent.com'


NameCollection = namedtuple('NameCollection', 'first, middle, last, formatted')


def parse_sovren_xml(raw_xml):
    resume_soup = bs4(raw_xml, 'lxml')
    contact_soup = resume_soup.find('contactinfo')
    names = name_tags_to_name(contact_soup.find('personname'))
    addresses = contact_tag_to_addresses(contact_soup)
    emails = contact_tag_to_emails(contact_soup)
    phones = contact_tag_to_phones(contact_soup)
    work_experiences = employment_tags_to_experiences(resume_soup.findAll('employmenthistory'))
    educations = education_tags_to_educations(resume_soup.findAll('schoolorinstitution'))
    skills = soup_qualifications_to_skills(resume_soup.find('qualifications'))

    candidate = dict(
        first_name=names.first,
        last_name=names.last,
        emails=emails,
        phones=phones,
        work_experiences=work_experiences,
        educations=educations,
        skills=skills,
        addresses=addresses,
        talent_pool_ids={'add': None}
    )
    return candidate


def name_tags_to_name(tag):
    if not tag or not tag.findAll(): return None, None, None, None
    middle_name = tag_text(tag, 'middlename', capwords=True)
    first_name = tag_text(tag, 'givenname', capwords=True)
    last_name = tag_text(tag, 'familyname', capwords=True)
    formatted_name = tag_text(tag, 'formattedname', capwords=True)
    if first_name and last_name and not formatted_name:   # if first + last but not formatted
        formatted_name = first_name + " " + (middle_name + " " if middle_name else "") + last_name
    if formatted_name and not first_name and not last_name: # if formatted_name but not first + last
        split_name = formatted_name.split(' ')
        first_name = split_name[0]
        # all the middle names joined together
        middle_name = ' '.join(split_name[1:-1]) if len(split_name) > 2 else None
        last_name = split_name[-1]
    return NameCollection(first_name, last_name, middle_name, formatted_name)


def contact_tag_to_emails(contact_tag):
    emails = []
    for i, email_tag in enumerate(contact_tag.findAll('internetemailaddress')):
        email = tag_text(email_tag)
        email = email.lower() if email else None
        emails.append(dict(
            address = email
        ))
    return emails


def contact_tag_to_phones(contact_tag):
    phones = []
    for phone_tag in contact_tag.findAll('formattednumber'):
        number = tag_text(phone_tag)
        phones.append(dict(
            value = number
        ))


def employment_tags_to_experiences(employment_tags):
    candidate_experiences = []
    for employment_history_index, employment_history_tag  in enumerate(employment_tags):
        for position_history_index, position_history_tag in enumerate(employment_history_tag.findAll('positionhistory')):
            # Organization name
            org_name_tag = position_history_tag.find('orgname')
            organization_tag = (org_name_tag and org_name_tag.find('organizationname')) or employment_history_tag.find('employerorgname') or position_history_tag.find('companyname2')
            organization = tag_text(organization_tag)
            if organization and len(organization) > 5: organization = string.capwords(organization)
            # Position title
            position_title = tag_text(position_history_tag, 'title', capwords=False)
            # Start/End date
            start_tag = position_history_tag.find('startdate')
            end_tag = position_history_tag.find('enddate')
            start_month, start_year = get_month_and_year_from_sovren_date_tag(start_tag)
            end_month, end_year = get_month_and_year_from_sovren_date_tag(end_tag)
            # Current Job
            is_current_job = ("current" in end_tag.text) if end_tag else False
            # Company's address
            org_info_tag = position_history_tag.find('orginfo')
            company_city = tag_text(org_info_tag, 'positionlocation', 'municipality', capwords=True)
            company_regions = tag_text(org_info_tag, 'positionlocation', 'region')
            # company_country_code = tag_text(org_info_tag, 'positionlocation', 'countrycode')
            # Get experience bullets
            candidate_experience_bullets = []
            description_text = tag_text(position_history_tag, 'description', remove_questions=True)
            for i, bullet_description in enumerate(split_description(description_text)):
                candidate_experience_bullets.append(dict(
                    listOrder = i + 1,
                    description = bullet_description
                ))
            candidate_experiences.append(dict(
                organization = organization,
                position = position_title,
                city = company_city,
                state = company_regions,
                listOrder = position_history_index + 1,  # listOrder starts from 1
                startMonth = start_month,
                endMonth = end_month,
                startYear = start_year,
                endYear = end_year,
                isCurrent = is_current_job,
                candidate_experience_bullet = candidate_experience_bullets
            ))
    return candidate_experiences


def education_tags_to_educations(school_tags):
    educations = []
    for school_index, school_tag in enumerate(school_tags):
        school_type = school_tag.get('schooltype')
        # School location
        location_tag = school_tag.find('locationsummary') or school_tag.find('postaladdress')
        school_city = tag_text(location_tag, 'municipality', capwords=True)
        school_state = tag_text(location_tag, 'region', capwords=True)
        school_country = tag_text(location_tag, 'countrycode')
        # School name
        school_name = tag_text(school_tag, 'school', 'schoolname', capwords=True)
        # Degree
        candidate_education_degrees = []
        for degree_index, degree_tag in enumerate(school_tag.findAll('degree')):
            degree_name = tag_text(degree_tag, 'degreename')
            degree_type = string.capwords(degree_tag['degreetype']) if degree_tag.get('degreetype') else None
            # Start month/year, end month/year
            dates_tag = degree_tag.find('datesofattendance')
            start_month, start_year, end_month, end_year = None, None, None, None
            if dates_tag:
                start_month, start_year = get_month_and_year_from_sovren_date_tag(dates_tag.find('startdate'))
                end_month, end_year = get_month_and_year_from_sovren_date_tag(dates_tag.find('enddate'))
            # Get major & minor
            concentration_type = tag_text(degree_tag, 'degreemajor', 'name', capwords=True) or ''
            degree_minor = tag_text(degree_tag, 'degreeminor', 'name', capwords=True)
            if degree_minor:
                concentration_type += ' ' + degree_minor if concentration_type else degree_minor
            # GPA stuff
            degree_measure_tag = degree_tag.find('degreemeasure')
            educational_measure_tag = degree_measure_tag.find('educationalmeasure') if degree_measure_tag else None
            gpa_num, gpa_denom = None, None
            if educational_measure_tag:
                gpa_num = tag_text(educational_measure_tag, 'measurevalue', grandchild_tag_name=True)
                gpa_num = float(gpa_num.replace(',', '.')) if gpa_num else None
                gpa_denom = tag_text(educational_measure_tag, 'highestpossiblevalue', grandchild_tag_name=True)
                gpa_denom = float(gpa_denom.replace(',', '.')) if gpa_denom else None
            # Bullet description
            candidate_education_degree_bullets = []
            candidate_education_degree_bullet_comment = '\n'.join(split_description(tag_text(degree_tag, 'comments', remove_questions=True)))
            # TODO we actually don't need candidate_education_degree_bullet lol...it's not part of HRXML schema. concentrationType is actually the major
            candidate_education_degree_bullets.append(dict(
                listOrder=1,
                concentrationType=concentration_type,
                comments=candidate_education_degree_bullet_comment
            ))
            # Add data
            candidate_education_degrees.append(dict(
                listOrder = degree_index + 1,
                degreeType = degree_type,
                degreeTitle = degree_name,
                startMonth = start_month,
                endMonth = end_month,
                startYear = start_year,
                endYear = end_year,
                gpaNum = gpa_num,
                gpaDenom = gpa_denom,
                candidate_education_degree_bullet = candidate_education_degree_bullets
            ))
        educations.append(dict(
            listOrder = school_index + 1,
            schoolName = school_name,
            schoolType = school_type,
            city = school_city,
            state = school_state,
            # countryId = _country_code_to_country_id(school_country),
            candidate_education_degree = candidate_education_degrees
        ))
    return educations


def soup_qualifications_to_skills(qualifications):
    candidate_skills = []
    skill_names_added = []
    for skill_tag_index, skill_tag in enumerate(qualifications.findAll('competency')):
        if skill_tag_index > 255: break # only 256 skills per resume
        skill_name = skill_tag.get('name')
        last_used_date, months_used = None, None
        if skill_name:
            competency_evidence_tag = skill_tag.find('competencyevidence')
            if competency_evidence_tag: last_used_date = competency_evidence_tag.get('lastused') # in format YYYY-MM-DD, which is what web2py wants
            months_used = int(tag_text(skill_tag, 'competencyevidence', grandchild_tag_name=True) or 0) # .find('competencyevidence').findAll()[0])
        # Add skills to list unless already in there
        if skill_name.lower() not in skill_names_added:
            skill_names_added.append(skill_name.lower())
            candidate_skills.append(dict(
                listOrder = skill_tag_index + 1,
                totalMonths = months_used,
                lastUsed = last_used_date,
                description = skill_name
            ))
    return candidate_skills


def contact_tag_to_addresses(contact_tag):
    addresses = []
    for i, address_tag in enumerate(contact_tag.findAll('postaladdress')):
        address_line_1, address_line_2 = None, None
        delivery_address_tag = address_tag.find('deliveryaddress')
        if delivery_address_tag:
            for i, address_line_tag in enumerate(delivery_address_tag.findAll('addressline')):
                if i == 0:
                    address_line_1 = tag_text(address_line_tag)
                elif i == 1:
                    address_line_2 = tag_text(address_line_tag)
                else:
                    break
        zipcode = tag_text(address_tag, 'postalcode')
        city = tag_text(address_tag, 'municipality', capwords=True)
        state = tag_text(address_tag, 'region')
        addresses.append(dict(
            addressLine1 = address_line_1,
            addressLine2 = address_line_2,
            city=city,
            state=state,
            # countryId=_country_code_to_country_id(_tag_text(address_tag, 'countrycode')),
            zipCode = zipcode,
        ))
    return addresses


# Compile regexps
split_description_regexp = re.compile(r"•≅_|≅_| \* |•|➢|→|\n\n\n")
split_description_by_hyphen_regexp = re.compile(r"\s?-([A-Z])")
newlines_regexp = re.compile(r"[\r\n]+")
date_regexp = re.compile(r"(\d{4})-?(\d{2})?-?(\d{2})?")


# ALWAYS USE THIS FOR GETTING TEXT OUT OF A TAG
# Gets text of tag, or tag.child_tag if child_tag_name supplied, or tag.child_tag.grandchild_tag if grandchild_tag_name supplied
# If grandchild_tag_name=True, gets text of first child of child_tag.
# This function also converts to utf-8 since BeautifulSoup always returns Unicode strings
def tag_text(tag, child_tag_name=None, grandchild_tag_name=None, remove_questions=False, remove_extra_newlines=False, capwords=False):
    if not tag: return ''
    parent_of_text = tag.find(child_tag_name) if child_tag_name else tag
    if not parent_of_text: return ''
    if grandchild_tag_name is True:
        parent_of_text = parent_of_text.findAll()[0] if parent_of_text.findAll() else parent_of_text
    elif isinstance(grandchild_tag_name, basestring):  # if string
        parent_of_text = parent_of_text.find(grandchild_tag_name) if grandchild_tag_name else parent_of_text
    if parent_of_text and parent_of_text.string:
        text = parent_of_text.string.strip()
        if remove_questions: text = text.replace("?", "")
        if remove_extra_newlines: text = newlines_regexp.sub(" ", text)
        if capwords: text = string.capwords(text)
        text = text.encode('utf-8')
        return text
    return ''


# date_tag has child tag that could be one of: current, YYYY-MM, notKnown, YYYY, YYYY-MM-DD, or notApplicable (i think)
def get_month_and_year_from_sovren_date_tag(date_tag):
    date_child = date_tag.findAll()[0] if date_tag and date_tag.findAll() else None
    if not date_tag or not date_child: return None, None
    date_child_text = tag_text(date_child)
    # If end tag is current, return None, None
    if date_tag.name == "enddate" and "current" in date_child_text:
        return None, None
    result = date_regexp.search(date_child_text)
    if not result: return None, None  # notKnown, notApplicable
    year, month, day = result.groups()
    month, year = int(month) if month else None, int(year) if year else None
    return month, year


def split_description(text):
    if not text: return []
    split_text = split_description_regexp.split(text)
    if len(split_text) == 1:  # If none of the separators were found, try splitting on " -[A-Z]"
        messed_up_split_array = split_description_by_hyphen_regexp.split(text)  # "Hello there -Hi my name is Osman" -> ['Hello there', 'H', 'i my name is Osman']
        messed_up_split_array = filter(None, messed_up_split_array) # remove empties
        if len(messed_up_split_array) > 1:  # if it actually split
            split_text = []
            ignore_next_text_part = False
            for i, text_part in enumerate(messed_up_split_array):
                # If a text_part is one character long, add it to the next text_part if it's there
                if len(text_part) == 1:
                    next_text_part = messed_up_split_array[i + 1] if len(messed_up_split_array) != i + 1 else ""
                    split_text.append(text_part + next_text_part)
                    ignore_next_text_part = True
                elif not ignore_next_text_part:
                    split_text.append(text_part)
                    ignore_next_text_part = False
                else:
                    ignore_next_text_part = False
    split_text = [text_piece.strip().replace('\n', '') for text_piece in split_text]  # strip() all elements
    return filter(None, split_text)  # remove empties