from datetime import datetime
from graphql_service.common.models.candidate import CandidateEmail
from graphql_service.common.utils.handy_functions import purge_dict
from graphql_service.common.utils.validators import is_valid_email, sanitize_zip_code
# from graphql_service.common.geo_services.geo_coordinates import get_coordinates

from graphql_service.common.utils.datetime_utils import DatetimeUtils


class ValidateAndSave(object):
    """
    Class contains functions that will clean, validate, and save candidate's data
    """
    added_datetime = DatetimeUtils.to_utc_str(datetime.utcnow())
    updated_datetime = added_datetime

    # Aggregated candidate data for dynamodb
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
                     coordinates=3)#get_coordinates(zipcode=zip_code, city=city, state=iso3166_subdivision))
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
