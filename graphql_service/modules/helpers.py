# Standard library
import re
from datetime import datetime
from copy import deepcopy

import phonenumbers
import pycountry

# SQLAlchemy Models
from graphql_service.common.models.candidate import CandidateEmail, PhoneLabel

# Helpers
from graphql_service.common.utils.handy_functions import purge_dict
from graphql_service.common.utils.validators import is_valid_email, sanitize_zip_code, parse_phone_number
from graphql_service.common.geo_services.geo_coordinates import get_coordinates

from graphql_service.common.utils.datetime_utils import DatetimeUtils


class ValidatedCandidateData(object):
    """

    """

    # TODO: Include error handling
    # TODO: Complete all checks and validations
    def __init__(self, primary_data, addresses_data=None, educations_data=None,
                 emails_data=None, phones_data=None):
        self.name = 'ValidatedCandidateData'

        if not isinstance(primary_data, dict):
            raise Exception("Candidate's primary data must be of type dict")

        self.candidate_data = primary_data.copy()
        self.addresses_data = addresses_data
        self.educations_data = educations_data
        self.emails_data = emails_data
        self.phones_data = phones_data

        # Addresses
        if self.addresses_data:
            self.addresses(self.addresses_data)

        # Educations
        if self.educations_data:
            self.educations(self.educations_data)

        # Emails
        if self.emails_data:
            self.emails(self.emails_data)

        # Phones
        if self.phones_data:
            self.phones(self.phones_data)

    def __repr__(self):
        return "<ValidatedCandidateData {} ({})>".format(self.name, hash(self))

    def addresses(self, addresses_):
        # Aggregate formatted & validated address data
        checked_address_data = []

        # Check if any of the addresses is set as the default address
        addresses_have_default = [isinstance(address.get('is_default'), bool) for address in addresses_]

        for i, address in enumerate(addresses_):
            zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
            city = clean(address.get('city'))
            iso3166_subdivision = address.get('iso3166_subdivision')

            checked_address_data.append(
                dict(zip_code=zip_code,
                     city=city,
                     iso3166_subdivision=iso3166_subdivision,
                     iso3166_country=address.get('iso3166_country'),
                     po_box=clean(address.get('po_box')),
                     is_default=i == 0 if not addresses_have_default else address.get('is_default'),
                     coordinates=get_coordinates(zipcode=zip_code, city=city, state=iso3166_subdivision))
            )

        # Save addresses data
        self.candidate_data['addresses'] = checked_address_data

    def educations(self, educations_):
        # Aggregate formatted & validated education data
        checked_education_data = []

        for i, education in enumerate(educations_):
            checked_education_data.append(dict(
                school_name=education.get('school_name'),
                school_type=education.get('school_type'),
                city=education.get('city'),
                iso3166_country=(education.get('iso3166_country') or '').upper(),
                iso3166_subdivision=(education.get('iso3166_subdivision') or '').upper(),
                is_current=education.get('is_current'),
                added_datetime=education.get('added_datetime') or ValidateAndSave.added_datetime,
                updated_datetime=DatetimeUtils.to_utc_str(datetime.utcnow())
            ))

            degrees = education.get('degrees')
            if degrees:
                # Aggregate formatted & validated degree data
                checked_degree_data = []

                for degree in degrees:
                    # Because DynamoDB is too cool for floats
                    from decimal import Decimal
                    gpa = Decimal(degree['gpa']) if degree.get('gpa') else None

                    checked_degree_data.append(dict(
                        added_datetime=degree.get('added_datetime') or ValidateAndSave.added_datetime,
                        updated_datetime=ValidateAndSave.updated_datetime,
                        start_year=degree.get('start_year'),
                        start_month=degree.get('start_month'),
                        end_year=degree.get('end_year'),
                        end_month=degree.get('end_month'),
                        gpa=gpa,
                        degree_type=degree.get('degree_type'),
                        degree_title=degree.get('degree_title'),
                        concentration=degree.get('concentration'),
                        comments=degree.get('comments')
                    ))

                # Aggregate degree data to the corresponding education data
                checked_education_data[i]['degrees'] = checked_degree_data

        # Save educations data
        self.candidate_data['educations'] = checked_education_data

    def emails(self, emails_):
        # Aggregate formatted & validated email data
        checked_email_data = []

        # Check if any of the emails is set as the default email
        emails_have_default = [isinstance(email.get('is_default'), bool) for email in emails_]

        for i, email in enumerate(emails_):
            # Label
            label = (email.get('label') or '').title()
            if not label or label not in CandidateEmail.labels_mapping.keys():
                label = 'Other'

            # First email will be set as default if no other email is set as default
            default = i == 0 if not any(emails_have_default) else email.get('is_default')

            checked_email_data.append(
                dict(label=label, address=clean(email.get('address')), is_default=default)
            )

        # Save emails data
        self.candidate_data['emails'] = checked_email_data

    def phones(self, phones_):
        # Aggregate formatted & validated phone data
        checked_phone_data = []

        # Check if phone label and default have been provided
        phones_have_label = any([phone.get('label') for phone in phones_])
        phones_have_default = any([isinstance(phone.get('is_default'), bool) for phone in phones_])

        # If duplicate phone numbers are provided, we will only use one of them
        seen = set()
        for phone in phones_:
            phone_value = phone.get('value')
            if phone_value and phone_value in seen:
                phones_.remove(phone)
            seen.add(phone_value)

        for index, phone in enumerate(phones_):

            # If there is no default value, the first phone should be set as the default phone
            is_default = index == 0 if not phones_have_default else phone.get('is_default')

            # If there's no label, the first phone's label will be 'Home', rest will be 'Other'
            phone_label = PhoneLabel.DEFAULT_LABEL if (not phones_have_label and index == 0) \
                else clean(phone.get('label')).title()

            # Phone number must contain at least 7 digits
            # http://stackoverflow.com/questions/14894899/what-is-the-minimum-length-of-a-valid-international-phone-number
            value = clean(phone.get('value'))
            number = re.sub('\D', '', value)
            if len(number) < 7:
                print("Phone number ({}) must be at least 7 digits".format(value))

            iso3166_country_code = phone.get('iso3166_country')
            phone_number_obj = parse_phone_number(value, iso3166_country_code=iso3166_country_code) if value else None
            """
            :type phone_number_obj: PhoneNumber
            """
            # phonenumbers.format() will append "+None" if phone_number_obj.country_code is None
            if phone_number_obj:
                if not phone_number_obj.country_code:
                    value = str(phone_number_obj.national_number)
                else:
                    value = str(phonenumbers.format_number(phone_number_obj, phonenumbers.PhoneNumberFormat.E164))

            phone_dict = dict(
                value=value,
                extension=phone_number_obj.extension if phone_number_obj else None,
                label=phone_label,
                is_default=is_default
            )

            # Remove keys with empty values
            phone_dict = purge_dict(phone_dict)

            # Prevent adding empty records to db
            if not phone_dict:
                continue

            # Save data
            checked_phone_data.append(phone_dict)

        self.candidate_data['phones'] = checked_phone_data


