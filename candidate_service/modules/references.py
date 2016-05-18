"""
This file contains functions for candidate reference(s) CRUD operations
"""
# Models
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import (
    Candidate, CandidateReference, ReferenceWebAddress, EmailLabel, PhoneLabel
)
from candidate_service.common.models.associations import ReferenceEmail, ReferencePhone

# Handy functions
from candidate_service.common.utils.handy_functions import purge_dict

# Common validators
from candidate_service.common.utils.validators import format_phone_number


def get_references(candidate):
    """
    Function will return a list of candidate's references
    :type candidate:  Candidate
    :rtype:  list[dict]
    """

    def _get_reference_emails(reference_id):
        """
        Function will return candidate's reference's email information
        :type reference_id:  int|long
        :rtype:  dict
        """
        reference_email = ReferenceEmail.get_by_reference_id(reference_id)
        if reference_email:
            return dict(label=EmailLabel.get_description_from_id(reference_email.email_label_id),
                        is_default=reference_email.is_default,
                        address=reference_email.value)

    def _get_reference_phones(reference_id):
        """
        Function will return candidate's reference's phone information
        :type reference_id:  int|long
        :rtype:  dict
        """
        reference_phone = ReferencePhone.get_by_reference_id(reference_id)
        if reference_phone:
            return dict(label=PhoneLabel.get_description_from_id(reference_phone.phone_label_id),
                        is_default=reference_phone.is_default,
                        value=reference_phone.value,
                        extension=reference_phone.extension)

    def _get_reference_web_addresses(reference_id):
        """
        Function will return candidate's reference's web address information
        :type reference_id:  int|long
        :rtype:  dict
        """
        reference_web_address = ReferenceWebAddress.get_by_reference_id(reference_id)
        if reference_web_address:
            return dict(id=reference_web_address.id,
                        url=reference_web_address.url,
                        description=reference_web_address.description)

    return_list = []  # Aggregate all of candidate's references' information
    for reference in candidate.references:
        reference_id = reference.id
        return_dict = dict(
            id=reference_id,
            name=reference.person_name,
            position_title=reference.position_title,
            comments=reference.comments,
            reference_email=_get_reference_emails(reference_id),
            reference_phone=_get_reference_phones(reference_id),
            reference_web_address=_get_reference_web_addresses(reference_id)
        )
        # Remove keys with empty values and strip each value
        return_dict = purge_dict(dictionary=return_dict, strip=False)
        return_list.append(return_dict)

    return return_list


def create_references(candidate_id, references):
    """
    Function will insert candidate's references' information into db.
    References' information must include: person_name and comments.
    References' information can include: reference-email dict & reference-phone dict.
    Empty data will not be added to db
    :type candidate_id: int|long
    :type references:  list[dict]
    :rtype:  list[int]
    """
    created_reference_ids = []
    for reference in references:
        candidate_reference_dict = dict(
            resume_id=candidate_id,
            candidate_id=candidate_id,
            person_name=reference.get('name'),
            position_title=reference.get('position_title'),
            comments=reference.get('comments')
        )
        # Strip each value & remove keys with empty values
        candidate_reference_dict = purge_dict(candidate_reference_dict)

        # Prevent inserting empty records in db
        if not candidate_reference_dict:
            continue

        candidate_reference = CandidateReference(**candidate_reference_dict)
        db.session.add(candidate_reference)
        db.session.flush()
        reference_id = candidate_reference.id

        reference_email, reference_phone = reference.get('reference_email'), reference.get('reference_phone')
        reference_web_address = reference.get('reference_web_address')
        if reference_email:  # add reference's email info if provided
            email_label = 'Primary' if not reference_email.get('label') else reference_email['label'].strip().title()
            value = reference_email['address'].strip() if reference_email.get('address') else None
            reference_email_dict = dict(
                email_label_id=EmailLabel.email_label_id_from_email_label(email_label) if value else None,
                is_default=reference_email.get('is_default') or True if value else None,
                value=value
            )
            # Remove keys with empty values
            reference_email_dict = purge_dict(reference_email_dict, strip=False)

            # Prevent adding empty records to db
            if reference_email_dict:
                reference_email_dict.update(reference_id=reference_id)
                db.session.add(ReferenceEmail(**reference_email_dict))

        if reference_phone:  # add reference's phone info if provided
            phone_label = 'Home' if not reference_phone.get('label') else reference_phone['label'].strip().title()
            value = reference_phone['value'].strip() if reference_phone.get('value') else None
            phone_number_dict = format_phone_number(value) if value else None
            reference_phone_dict = dict(
                phone_label_id=PhoneLabel.phone_label_id_from_phone_label(phone_label) if phone_number_dict else None,
                is_default=reference_phone.get('is_default') or True if phone_number_dict else None,
                value=phone_number_dict.get('formatted_number') if phone_number_dict else None,
                extension=phone_number_dict.get('extension') if phone_number_dict else None
            )
            # Remove keys with empty values
            reference_phone_dict = purge_dict(reference_phone_dict, strip=False)

            # Prevent adding empty records to db
            if reference_phone_dict:
                reference_phone_dict.update(reference_id=reference_id)
                db.session.add(ReferencePhone(**reference_phone_dict))

        if reference_web_address:
            reference_web_address_dict = dict(
                url=reference_web_address.get('url'),
                description=reference_web_address.get('description'),
            )
            # Remove keys with empty values & strip each value
            reference_web_address_dict = purge_dict(reference_web_address_dict)

            # Prevent inserting empty records into db
            if reference_web_address_dict:
                reference_web_address_dict.update(reference_id=reference_id)
                db.session.add(ReferenceWebAddress(**reference_web_address_dict))

        db.session.commit()  # Commit transactions to db
        created_reference_ids.append(reference_id)

    return created_reference_ids


def delete_reference(candidate_reference):
    """
    :type candidate_reference:  CandidateReference
    :rtype:  dict
    """
    db.session.delete(candidate_reference)
    db.session.commit()
    return {'id': candidate_reference.id}


def delete_all_references(candidate_references):
    """
    :type candidate_references:  list[CandidateReference]
    :rtype:  list[dict]
    """
    deleted_candidate_references = []
    for reference in candidate_references:
        deleted_candidate_references.append(delete_reference(reference))
    return deleted_candidate_references
