from graph_api_service.common.models.candidate import CandidateEmail
from graph_api_service.common.utils.handy_functions import purge_dict
from graph_api_service.common.utils.validators import is_valid_email, sanitize_zip_code
from graph_api_service.common.geo_services.geo_coordinates import get_coordinates


class ValidateAndSave(object):
    """
    Class contains functions that will clean, validate, and save candidate's data
    """
    # Aggregated candidate data for dynamodb
    candidate_data = {}

    @staticmethod
    def addresses(addresses_):
        # Aggregate formatted & validated address data
        checked_address_data = []

        # Check if any of the addresses is set as the defaul address
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
                     is_default=i == 0 if addresses_have_default else address.get('is_default'),
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


def clean(value):
    return (value or '').strip()