class CandidateData(object):
    candidate_data = {}


class ValidateAndSave(object):
    """
    Class contains functions that will clean, validate, and save candidate's data
    """
    added_datetime = DatetimeUtils.to_utc_str(datetime.utcnow())
    updated_datetime = added_datetime

    # Aggregated candidate data for dynamodb
    # TODO: Create new object each time to prevent conflicts in case of multi-thread requests
    candidate_data = {}

    @staticmethod
    def addresses(addresses_):
        # Aggregate formatted & validated address data
        checked_address_data = []

        # Check if any of the addresses is set as the default address
        addresses_have_default = [isinstance(address.get('is_default'), bool) for address in addresses_]

        for i, address in enumerate(addresses_):
            zip_code = sanitize_zip_code(address['zip_code']) if address.get('zip_code') else None
            city = clean(address.get('city'))
            iso3166_subdivision = address.get('iso3166_subdivision')

            checked_address_data.append(
                dict(zip_code=zip_code,
                     city=city,
                     iso3166_subdivision=iso3166_subdivision,
                     iso3166_country=address.get('iso3166_country'),
                     po_box=clean(address.get('po_box')),
                     is_default=i == 0 if not addresses_have_default else address.get('is_default'),
                     coordinates=get_coordinates(zipcode=zip_code, city=city, state=iso3166_subdivision))
            )

        # Save data
        ValidateAndSave.candidate_data['addresses'] = checked_address_data
        return

    @staticmethod
    def emails(emails_):
        # Aggregate formatted & validated email data
        checked_email_data = []

        # Check if any of the emails is set as the default email
        emails_have_default = [isinstance(email.get('is_default'), bool) for email in emails_]

        for i, email in enumerate(emails_):

            # Label
            label = (email.get('label') or '').title()
            if not label or label not in CandidateEmail.labels_mapping.keys():
                label = 'Other'

            # First email will be set as default if no other email is set as default
            default = i == 0 if not any(emails_have_default) else email.get('is_default')

            checked_email_data.append(
                dict(label=label, address=clean(email.get('address')), is_default=default)
            )

        # Save data
        ValidateAndSave.candidate_data['emails'] = checked_email_data
        return

    @staticmethod
    def educations(educations_):
        # Aggregate formatted & validated education data
        checked_education_data = []

        for i, education in enumerate(educations_):
            checked_education_data.append(dict(
                school_name=education.get('school_name'),
                school_type=education.get('school_type'),
                city=education.get('city'),
                iso3166_country=(education.get('iso3166_country') or '').upper(),
                iso3166_subdivision=(education.get('iso3166_subdivision') or '').upper(),
                is_current=education.get('is_current'),
                added_datetime=education.get('added_datetime') or ValidateAndSave.added_datetime,
                updated_datetime=DatetimeUtils.to_utc_str(datetime.utcnow())
            ))

            degrees = education.get('degrees')
            if degrees:
                # Aggregate formatted & validated degree data
                checked_degree_data = []

                for degree in degrees:
                    # Because DynamoDB is too cool for floats
                    from decimal import Decimal
                    gpa = Decimal(degree['gpa']) if degree.get('gpa') else None

                    checked_degree_data.append(dict(
                        added_datetime=degree.get('added_datetime') or ValidateAndSave.added_datetime,
                        updated_datetime=ValidateAndSave.updated_datetime,
                        start_year=degree.get('start_year'),
                        start_month=degree.get('start_month'),
                        end_year=degree.get('end_year'),
                        end_month=degree.get('end_month'),
                        gpa=gpa,
                        degree_type=degree.get('degree_type'),
                        degree_title=degree.get('degree_title'),
                        concentration=degree.get('concentration'),
                        comments=degree.get('comments')
                    ))

                # Aggregate degree data to the corresponding education data
                checked_education_data[i]['degrees'] = checked_degree_data

        ValidateAndSave.candidate_data['educations'] = checked_education_data


def clean(value):
    """
    :rtype: str
    """
    return (value or '').strip()
